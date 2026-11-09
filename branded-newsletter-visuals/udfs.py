"""The brand plate for the Issues table.

The prompts live in schema.py. This file holds the optional inspiration image
for the picture prompt and the Pillow drawing. The video comes from Pixeltable's
built-in Gemini function, called in schema.py. The plate draws the issue label the schema already formatted, so the words on the
cover and the words in the video prompt are the same column.
"""

from pathlib import Path

import pixeltable as pxt
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

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
