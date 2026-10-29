"""The brand plate and the video call for the Issues table.

The prompts live in schema.py. This file holds the optional inspiration image
for the picture prompt, the Pillow drawing, and the video call. The
plate draws the issue label the schema already formatted, so the words on the
cover and the words in the video prompt are the same column.

Gemini Omni Flash makes the video through the Interactions API. The cover
image is the first frame.
"""

import base64
import io
from pathlib import Path

import pixeltable as pxt
from pixeltable.utils.local_store import TempStore
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

# Omni usually answers in under a minute. A stalled call becomes an error on that row after this many seconds.
VIDEO_TIMEOUT_SECONDS = 180

NEWSLETTER_NAME = "RAMI'S DATA NEWSLETTER"
_FONTS = Path(__file__).parent / 'fonts'
_PINK_CORE = (255, 150, 232, 255)
_PINK_GLOW = (255, 40, 200, 255)
_WHITE = (255, 255, 255, 255)
_RED_GLOW = (255, 30, 60, 255)


def _glow(mask: Image.Image, color: tuple, radius: float, strength: float = 1.0) -> Image.Image:
    """A soft halo in one color around the white parts of a mask: a tight blur plus a faint wide one."""
    tight = mask.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * strength)))
    wide = mask.filter(ImageFilter.GaussianBlur(radius * 3)).point(lambda v: min(255, int(v * strength * 0.6)))
    alpha = ImageChops.lighter(tight, wide)
    return Image.merge('RGBA', (*Image.new('RGB', mask.size, color[:3]).split(), alpha))


def _text_mask(size, xy, text, font, stroke=0, tracking=0) -> Image.Image:
    """White text on black, one letter at a time so `tracking` can add space between letters."""
    mask = Image.new('L', size, 0)
    draw = ImageDraw.Draw(mask)
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
        x += font.getlength(ch) + tracking
    return mask


def _tracked_length(text, font, tracking) -> float:
    return sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)


@pxt.udf
def note_if_image(inspiration: pxt.Image | None, note: pxt.String) -> pxt.String:
    """The note when the row has an inspiration image, and an empty string when it doesn't."""
    return '' if inspiration is None else note


@pxt.udf
def art_input(prompt: pxt.String, inspiration: pxt.Image | None) -> pxt.Json:
    """The prompt alone, or the inspiration image followed by the prompt."""
    if inspiration is None:
        return prompt
    return [inspiration, prompt]


@pxt.udf
def make_plate(art: pxt.Image, issue_label: pxt.String) -> pxt.Image:
    """Transparent plate the size of the art: a pink neon issue line and a hollow white name with a red glow."""
    width, height = art.size
    size = (width, height)
    glow_r = height * 0.006

    # The issue line: tall condensed letters, drawn and then squeezed to 86% of their width.
    issue_font = ImageFont.truetype(_FONTS / 'BarlowCondensed-Medium.ttf', int(height * 0.145))
    box = issue_font.getbbox(issue_label)
    pad = int(height * 0.03)
    tile = (box[2] + 2 * pad, box[3] + 2 * pad)
    issue_mask = _text_mask(tile, (pad, pad), issue_label, issue_font)
    issue_mask = issue_mask.resize((int(tile[0] * 0.86), tile[1]), Image.LANCZOS)
    full_issue = Image.new('L', size, 0)
    full_issue.paste(issue_mask, (int(width * 0.092) - pad, int(height * 0.045) - pad))

    # The name: heavy letters, drawn only as a white ring around their edge.
    name_font = ImageFont.truetype(_FONTS / 'Montserrat-Variable.ttf', 100)
    name_font.set_variation_by_name('SemiBold')
    # Size the name, with wide letter spacing, to span 61% of the width like the newsletter's own covers.
    span = _tracked_length(NEWSLETTER_NAME, name_font, 100 * 0.07)
    name_font = name_font.font_variant(size=int(100 * width * 0.61 / span))
    tracking = name_font.size * 0.07
    body = max(1, name_font.size // 30)
    ring = max(3, name_font.size // 16)
    name_xy = (int(width * 0.276), int(height * 0.825))
    outer = _text_mask(size, name_xy, NEWSLETTER_NAME, name_font, body + ring, tracking)
    inner = _text_mask(size, name_xy, NEWSLETTER_NAME, name_font, body, tracking)
    name_ring = ImageChops.subtract(outer, inner)

    plate = Image.new('RGBA', size, (0, 0, 0, 0))
    plate = Image.alpha_composite(plate, _glow(full_issue, _PINK_GLOW, glow_r * 1.5, 2.0))
    # A soft dark halo behind the name keeps hollow letters readable on a busy picture.
    shade = outer.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(height * 0.012))
    shade = shade.point(lambda v: v * 3 // 4)
    plate = Image.alpha_composite(plate, Image.merge('RGBA', (*Image.new('RGB', size, (0, 0, 0)).split(), shade)))
    plate = Image.alpha_composite(plate, _glow(name_ring, _RED_GLOW, glow_r, 2.5))
    plate.paste(_PINK_CORE, (0, 0), full_issue)
    plate.paste(_WHITE, (0, 0), name_ring)
    return plate


@pxt.udf
def composite_cover(art: pxt.Image, plate: pxt.Image) -> pxt.Image:
    """Lay the brand plate on the generated art."""
    merged = Image.alpha_composite(art.convert('RGBA'), plate.convert('RGBA'))
    return merged.convert('RGB')


@pxt.udf
def animate_cover(prompt: pxt.String, cover: pxt.Image, model: pxt.String, duration_seconds: pxt.Int) -> pxt.Video:
    """Animate the branded cover. The cover is the first frame of the video."""
    from pixeltable.runtime import get_runtime

    buf = io.BytesIO()
    cover.convert('RGB').save(buf, format='JPEG', quality=90)
    image_b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    client = get_runtime().get_client('gemini')
    interaction = client.interactions.create(
        model=model,
        input=[
            {'type': 'image', 'data': image_b64, 'mime_type': 'image/jpeg'},
            {'type': 'text', 'text': f'<FIRST_FRAME> {prompt}'},
        ],
        # The Interactions API takes the length as a string such as '5s'.
        response_format={
            'type': 'video',
            'aspect_ratio': '16:9',
            'duration': f'{duration_seconds}s',
        },
        timeout=VIDEO_TIMEOUT_SECONDS,
    )
    video = interaction.output_video
    raw = _video_bytes(client, video)
    # A file in Pixeltable's TempStore moves into the media store with the row.
    path = TempStore.create_path(extension='.mp4')
    path.write_bytes(raw)
    return str(path)


def _video_bytes(client: object, video: object) -> bytes:
    if video is None:
        raise RuntimeError('The video model returned no video.')
    data = getattr(video, 'data', None)
    if data:
        return base64.b64decode(data)
    uri = getattr(video, 'uri', None)
    if uri:
        return client.files.download(file=uri)
    raise RuntimeError('The video model returned no video.')
