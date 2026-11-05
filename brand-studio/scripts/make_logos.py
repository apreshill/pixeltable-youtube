"""Draw the ORIEL and brume wordmarks as transparent PNGs.

Maintainer script. The PNGs are committed under brand_kits/, so people running
the tutorial never need to run this. A real brand would upload its own logo files.

    uv run python scripts/make_logos.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KITS = Path(__file__).resolve().parent.parent / 'brand_kits'

WORDMARKS = {
    'oriel': {
        'text': 'ORIEL',
        'font': 'fonts/Jost-Variable.ttf',
        'weight': 300,
        'tracking': 0.42,
        'dark': '#33241D',
        'light': '#F4EDE3',
    },
    'brume': {
        'text': 'brume',
        'font': 'fonts/DMMono-Medium.ttf',
        'weight': None,
        'tracking': 0.04,
        'dark': '#1E2A2F',
        'light': '#E8EAE5',
    },
}

SIZE = 400  # font size in pixels; the PNGs are cropped to the letters plus a margin


def draw(spec: dict, color: str, kit: Path) -> Image.Image:
    font = ImageFont.truetype(kit / spec['font'], SIZE)
    if spec['weight'] is not None:
        font.set_variation_by_axes([spec['weight']])
    tracking = SIZE * spec['tracking']
    letters = spec['text']
    width = sum(font.getlength(ch) for ch in letters) + tracking * (len(letters) - 1)
    canvas = Image.new('RGBA', (int(width + SIZE), int(SIZE * 2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(canvas)
    x = SIZE / 2
    for ch in letters:
        d.text((x, SIZE / 2), ch, font=font, fill=color)
        x += font.getlength(ch) + tracking
    bbox = canvas.getbbox()
    pad = int(SIZE * 0.08)
    return canvas.crop((bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad))


def main() -> None:
    for slug, spec in WORDMARKS.items():
        kit = KITS / slug
        draw(spec, spec['dark'], kit).save(kit / 'logo-dark.png')
        draw(spec, spec['light'], kit).save(kit / 'logo-light.png')
        print(f'wrote {kit}/logo-dark.png and logo-light.png')


if __name__ == '__main__':
    main()
