#!/usr/bin/env bash
# Does `pxt schema update schema_validate.py` call Gemini again for the rows already stored?
# Insert one photo with the key set, stop the daemon, then apply schema_validate.py with no Gemini key.
# If the update needed a model call, it would fail. Run from the video folder, in a sandbox Pixeltable home.
set -euo pipefail
BASE=https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/
uv run python -c "import pixeltable as pxt; pxt.drop_dir('verify_demo', force=True, if_not_exists='ignore')"
uv run pxt schema update schema.py verify_demo -f
uv run python -c "
import pixeltable as pxt
photos = pxt.get_table('verify_demo.photos')
print(photos.insert([{'name': 'guitar-1', 'photo': '${BASE}guitar-1.jpg'}], on_error='ignore'))
"
uv run pxt daemon stop || true
env -u GEMINI_API_KEY -u GOOGLE_API_KEY bash -c '
  if [ -z "${GEMINI_API_KEY:-}" ]; then echo "GEMINI_API_KEY is unset for the update"; else echo "GEMINI_API_KEY is set"; fi
  uv run pxt schema update schema_validate.py verify_demo -f
  uv run python -c "
import pixeltable as pxt
photos = pxt.get_table(\"verify_demo.photos\")
print(photos.select(photos.name, photos.stand_in_details.condition, photos.stand_in_validated.condition, photos.stand_in_validated.errortype).collect())
"
  uv run pxt history verify_demo/photos
'
uv run pxt daemon stop || true
