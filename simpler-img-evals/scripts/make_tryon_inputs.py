"""Generate the virtual try-on reference images with Pixeltable.

The try-on edit itself is produced by the edits table in schema.py. This script
only makes the two input references, person.png and garment.png, so they are
model-generated and carry clean provenance instead of coming from an unknown
stock source.

It declares a small class-based table whose image is computed by the built-in
pxtf.openai.image_generations, the same function the generations table uses, then
saves the two images under use_cases/virtual_try_on/assets/.

The AssetGen model is registered to its own pxt.model_base(), so create_all only
manages the asset_gen table. It does not touch the schema.py tables.

Needs OPENAI_API_KEY.

Usage:
    python scripts/make_tryon_inputs.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import udfs  # noqa: F401  # register the UDFs before touching tables
import pixeltable as pxt
import pixeltable.functions as pxtf

ASSETS = ROOT / 'use_cases' / 'virtual_try_on' / 'assets'
GEN_MODEL = 'gpt-image-1.5'
GEN_SIZE = '1024x1536'

PROMPTS = {
    'person': (
        'Full-body studio photograph of one fashion model standing and facing the '
        'camera, neutral expression, arms relaxed at the sides, wearing a plain '
        'fitted tank top and jeans, plain light gray seamless background, soft even '
        'studio lighting, sharp focus.'
    ),
    'garment': (
        'Product flat-lay photograph of a single jacket on a plain white background, '
        'front view, no person and no mannequin, centered, even lighting, '
        'e-commerce catalog style.'
    ),
}

TableModel = pxt.model_base()


class AssetGen(TableModel, name='asset_gen'):
    """Prompt in, generated image out, using the built-in OpenAI function."""

    name: pxt.Required[pxt.String]
    gen_prompt: pxt.Required[pxt.String]

    image = pxtf.openai.image_generations(
        gen_prompt, model=GEN_MODEL, model_kwargs={'size': GEN_SIZE}
    )['data'][0]


def _make_table() -> pxt.Table:
    """Create the class-based asset_gen table fresh each run."""
    pxt.drop_table('img_eval/asset_gen', force=True, if_not_exists='ignore')
    TableModel.create_all(catalog_dir='img_eval')
    return pxt.get_table('img_eval/asset_gen')


def main() -> None:
    gen = _make_table()
    gen.insert([{'name': name, 'gen_prompt': prompt} for name, prompt in PROMPTS.items()])

    ASSETS.mkdir(parents=True, exist_ok=True)
    for name in PROMPTS:
        img = gen.where(gen.name == name).select(gen.image).collect()[0]['image']
        dest = ASSETS / f'{name}.png'
        img.save(dest)
        print(f'wrote {dest}')

    print('done. the try-on references are now model-generated.')


if __name__ == '__main__':
    main()
