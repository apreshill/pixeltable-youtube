"""Make the library photos for the two invented brands.

Maintainer script. The photos are committed under brand_kits/<brand>/library/,
so people running the tutorial never need to run this. A real brand would load
its own photography into the library table instead.

    uv run python scripts/make_library.py
"""

import io
import sys
import time
from pathlib import Path

from google import genai
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sample_data import KITS, LIBRARY  # noqa: E402

MODEL = 'gemini-3-pro-image'


def main() -> None:
    client = genai.Client()
    for row in LIBRARY:
        out = KITS / row['brand'] / 'library' / row['file']
        if out.exists():
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(6):
            try:
                response = client.models.generate_content(
                    model=MODEL,
                    contents=row['prompt'],
                    config={'response_modalities': ['IMAGE'], 'image_config': {'aspect_ratio': '4:5', 'image_size': '1K'}},
                )
                break
            except genai.errors.ServerError:
                time.sleep(10 * (attempt + 1))
        else:
            raise RuntimeError(f'{MODEL} stayed unavailable')
        parts = [p for p in response.candidates[0].content.parts if p.inline_data and not p.thought]
        Image.open(io.BytesIO(parts[-1].inline_data.data)).convert('RGB').save(out, quality=88)
        print(f'wrote {out}')


if __name__ == '__main__':
    main()
