"""Off-camera check: which path each media file takes from a Pixeltable column to Gemini, in Pixeltable 0.7.25.

Logs, for every generate_content call:
- what Pixeltable's _process_media_contents turned each list element into (a PIL image, inline video, or an upload placeholder)
- the media type and byte count the google-genai SDK gave each PIL image (pil_to_blob)
- each Files API upload and delete (watch_files.py), and whether the uploaded media file is still there after the call
- each call's token counts and its price from genai-prices

Run from the media-to-llm folder, with GEMINI_API_KEY set and PIXELTABLE_HOME pointing at a sandbox home:
    uv run python runs/verify_paths.py
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

import google.genai._transformers as transformers
import PIL.Image
import pixeltable as pxt
import pixeltable.functions.gemini as pxt_gemini
from genai_prices import Usage, calc_price

import watch_files  # prints each Files API upload and delete

uploaded_names: list[str] = []
_upload = watch_files.AsyncFiles.upload


async def _upload_and_remember(self, *, file, config=None):
    f = await _upload(self, file=file, config=config)
    uploaded_names.append(f.name)
    return f


watch_files.AsyncFiles.upload = _upload_and_remember


def describe(part):
    if isinstance(part, PIL.Image.Image):
        return f'PIL image {part.format} {part.size} (Pixeltable loaded it from {Path(part.filename).parent.name}/)'
    if isinstance(part, dict) and 'inline_data' in part:
        d = part['inline_data']
        return f'inline_data {d["mime_type"]}, {len(d["data"])} base64 chars'
    if isinstance(part, dict) and pxt_gemini._UPLOAD_PLACEHOLDER_KEY in part:
        return f'Files API upload placeholder {part[pxt_gemini._UPLOAD_PLACEHOLDER_KEY]}'
    if isinstance(part, str):
        return f'text {part!r}'
    return repr(type(part))


_process = pxt_gemini._process_media_contents


def _process_and_log(data, large_video_paths):
    out = _process(data, large_video_paths)
    if isinstance(out, list):  # the top-level contents list; the function also calls itself on each element
        print('generate_content contents:', [describe(p) for p in out])
    return out


pxt_gemini._process_media_contents = _process_and_log

_pil_to_blob = transformers.pil_to_blob


def _pil_to_blob_and_log(image):
    blob = _pil_to_blob(image)
    print(f'google-genai SDK pil_to_blob: {blob.mime_type}, {len(blob.data)} bytes')
    return blob


transformers.pil_to_blob = _pil_to_blob_and_log

print('inline limit for a video, in bytes:', pxt_gemini.GEMINI_INLINE_LIMIT_BYTES * 3 // 4)

pxt.drop_dir('media_verify', force=True, if_not_exists='ignore')
subprocess.run(['pxt', 'schema', 'update', 'schema_video.py', 'media_verify', '-f'], check=True)

PHOTO_BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
VIDEO_BASE = 'https://raw.githubusercontent.com/pixeltable/pixeltable/main/tests/data/'

photos = pxt.get_table('media_verify.photos')
photos.insert([{'name': 'desk-lamp-1.jpg', 'photo': PHOTO_BASE + 'desk-lamp-1.jpg'}])

videos = pxt.get_table('media_verify.videos')
videos.insert(
    [
        {'name': 'bangkok_half_res.mp4', 'video': VIDEO_BASE + 'videos/bangkok_half_res.mp4'},
        {'name': 'bangkok.mp4', 'video': VIDEO_BASE + 'orig_videos/bangkok.mp4'},
    ]
)

client = pxt_gemini._genai_client()
for name in uploaded_names:
    try:
        client.files.get(name=name)
        print(f'{name} is still on the Files API')
    except Exception as e:
        print(f'{name} after the call: {type(e).__name__} {str(e)[:200]}')

for t, col in ((photos, photos.photo), (videos, videos.video)):
    for row in t.select(t.name, size=col.localpath, usage=t.response.usage_metadata).collect():
        u = row['usage']
        out_tokens = (u['candidates_token_count'] or 0) + (u['thoughts_token_count'] or 0)
        price = calc_price(Usage(input_tokens=u['prompt_token_count'], output_tokens=out_tokens), 'gemini-3.8-flash', provider_id='google')
        print(
            f"{row['name']}: {Path(row['size']).stat().st_size} bytes, input {u['prompt_token_count']} "
            f"{[(d['modality'], d['token_count']) for d in u['prompt_tokens_details']]}, output incl. thinking {out_tokens}, "
            f"${price.total_price:.5f}"
        )
