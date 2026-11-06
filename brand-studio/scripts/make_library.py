"""Make the library photos for the two invented brands, once.

Maintainer script. The photos are committed under brand_kits/<brand>/library/, so people running the
tutorial never need to run this. A real brand would load its own photography into the library table.

Each photo is a row in maintainer.library_shoots, so a photo is made once and kept, and Pixeltable
retries the provider on its own. It calls the paid Gemini API, so it stops unless you pass --spend.

    uv run python scripts/make_library.py --spend
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if '--spend' not in sys.argv:
    sys.exit(__doc__)

import pixeltable as pxt  # noqa: E402
import pixeltable.functions as pxtf  # noqa: E402

import udfs  # noqa: E402
from sample_data import KITS, LIBRARY  # noqa: E402

pxt.create_dir('maintainer', if_exists='ignore')
shoots = pxt.create_table(
    'maintainer.library_shoots', {'brand': pxt.String, 'file': pxt.String, 'prompt': pxt.String}, if_exists='ignore'
)
shoots.add_computed_column(
    image=udfs.first_image(
        pxtf.gemini.generate_content(
            shoots.prompt,
            model='gemini-3-pro-image',
            config={'response_modalities': ['IMAGE'], 'image_config': {'aspect_ratio': '4:5', 'image_size': '1K'}},
        )
    ),
    if_exists='ignore',
)

have = {r['file'] for r in shoots.select(shoots.file).collect()}
new = [{'brand': r['brand'], 'file': r['file'], 'prompt': r['prompt']} for r in LIBRARY if r['file'] not in have]
if new:
    shoots.insert(new, on_error='ignore')

for r in shoots.select(shoots.brand, shoots.file, shoots.image).collect():
    out = KITS / r['brand'] / 'library' / r['file']
    if r['image'] is not None and not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        r['image'].convert('RGB').save(out, quality=88)
        print(f'wrote {out}')
