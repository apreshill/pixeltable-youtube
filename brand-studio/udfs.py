"""Functions the brand studio tables call.

The lookups between tables are queries in schema.py. This file holds the rest:

- The brand board: Pillow draws the logo, type specimens, and palette from the
  brand kit, so every model call sees the brand the same way.
- Prompt builders: they turn the brand kits, the campaign's set, and a moment
  into the words and pictures each model call gets.
- Motion: the Gemini Omni call, reversing a clip for a reveal, and cutting a reel.
"""

import io
import json

import av
import pixeltable as pxt
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pixeltable.utils.local_store import TempStore

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _loads(text: str):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1].rsplit('```', 1)[0]
    return json.loads(text)


@pxt.udf
def parse_json(text: str) -> pxt.Json:
    """A model's JSON answer as a dict. Strips a ``` fence if the model added one."""
    return _loads(text)


@pxt.udf
def parse_optional_json(text: str | None) -> pxt.Json | None:
    """The same, for a call that may not have run, such as the review of a clip that was never made."""
    return None if text is None else _loads(text)


def _color(palette: list, role: str) -> str:
    for swatch in palette:
        if swatch['role'] == role:
            return swatch['hex']
    raise KeyError(f'palette has no {role!r} color')


def _ink(palette: list) -> str:
    ink = next(s for s in palette if s['role'] == 'ink')
    return f"{ink['name']} {ink['hex']}"


def _palette_line(palette: list) -> str:
    return ', '.join(f"{s['name']} {s['hex']} ({s['role']})" for s in palette)


def _font(data: bytes, size: int, weight: int | None = None) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(io.BytesIO(data), max(1, int(size)))
    if weight is not None and font.get_variation_axes():
        font.set_variation_by_axes([weight])
    return font


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip('#')
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _luminance(rgb) -> float:
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in rgb[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _tracked(draw, xy, text, font, fill, tracking: float) -> None:
    """Draw text one letter at a time so wide letter spacing works."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill, anchor='ls')
        x += font.getlength(ch) + tracking


def _tracked_length(text, font, tracking: float) -> float:
    return sum(font.getlength(ch) for ch in text) + tracking * max(0, len(text) - 1)


# ---------------------------------------------------------------------------
# The brand board: one picture that carries a brand's look into every model call.
# ---------------------------------------------------------------------------


@pxt.udf
def brand_board(
    name: str,
    category: str,
    palette: pxt.Json,
    type_spec: pxt.Json,
    headline_font: pxt.Binary,
    accent_font: pxt.Binary,
    body_font: pxt.Binary,
    logo_dark: pxt.Image,
) -> pxt.Image:
    """Logo, type specimens, and palette swatches on the brand's background color."""
    W, H = 1800, 1200
    m = 90
    bg, ink = _color(palette, 'background'), _color(palette, 'ink')
    board = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(board)
    hs, acs, bs = type_spec['headline'], type_spec['accent'], type_spec['body']

    logo = logo_dark.convert('RGBA')
    logo = logo.resize((int(logo.width * 70 / logo.height), 70), Image.LANCZOS)
    board.paste(logo, (m, m), logo)
    label = _font(body_font, 26, bs.get('weight'))
    _tracked(d, (W - m - _tracked_length(category.upper(), label, 26 * 0.2), m + 50), category.upper(), label, ink, 26 * 0.2)

    # Type specimens: the headline face, the emphasis face, and a line of body copy.
    head = _font(headline_font, 300, hs.get('weight'))
    acc = _font(accent_font, int(300 * acs.get('scale', 1.0)), acs.get('weight'))
    base = 560
    d.text((m, base), 'Aa', font=head, fill=ink, anchor='ls')
    d.text((m + head.getlength('Aa') + 60, base), 'Aa', font=acc, fill=_color(palette, 'cta'), anchor='ls')
    spec_x = m + head.getlength('Aa') + acc.getlength('Aa') + 160
    small = _font(body_font, 30, bs.get('weight'))
    for i, (role, spec) in enumerate((('Headlines', hs), ('Emphasis', acs), ('Body and buttons', bs))):
        y = 300 + i * 92
        _tracked(d, (spec_x, y), role.upper(), _font(body_font, 22, bs.get('weight')), ink, 22 * 0.2)
        d.text((spec_x, y + 40), spec['family'], font=small, fill=ink, anchor='ls')

    # Swatches.
    top, bottom = 660, H - m
    gap = 24
    sw = (W - 2 * m - gap * (len(palette) - 1)) / len(palette)
    name_font = _font(body_font, 30, 500 if bs.get('weight') else None)
    hex_font = _font(body_font, 24, bs.get('weight'))
    for i, s in enumerate(palette):
        x0 = m + i * (sw + gap)
        fill = _rgb(s['hex'])
        d.rectangle((x0, top, x0 + sw, bottom), fill=fill, outline=ink if _contrast(fill, _rgb(bg)) < 1.15 else None, width=2)
        text = _rgb(ink) if _contrast(fill, _rgb(ink)) >= _contrast(fill, _rgb(bg)) else _rgb(bg)
        d.text((x0 + 28, bottom - 78), s['name'], font=name_font, fill=text, anchor='ls')
        d.text((x0 + 28, bottom - 34), s['hex'].upper(), font=hex_font, fill=text, anchor='ls')
    return board


# ---------------------------------------------------------------------------
# Art direction: Gemini reads each brand's style guide once.
# ---------------------------------------------------------------------------

ART_DIRECTION_PROMPT = (
    'You are the brand studio lead. Read these brand guidelines and return the art direction '
    'that an image model needs, as JSON. Keep each field short and concrete. '
    'Copy hex codes exactly as written.\n\n'
)

ART_DIRECTION_SCHEMA = {
    'type': 'object',
    'properties': {
        'voice': {'type': 'string', 'description': 'How the brand writes, in two sentences.'},
        'light': {'type': 'string'},
        'surfaces': {'type': 'array', 'items': {'type': 'string'}},
        'props': {'type': 'array', 'items': {'type': 'string'}},
        'story': {'type': 'string', 'description': 'How pictures show the product and its ritual.'},
        'composition': {'type': 'string'},
        'never': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Things that must never appear in a picture.'},
    },
    'required': ['voice', 'light', 'surfaces', 'props', 'story', 'composition', 'never'],
}


@pxt.udf
def art_direction_prompt(style_guide: str) -> str:
    return ART_DIRECTION_PROMPT + style_guide


# ---------------------------------------------------------------------------
# Templates. Every creative prompt is a row in `directions` or `moments`, with
# {slots}. These functions only fill the slots from the brand kits, the set,
# and the moment.
# ---------------------------------------------------------------------------


@pxt.udf
def fill(template: pxt.Json, context: pxt.Json) -> str:
    """A template from a directions or moments row, with its {slots} filled in."""
    return template.format_map(context)


def _bullets(items) -> str:
    return '\n'.join(f'- {item}' for item in items)


@pxt.udf
def campaign_context(
    playbook: pxt.Json, style: pxt.Json, partner: pxt.Json | None, brief: str, moments: pxt.Json
) -> pxt.Json:
    """The slots every template in a campaign can use."""
    kits = [style] + ([partner] if partner else [])
    names = [k['name'] for k in kits]
    if partner:
        wordmarks = f'the {names[0]} and {names[1]} wordmarks, exactly as attached, {playbook["lockup"]}'
    else:
        wordmarks = f'the {names[0]} wordmark, exactly as attached'
    brands = []
    for k in kits:
        ad = k['art_direction']
        brands.append(
            f"{k['name']} ({k['category']}). Palette: {_palette_line(k['palette'])}. Light: {ad['light']} "
            f"Surfaces: {', '.join(ad['surfaces'])}. Props: {', '.join(ad['props'])}. Story: {ad['story']}"
        )
    # In a collaboration the first brand owns the room, so its rules are {never}.
    # {never_all} adds the partner's, for templates that want both.
    inks = [f"{k['name']} in {_ink(k['palette'])}" for k in kits]
    never = list(style['art_direction']['never'])
    never_all = [n for k in kits for n in k['art_direction']['never']]
    return {
        'brief': brief,
        'lockup': ' × '.join(names),
        'names': ' and '.join(f'"{n}"' for n in names),
        'wordmarks': wordmarks,
        # Each wordmark in its own brand's ink color, for moments that color the letters.
        'letter_colors': inks[0].split(' in ', 1)[1] if not partner else ' and '.join(inks),
        'brands': '\n'.join(brands),
        'pairing': playbook['pairing'] if partner else playbook['solo'],
        'house_rules': _bullets(playbook['house_rules']),
        'never': '; '.join(never),
        'never_all': '; '.join(never_all),
        # The room must have every moment's subject. Lettering comes later, shot by shot.
        'needs': _bullets(m['subject'] for m in moments),
    }


WORLD_SCHEMA = {
    'type': 'object',
    'properties': {
        'set': {'type': 'string', 'description': 'The place, in two or three concrete sentences: room, layout, and what is in it.'},
        'palette': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string'},
                    'hex': {'type': 'string'},
                    'where': {'type': 'string', 'description': 'Which surfaces in the set are this color.'},
                },
                'required': ['name', 'hex', 'where'],
            },
        },
        'materials': {'type': 'array', 'items': {'type': 'string'}},
        'hardware': {'type': 'string', 'description': 'Taps, hooks, handles, and their finish.'},
        'light': {'type': 'string'},
        'styling': {'type': 'string', 'description': 'How the products and props are placed in the set.'},
    },
    'required': ['set', 'palette', 'materials', 'hardware', 'light', 'styling'],
}


@pxt.udf
def with_world(context: pxt.Json, world: pxt.Json) -> pxt.Json:
    """The campaign slots plus {world}: the set the designer returned, as prompt lines."""
    lines = [
        f"The set: {world['set']}",
        'Colors: ' + '; '.join(f"{c['name']} {c['hex']} on {c['where']}" for c in world['palette']) + '.',
        f"Materials: {', '.join(world['materials'])}. Hardware: {world['hardware']}.",
        f"Light: {world['light']}",
    ]
    return {**context, 'world': '\n'.join(lines), 'styling': world['styling']}


@pxt.udf
def styles(brand: str, style: str, partner: str | None, partner_style: str | None) -> pxt.Json:
    """Each brand in the campaign, with its wordmark style."""
    out = {brand: style}
    if partner:
        out[partner] = partner_style
    return out


@pxt.udf
def shot_context(context: pxt.Json, products: pxt.Json, spec: pxt.Json, wordmark_styles: pxt.Json) -> pxt.Json:
    """The campaign and set slots plus the moment's own: {subject}, {treatment}, {framing}, {products}."""
    misfits = [f'{b} ({s})' for b, s in wordmark_styles.items() if s not in spec['fits']]
    if misfits:
        raise ValueError(
            f"{spec['moment']} cannot carry the wordmark of {', '.join(misfits)}: "
            f"its material can only make {', '.join(spec['fits'])}"
        )
    shown = products if spec['show_products'] else []
    # Products are shown, not named: a named product tempts the image model to invent label text.
    product_line = (
        f"{context['styling']} The products are the {len(shown)} in the attached packshots, exactly as they look, "
        'with labels that show only what the packshots show.'
        if shown
        else 'No products in this shot.'
    )
    return {
        **context,
        'subject': spec['subject'],
        'blank': spec['blank'],
        'treatment': spec['treatment'].format_map(context),
        'physics': spec['physics'],
        'framing': spec['framing'],
        'products': product_line,
        # What the finished clip shows, which differs from the prompt when the clip plays backwards.
        'motion': spec['motion'].get('shows', spec['motion']['prompt']),
    }


@pxt.udf
def plate_input(prompt: str, references: pxt.Json) -> pxt.Json:
    """The establishing shot's input: library photos for mood, then the prompt."""
    parts: list = []
    for r in references:
        parts += ['Brand photography. Match its light and mood, not its content.', r['image']]
    return parts + [prompt]


@pxt.udf
def image_config(aspect_ratio: str) -> pxt.Json:
    return {'response_modalities': ['IMAGE'], 'image_config': {'aspect_ratio': aspect_ratio, 'image_size': '2K'}}


@pxt.udf
def shot_input(prompt: str, plate: pxt.Image, products: pxt.Json, spec: pxt.Json) -> pxt.Json:
    """The base shot's input: the set, the packshots, then the prompt. No logos: the surface stays blank."""
    # Every reference is labeled as a reference, so the model photographs the scene fresh instead of pasting them in.
    parts: list = [
        'Reference for the room only: its colors, materials, and hardware. Do not paste, frame, or reuse this '
        'picture. Photograph the room fresh from the camera position described below.',
        plate,
    ]
    if spec['show_products']:
        for p in products:
            parts += [
                'Reference for one of the products. Place the real product in the scene, standing on a surface and lit '
                'by the room, with its label exactly as shown. Never paste this picture or its background.',
                p['packshot'],
            ]
    return parts + [prompt]


@pxt.udf
def letter_input(prompt: str, base: pxt.Image, visuals: pxt.Json, partner_visuals: pxt.Json | None) -> pxt.Json:
    """The image model's edit: the base photo, the wordmarks, then the prompt."""
    parts: list = ['The photograph to edit.', base]
    for v in [visuals] + ([partner_visuals] if partner_visuals else []):
        parts += [f"Reference for the {v['name']} wordmark: copy these letterforms exactly, in this typeface and case.", v['logo']]
    return parts + [prompt]


REVIEW_SCHEMA = {
    'type': 'object',
    'properties': {
        'text_seen': {'type': 'string', 'description': 'Every word visible in the picture, exactly as written, in reading order.'},
        'spelling_ok': {'type': 'boolean', 'description': 'True only if every brand name appears spelled and cased exactly.'},
        'extra_text': {'type': 'boolean', 'description': 'True if there are words other than the brand names and product labels.'},
        'physically_made': {'type': 'boolean', 'description': 'True only if the words are made from the material as described, not laid on top of it.'},
        'looks_real': {
            'type': 'boolean',
            'description': 'False if there are pasted-in or duplicated objects, warped or impossible geometry, '
            'text laid on top of a surface, or smooth plastic computer-rendered surfaces. Otherwise true.',
        },
        'blocking': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Problems that stop this shot from shipping.'},
        'minor': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Small flaws worth noting that do not stop it.'},
        'notes': {'type': 'string', 'description': 'The verdict in one or two sentences.'},
        'approved': {'type': 'boolean', 'description': 'True if and only if there are no blocking problems.'},
    },
    'required': ['text_seen', 'spelling_ok', 'extra_text', 'physically_made', 'looks_real', 'blocking', 'minor', 'notes', 'approved'],
}


@pxt.udf
def review_input(still: pxt.Image, prompt: str) -> pxt.Json:
    return [still, prompt]


@pxt.udf
def pick_version(ai_approved: bool | None, code_approved: bool | None) -> pxt.String | None:
    """Which version ships: 'code' when it passed review, since its letters are exact, else 'ai' if that passed."""
    if code_approved:
        return 'code'
    if ai_approved:
        return 'ai'
    return None


@pxt.udf
def pick(version: str | None, ai: pxt.Image | None, code: pxt.Image | None) -> pxt.Image | None:
    """The image of the version that ships."""
    return {'ai': ai, 'code': code}.get(version)


@pxt.udf
def verdict(review: pxt.Json | None) -> pxt.Bool | None:
    """A review's approval as its own column. Empty when nothing was reviewed."""
    return None if review is None else bool(review['approved'])


CLIP_REVIEW_SCHEMA = {
    'type': 'object',
    'properties': {
        'words_hold': {'type': 'boolean', 'description': 'True if the brand names stay legible and correctly spelled whenever they are visible.'},
        'glitches': {'type': 'array', 'items': {'type': 'string'}, 'description': 'Objects that appear, vanish, warp, or move unnaturally.'},
        'motion_ok': {'type': 'boolean', 'description': 'True if the motion matches what was asked.'},
        'notes': {'type': 'string'},
        'approved': {'type': 'boolean'},
    },
    'required': ['words_hold', 'glitches', 'motion_ok', 'notes', 'approved'],
}


@pxt.udf
def clip_review_input(clip: pxt.Video, prompt: str) -> pxt.Json:
    """The clip reviewer's input. Pixeltable sends the video file to Gemini."""
    return [clip, prompt]


# ---------------------------------------------------------------------------
# Products: one studio packshot per SKU, so every shot shows the same product.
# ---------------------------------------------------------------------------

PACKSHOT_TEMPLATE = (
    'A product packshot of {name} by {brand}. {packaging} '
    'The product stands alone, centered, on a seamless backdrop in {background}, with a soft, natural shadow. '
    'Soft, even studio daylight. Photoreal, sharp, high end beauty catalog. '
    'The label shows the attached wordmark exactly, letter for letter, and no other words.'
)


@pxt.udf
def packshot_input(name: str, packaging: str, visuals: pxt.Json, style: pxt.Json, photo: pxt.Image | None) -> pxt.Json:
    background = next(s for s in style['palette'] if s['role'] == 'background')
    prompt = PACKSHOT_TEMPLATE.format(
        name=name, brand=style['name'], packaging=packaging, background=f"{background['name']} {background['hex']}"
    )
    parts = [f"The {style['name']} wordmark:", visuals['logo']]
    if photo is not None:
        parts += ['A phone photo of the real product. Keep its exact shape and materials.', photo]
    return parts + [prompt]


@pxt.udf
def first_image(response: pxt.Json) -> pxt.Image:
    """The image part of a Gemini response."""
    # Thinking models can return draft images marked as thoughts. The answer is the last image that is not one.
    images = [
        p['inline_data']['data']
        for p in response['candidates'][0]['content']['parts']
        if (p.get('inline_data') or {}).get('data') is not None and not p.get('thought')
    ]
    if not images:
        raise ValueError('the model returned no image')
    data = images[-1]
    return data if isinstance(data, Image.Image) else Image.open(io.BytesIO(data))


# ---------------------------------------------------------------------------
# Letters laid by code: the same blank surface, with the wordmarks set into it
# from the logo files. The letters are always exact; the material does the rest.
# ---------------------------------------------------------------------------


def _as_image(value) -> Image.Image:
    return value if isinstance(value, Image.Image) else Image.open(value)


def _lockup(logos: list, colors: list) -> Image.Image:
    """The wordmarks as one RGBA picture, each in its brand's color: one logo, or two at the same width with a × between."""
    marks = []
    for logo, color in zip(logos, colors):
        alpha = _as_image(logo).convert('RGBA').getchannel('A')
        alpha = alpha.crop(alpha.getbbox())
        mark = Image.new('RGBA', alpha.size, _rgb(color) + (0,))
        mark.putalpha(alpha)
        marks.append(mark)
    if len(marks) == 1:
        return marks[0]
    width = max(m.width for m in marks)
    marks = [m.resize((width, round(m.height * width / m.width)), Image.LANCZOS) for m in marks]
    cross = round(0.42 * min(m.height for m in marks))
    gap = round(0.45 * cross)
    out = Image.new('RGBA', (width, marks[0].height + 2 * gap + cross + marks[1].height), (0, 0, 0, 0))
    out.alpha_composite(marks[0], (0, 0))
    out.alpha_composite(marks[1], (0, out.height - marks[1].height))
    d = ImageDraw.Draw(out)
    cx, cy, r = width / 2, marks[0].height + gap + cross / 2, cross / 2
    stroke = max(2, round(cross * 0.1))
    for a, b in (((cx - r, cy - r), (cx + r, cy + r)), ((cx - r, cy + r), (cx + r, cy - r))):
        d.line([a, b], fill=_rgb(colors[0]) + (255,), width=stroke)
    return out


def _tiles(gray):
    """Find every tile. Grout is the thin network that is lighter, or darker, than its neighborhood.

    Returns a tile number per pixel (0 for grout and anything that is not a tile) and the grout mask.
    """
    import numpy as np
    from scipy import ndimage as ndi

    g = gray.astype(np.float32)
    local = ndi.uniform_filter(g, size=max(15, g.shape[1] // 24))
    best = None
    for sign in (1, -1):  # light grout, then dark grout
        grout = ndi.binary_closing(sign * (g - local) > 2, np.ones((3, 3)))
        labels, _ = ndi.label(ndi.binary_erosion(~grout, np.ones((3, 3))))
        boxes = ndi.find_objects(labels)
        if not boxes:
            continue
        area = np.bincount(labels.ravel())[1:]
        w = np.array([b[1].stop - b[1].start for b in boxes])
        h = np.array([b[0].stop - b[0].start for b in boxes])
        typical = np.median(area[area > 30]) if (area > 30).any() else 0
        ok = (area > 0.35 * typical) & (area < 2.2 * typical) & (w < 1.6 * h) & (h < 1.6 * w)
        if best is None or ok.sum() > best[1].sum():
            best = (labels, ok, grout)
    if best is None or best[1].sum() < 50:
        raise ValueError('could not find a tile grid in the base image')
    labels, ok, grout = best
    keep = np.concatenate([[False], ok])
    return np.where(keep[labels], labels, 0), grout


def _inlay(base: Image.Image, lockup: Image.Image, width: float = 0.78, seed: int = 7) -> Image.Image:
    """Inlay the wordmarks into a tiled floor, the way a stone setter would.

    Each letter is one piece of matte tile in its brand's color, cut to the exact logo shape, with a fine
    joint around it where the floor tiles were cut to fit. The letters take the floor's own light, so a
    patch of sun across the floor crosses them too.
    """
    import numpy as np
    from scipy import ndimage as ndi

    rgb = np.asarray(base.convert('RGB')).astype(np.float32)
    gray = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    labels, grout = _tiles(gray)
    area = np.bincount(labels.ravel())[1:]
    pitch = np.sqrt(np.median(area[area > 0]))

    # Place the lettering in the middle of the tiled floor.
    ys, xs = np.nonzero(labels)
    x0, x1 = np.percentile(xs, [4, 96])
    y0, y1 = np.percentile(ys, [4, 96])
    scale = min(width * (x1 - x0) / lockup.width, 0.6 * (y1 - y0) / lockup.height)
    mw, mh = max(1, round(lockup.width * scale)), max(1, round(lockup.height * scale))
    left, top = round((x0 + x1 - mw) / 2), round((y0 + y1 - mh) / 2)
    placed = Image.new('RGBA', base.size, (0, 0, 0, 0))
    placed.alpha_composite(lockup.resize((mw, mh), Image.LANCZOS), (left, top))
    placed = np.asarray(placed).astype(np.float32)
    alpha, color = placed[..., 3:] / 255, placed[..., :3]

    # The floor's light without its grid: blur away the grout, keep the gradients and the sun.
    floor = gray[labels > 0].mean()
    light = ndi.gaussian_filter(np.where(grout, floor, gray), pitch) / floor
    rng = np.random.default_rng(seed)
    grain = ndi.gaussian_filter(rng.normal(0, 7, gray.shape), 1.0)[..., None]  # matte, fine-grained
    # Each piece has a slightly eased edge: the top edges catch the light, the bottom edges fall into shadow.
    soft = ndi.gaussian_filter(alpha[..., 0], max(1.0, pitch * 0.04))
    bevel = ndi.sobel(soft, axis=0)[..., None] * 60
    letter = color * light[..., None] + grain + bevel
    out = rgb * (1 - alpha) + letter * alpha

    # A fine joint around every letter, in the floor's grout color, where the floor tiles were cut to fit.
    solid = alpha[..., 0] > 0.5
    joint = max(2.5, pitch * 0.07)
    ring = (ndi.distance_transform_edt(~solid) <= joint) & ~solid
    ring = ndi.gaussian_filter(ring.astype(np.float32), 0.7)[..., None]
    grout_color = np.median(rgb[grout], axis=0) * light[..., None]
    out = out * (1 - ring) + grout_color * ring
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


COMPOSITORS = {'inlay': _inlay}


@pxt.udf
def lay_letters(
    base: pxt.Image, spec: pxt.Json, visuals: pxt.Json, partner_visuals: pxt.Json | None, style: pxt.Json, partner: pxt.Json | None
) -> pxt.Image | None:
    """The code version of a shot: the exact logo files set into the blank base by the moment's compositor.

    Each wordmark takes its brand's ink color. Empty for a moment with no compositor, such as a woven label.
    """
    method = spec.get('composite')
    if method is None:
        return None
    kits = [(visuals, style)] + ([(partner_visuals, partner)] if partner_visuals else [])
    lockup = _lockup([v['logo'] for v, _ in kits], [_color(s['palette'], 'ink') for _, s in kits])
    return COMPOSITORS[method](base, lockup)


# ---------------------------------------------------------------------------
# Motion: Gemini Omni animates an approved still. A reveal plays backwards.
# ---------------------------------------------------------------------------

VIDEO_TIMEOUT_SECONDS = 240


@pxt.udf
def animate(final: pxt.Image | None, spec: pxt.Json, enabled: bool, model: str) -> pxt.Video | None:
    """A short clip from the version that ships, made only after it passes review.

    With `reverse`, Omni starts from the approved still and takes the words away (the fog on a
    mirror clears), and the clip plays backwards: the fog forms and the words appear, ending on
    the exact still the reviewer approved.
    """
    import base64

    from pixeltable.runtime import get_runtime

    if not enabled:
        return None
    if final is None:
        raise ValueError('not animated: no version of this shot passed review')
    motion = spec['motion']
    buf = io.BytesIO()
    final.convert('RGB').save(buf, format='JPEG', quality=92)
    client = get_runtime().get_client('gemini')
    interaction = client.interactions.create(
        model=model,
        input=[
            {'type': 'image', 'data': base64.b64encode(buf.getvalue()).decode('ascii'), 'mime_type': 'image/jpeg'},
            {'type': 'text', 'text': f"<FIRST_FRAME> {motion['prompt']}"},
        ],
        response_format={'type': 'video', 'aspect_ratio': spec['aspect_ratio'], 'duration': f"{motion['seconds']}s"},
        timeout=VIDEO_TIMEOUT_SECONDS,
    )
    raw = _video_bytes(client, interaction.output_video)
    path = TempStore.create_path(extension='.mp4')
    frames, rate = _decode(raw)
    _encode(list(reversed(frames)) if motion.get('reverse') else frames, rate, path)
    return str(path)


@pxt.udf
def stitch(clips: pxt.Json, sequence: pxt.Json) -> pxt.Video:
    """Cut the campaign's clips together, in the order the reel lists its moments."""
    by_moment = {c['moment']: c['clip'] for c in clips if c['clip'] and (c['review'] or {}).get('approved')}
    missing = [m for m in sequence if m not in by_moment]
    if missing:
        raise ValueError(f'no approved clip yet for: {", ".join(missing)}')
    frames: list = []
    rate = None
    size = None
    for m in sequence:
        with open(by_moment[m], 'rb') as f:
            clip_frames, clip_rate = _decode(f.read())
        rate = rate or clip_rate
        size = size or clip_frames[0].size
        frames += [im if im.size == size else ImageOps.fit(im, size, Image.LANCZOS) for im in clip_frames]
    path = TempStore.create_path(extension='.mp4')
    _encode(frames, rate, path)
    return str(path)


def _video_bytes(client, video) -> bytes:
    import base64

    if video is None:
        raise RuntimeError('the video model returned no video')
    if getattr(video, 'data', None):
        return base64.b64decode(video.data)
    if getattr(video, 'uri', None):
        return client.files.download(file=video.uri)
    raise RuntimeError('the video model returned no video')


def _decode(raw: bytes) -> tuple[list[Image.Image], object]:
    with av.open(io.BytesIO(raw)) as src:
        stream = src.streams.video[0]
        rate = stream.average_rate or 24
        return [f.to_image() for f in src.decode(stream)], rate


def _encode(frames: list[Image.Image], rate, path) -> None:
    """Write frames as an H.264 MP4, without sound."""
    with av.open(str(path), 'w') as dst:
        out = dst.add_stream('libx264', rate=rate)
        out.width, out.height = frames[0].size
        out.pix_fmt = 'yuv420p'
        out.options = {'crf': '18'}
        for im in frames:
            for packet in out.encode(av.VideoFrame.from_image(im)):
                dst.mux(packet)
        for packet in out.encode():
            dst.mux(packet)
