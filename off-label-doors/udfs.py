"""The functions the paints table runs on each paint color.

- `bm_color`: reads a color's official data from its Benjamin Moore page.
- `fetch_image`: downloads Benjamin Moore's official photo of the color.
- `paint_chip`: draws a paint chip from the official hex, name, number, and LRV.
- `first_image`: pulls the picture out of a Gemini response.
"""

import io
import json
import re
import urllib.request

import pixeltable as pxt
from PIL import Image, ImageDraw, ImageFont

BM_COLOR_URL = 'https://www.benjaminmoore.com/en-us/paint-colors/color/{number}'
HEADERS = {'User-Agent': 'Mozilla/5.0 (pixeltable-youtube tutorial)'}


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


@pxt.udf
def bm_color(number: str) -> pxt.Json:
    """A Benjamin Moore color's official data, read from the data on its color page."""
    html = _get(BM_COLOR_URL.format(number=number)).decode('utf-8')
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if m is None:
        raise ValueError(f'no color data on the page for {number}')
    page = json.loads(m.group(1))
    c = page['props']['pageProps']['componentData']['components'][0]['color_data']['props']['color']
    tags = {t['tag']: t['value'] for t in c.get('tags', [])}
    return {
        'name': c['name'],
        'number': c['number'],
        'hex': '#' + c['hex'],
        'rgb': [c['r'], c['g'], c['b']],
        'lrv': c['lrv'],
        'family': c['family'],
        'subfamily': tags.get('Color Subfamily', []),
        'collection': re.sub(r'<[^>]+>|&reg;', '', (tags.get('Color Collection') or [''])[0]).strip(),
        'exterior': c['exterior_availability'] == 'available',
        'best_selling': c['is_best_selling'],
        'description': c['plain_description'],
        'photo_url': c['cdp_images'][0]['url_med'] if c.get('cdp_images') else None,
        'page': BM_COLOR_URL.format(number=number),
    }


@pxt.udf
def fetch_image(url: str | None) -> pxt.Image | None:
    """Downloads an image."""
    if url is None:
        return None
    return Image.open(io.BytesIO(_get(url))).convert('RGB')


@pxt.udf
def paint_chip(name: str, number: str, hex_code: str, lrv: float) -> pxt.Image:
    """A paint chip: a block of the official color over a white label with its name, number, and LRV."""
    w, swatch_h, label_h = 600, 600, 170
    chip = Image.new('RGB', (w, swatch_h + label_h), 'white')
    draw = ImageDraw.Draw(chip)
    draw.rectangle([0, 0, w, swatch_h], fill=hex_code)
    big, small = ImageFont.load_default(46), ImageFont.load_default(30)
    draw.text((30, swatch_h + 22), name, fill='#222222', font=big)
    draw.text((30, swatch_h + 86), f'{number}   {hex_code.upper()}   LRV {lrv:.2f}', fill='#555555', font=small)
    draw.rectangle([0, 0, w - 1, swatch_h + label_h - 1], outline='#dddddd', width=2)
    return chip


@pxt.udf
def first_image(response: pxt.Json) -> pxt.Image:
    """The image part of a Gemini response."""
    # Thinking models can return draft images marked as thoughts. The answer is the last image that is not one.
    candidate = response['candidates'][0]
    images = [
        p['inline_data']['data']
        for p in (candidate['content'] or {}).get('parts') or []
        if (p.get('inline_data') or {}).get('data') is not None and not p.get('thought')
    ]
    if not images:
        raise ValueError(f'the model returned no image (finish reason: {candidate.get("finish_reason")})')
    data = images[-1]
    return data if isinstance(data, Image.Image) else Image.open(io.BytesIO(data))
