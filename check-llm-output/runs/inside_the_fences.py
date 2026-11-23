"""After the notebook run: strip each prompt-only answer's Markdown fence and look at what's inside. No model calls."""

import json
import re
import sys

sys.path.insert(0, '..')  # listing.py is in the video folder

import pixeltable as pxt

from listing import ListingDetails

photos = pxt.get_table('llm_output_demo.photos')
for row in photos.select(photos.name, photos.prompt_only_text).order_by(photos.name).collect():
    text = row['prompt_only_text']
    body = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
    keys = re.findall(r'^\s*"([a-z_]+)":', body, flags=re.M)  # top-level keys, in order, repeats included
    print(f"--- {row['name']}: starts with {text[:7]!r}")
    print('    keys in the text:', keys)
    print('    repeated keys:', sorted({k for k in keys if keys.count(k) > 1}) or 'none')
    print('    keys not in ListingDetails:', sorted(set(keys) - set(ListingDetails.model_fields)) or 'none')
    try:
        parsed = json.loads(body)
        ListingDetails.model_validate(parsed)
        print('    without the fence: json.loads and ListingDetails.model_validate pass')
    except Exception as e:
        print(f'    without the fence: {type(e).__name__}: {e}')
