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
def art_direction_prompt(style_guide: str, wording: pxt.Json) -> str:
    """The art direction prompt: the `art_direction` row, with the style guide filled in."""
    return _words(wording)['art_direction'].format(style_guide=style_guide)


# ---------------------------------------------------------------------------
# Templates. Every creative prompt is a row in `directions` or `moments`, with
# {slots}. These functions only fill the slots from the brand kits, the set,
# and the moment.
# ---------------------------------------------------------------------------


@pxt.udf
def fill(template: pxt.Json, context: pxt.Json) -> str:
    """A template from a directions or moments row, with its {slots} filled in."""
    return template.format_map(context)


def _words(wording) -> dict:
    """The `prompts` table as {name: template}."""
    return {r['name']: r['template'] for r in wording}


def _bullets(items) -> str:
    return '\n'.join(f'- {item}' for item in items)


@pxt.udf
def campaign_context(
    playbook: pxt.Json,
    style: pxt.Json,
    partner: pxt.Json | None,
    brief: str,
    moments: pxt.Json,
    wordmark_looks: pxt.Json,
    wording: pxt.Json,
) -> pxt.Json:
    """The slots every template in a campaign can use, worded by the `prompts` rows."""
    words = _words(wording)
    kits = [style] + ([partner] if partner else [])
    names = [k['name'] for k in kits]
    looks = list(wordmark_looks.values())
    inks = [_ink(k['palette']) for k in kits]
    pair = {'name': names[0], 'look': looks[0], 'ink': inks[0], 'lockup': playbook['lockup']}
    if partner:
        pair |= {'partner_name': names[1], 'partner_look': looks[1], 'partner_ink': inks[1]}
    count = 'two' if partner else 'one'
    brands = [
        words['brand_line'].format(
            name=k['name'],
            category=k['category'],
            palette=_palette_line(k['palette']),
            light=k['art_direction']['light'],
            surfaces=', '.join(k['art_direction']['surfaces']),
            props=', '.join(k['art_direction']['props']),
            story=k['art_direction']['story'],
        )
        for k in kits
    ]
    # In a collaboration the first brand owns the set, so its rules are {never}.
    # {never_all} adds the partner's, for templates that want both.
    never = list(style['art_direction']['never'])
    never_all = [n for k in kits for n in k['art_direction']['never']]
    return {
        'words': words,
        'pair': pair,
        'brief': brief,
        'lockup': ' × '.join(names),
        'names': ' and '.join(f'"{n}"' for n in names),
        'wordmarks': words[f'wordmark_{count}'].format(**pair),
        'letter_colors': words[f'letter_colors_{count}'].format(**pair),
        'brands': '\n'.join(brands),
        'pairing': playbook['pairing'] if partner else playbook['solo'],
        'house_rules': _bullets(playbook['house_rules']),
        'never': '; '.join(never),
        'never_all': '; '.join(never_all),
        # The set must have every moment's subject. Lettering comes later, shot by shot.
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
    """The campaign slots plus {world}: the set the designer returned, worded by the `world` row."""
    words = context['words']
    colors = '; '.join(
        words['world_color'].format(name=c.get('name', ''), hex=c.get('hex', ''), where=c.get('where', '')) for c in world['palette']
    )
    text = words['world'].format(
        set=world['set'], colors=colors, materials=', '.join(map(str, world['materials'])), hardware=world['hardware'], light=world['light']
    )
    return {**context, 'world': text, 'styling': world['styling']}


@pxt.udf
def styles(brand: str, style: str, partner: str | None, partner_style: str | None) -> pxt.Json:
    """Each brand in the campaign, with its wordmark style."""
    out = {brand: style}
    if partner:
        out[partner] = partner_style
    return out


@pxt.udf
def shot_context(context: pxt.Json, products: pxt.Json, spec: pxt.Json) -> pxt.Json:
    """The campaign and set slots plus the moment's own, worded by the `prompts` rows.

    The code only counts the attached images, so each label names the right one.
    """
    words, pair = context['words'], context['pair']
    # Products are shown, not named: a named product tempts the image model to invent label text.
    shown = products if spec['show_products'] else []
    if shown:
        packshots = 'Image 2' if len(shown) == 1 else f'Images 2 to {1 + len(shown)}'
        base_images = words['base_images_products'].format(packshots=packshots)
        product_line = words['products_shown'].format(styling=context['styling'], count=len(shown))
    else:
        base_images = words['base_images']
        product_line = words['products_none']
    letter_images = words['letter_images_two' if 'partner_name' in pair else 'letter_images_one'].format(**pair)
    return {
        **context,
        'base_images': base_images,
        'letter_images': letter_images,
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
    return [r['image'] for r in references] + [prompt]


@pxt.udf
def image_config(aspect_ratio: str) -> pxt.Json:
    return {'response_modalities': ['IMAGE'], 'image_config': {'aspect_ratio': aspect_ratio, 'image_size': '2K'}}


@pxt.udf
def shot_input(prompt: str, plate: pxt.Image, products: pxt.Json, spec: pxt.Json) -> pxt.Json:
    """The base shot's input: Image 1 the room, then the packshots, then the prompt that names them."""
    packshots = [p['packshot'] for p in products] if spec['show_products'] else []
    return [plate, *packshots, prompt]


@pxt.udf
def letter_input(prompt: str, base: pxt.Image, visuals: pxt.Json, partner_visuals: pxt.Json | None) -> pxt.Json:
    """The edit's input: Image 1 the base photo, then each logo, then the prompt that names them."""
    logos = [visuals['logo']] + ([partner_visuals['logo']] if partner_visuals else [])
    return [base, *logos, prompt]


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

@pxt.udf
def packshot_prompt(name: str, packaging: str, style: pxt.Json, photo: pxt.Image | None, wording: pxt.Json) -> str:
    """The packshot prompt: the `packshot` row, with the product and each attached image filled in."""
    words = _words(wording)
    background = next(s for s in style['palette'] if s['role'] == 'background')
    images = words['packshot_images_photo' if photo is not None else 'packshot_images'].format(brand=style['name'])
    return words['packshot'].format(
        images=images, name=name, brand=style['name'], packaging=packaging, background=f"{background['name']} {background['hex']}"
    )


@pxt.udf
def packshot_input(prompt: str, visuals: pxt.Json, photo: pxt.Image | None) -> pxt.Json:
    """Image 1 the logo, Image 2 the phone photo if there is one, then the prompt."""
    return [visuals['logo']] + ([photo] if photo is not None else []) + [prompt]


@pxt.udf
def logo_stencil(logo: pxt.Image) -> pxt.Image:
    """A logo as a stencil: its letter shapes in white on black, with none of the logo's own color."""
    rgba = logo.convert('RGBA')
    alpha = rgba.getchannel('A')
    if alpha.getextrema()[0] < 255:
        mask = alpha  # a transparent logo: the letters are wherever it is opaque
    else:
        mask = ImageOps.invert(rgba.convert('L'))  # dark ink on white: the letters are the dark parts
    pad = mask.height // 3
    out = Image.new('L', (mask.width + 2 * pad, mask.height + 2 * pad), 0)
    out.paste(mask, (pad, pad))
    return out.convert('RGB')


def _ink(stencil: Image.Image) -> Image.Image:
    """A stencil cropped to its letters, as a mask."""
    mask = stencil.convert('L')
    return mask.crop(mask.getbbox())


@pxt.udf
def logo_lockup(house_stencil: pxt.Image, guest_stencil: pxt.Image) -> pxt.Image:
    """The collaboration lockup: the house logo, a small x, and the partner logo, stacked. White on black."""
    top, bottom = _ink(house_stencil), _ink(guest_stencil)
    height = max(top.height, bottom.height)
    cross, gap = round(height * 0.34), round(height * 0.42)
    width = max(top.width, bottom.width)
    out = Image.new('L', (width, top.height + gap + cross + gap + bottom.height), 0)
    out.paste(top, ((width - top.width) // 2, 0))
    x0, y0 = (width - cross) // 2, top.height + gap
    stroke = max(4, round(height * 0.045))
    draw = ImageDraw.Draw(out)
    draw.line([(x0, y0), (x0 + cross, y0 + cross)], fill=255, width=stroke)
    draw.line([(x0 + cross, y0), (x0, y0 + cross)], fill=255, width=stroke)
    out.paste(bottom, ((width - bottom.width) // 2, y0 + cross + gap))
    return out.convert('RGB')


GUIDE_COLOR = (255, 0, 255)  # magenta: a color no scene has, so the image model can tell the marks from the photo


@pxt.udf
def logo_guide(scene: pxt.Image, lockup: pxt.Image, box: pxt.Json) -> pxt.Image:
    """The scene with the lockup marked on its surface in flat magenta, centered in the surface's box.

    `box` is where the surface is, as ymin, xmin, ymax, xmax from 0 to 1000. The lockup spans about
    two thirds of the surface's width, and no more than half its height.
    """
    scene = scene.convert('RGB')
    x0, x1 = (box[k] / 1000 * scene.width for k in ('xmin', 'xmax'))
    y0, y1 = (box[k] / 1000 * scene.height for k in ('ymin', 'ymax'))
    mask = lockup.convert('L')
    scale = min((x1 - x0) * 0.64 / mask.width, (y1 - y0) * 0.5 / mask.height)
    mask = mask.resize((max(1, round(mask.width * scale)), max(1, round(mask.height * scale))), Image.LANCZOS)
    left, top = round((x0 + x1) / 2 - mask.width / 2), round((y0 + y1) / 2 - mask.height / 2)
    out = scene.copy()
    out.paste(Image.new('RGB', mask.size, GUIDE_COLOR), (left, top), mask)
    return out


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


def _mosaic(base: Image.Image, lockup: Image.Image, width: float = 0.8, seed: int = 7) -> Image.Image:
    """Mosaic lettering: the wordmarks spelled out in whole tiles of the floor's own grid, in each brand's ink.

    A tile joins a letter when the lettering covers at least half of it, and no stroke is thinner than one
    tile. Each letter tile keeps the original tile's light and texture, recolored.
    """
    import numpy as np
    from scipy import ndimage as ndi

    rgb = np.asarray(base.convert('RGB')).astype(np.float32)
    gray = rgb @ np.array([0.299, 0.587, 0.114], np.float32)
    labels, grout = _tiles(gray)
    n = labels.max() + 1
    area = np.bincount(labels.ravel(), minlength=n).astype(np.float32)
    pitch = np.sqrt(np.median(area[1:][area[1:] > 0])) * 1.12  # a tile plus its grout

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
    inside = placed[..., 3] > 127

    # No stroke thinner than one tile.
    stroke = 2 * np.percentile(ndi.distance_transform_edt(inside)[inside], 95)
    if stroke < pitch:
        grown = ndi.distance_transform_edt(~inside) <= (pitch - stroke) / 2
        nearest = ndi.distance_transform_edt(~inside, return_distances=False, return_indices=True)
        placed = placed[nearest[0], nearest[1]]  # each new pixel takes the color of the letter it grew from
        inside = grown

    # A tile joins a letter when the lettering covers at least half of it, and takes that letter's ink.
    covered = np.bincount(labels.ravel(), weights=inside.ravel().astype(np.float32), minlength=n)
    letter = covered / np.maximum(area, 1) >= 0.5
    letter[0] = False
    ink = np.stack(
        [np.bincount(labels.ravel(), weights=(placed[..., c] * inside).ravel(), minlength=n) for c in range(3)], axis=1
    ) / np.maximum(covered, 1)[:, None]

    # Recolor: the ink, shaded by the tile's own light and texture, with a little tile-to-tile variation.
    tile_mean = np.bincount(labels.ravel(), weights=gray.ravel(), minlength=n) / np.maximum(area, 1)
    shade = gray / np.maximum(tile_mean[labels], 1)
    jitter = np.random.default_rng(seed).uniform(0.95, 1.05, n).astype(np.float32)
    recolored = ink[labels] * (shade * jitter[labels])[..., None]
    out = np.where(letter[labels][..., None], recolored, rgb)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


COMPOSITORS = {'mosaic': _mosaic}


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
