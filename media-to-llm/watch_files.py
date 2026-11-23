"""Demo only: print a line each time the google-genai SDK uploads a media file to Gemini's Files API, or deletes one."""

from pathlib import Path

from google.genai.files import AsyncFiles

_upload, _delete = AsyncFiles.upload, AsyncFiles.delete


async def _upload_and_print(self, *, file, config=None):
    uploaded = await _upload(self, file=file, config=config)
    print(f'uploaded a {Path(file).stat().st_size / 2**20:.1f} MiB video to the Files API as {uploaded.name}')
    return uploaded


async def _delete_and_print(self, *, name, config=None):
    deleted = await _delete(self, name=name, config=config)
    print(f'deleted {name} from the Files API')
    return deleted


AsyncFiles.upload, AsyncFiles.delete = _upload_and_print, _delete_and_print
