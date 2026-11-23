"""Demo only: a stand-in for pxtf.gemini.generate_content, so the failed answers are the same on every run.

It returns the answers gemini-3.8-flash gave for these six photos in our run (gemini_answers.json), so it needs
no API key and costs nothing. It breaks one field in two of those answers. schema_gemini.py calls Gemini instead.
"""

import hashlib
import json
from pathlib import Path

import pixeltable as pxt

ANSWERS = json.loads(Path(__file__).with_name('gemini_answers.json').read_text())
NAMES = {photo['md5']: name for name, photo in ANSWERS.items()}


def photo_name(photo) -> str:
    """Which of the six photos this is, from a hash of its pixels."""
    name = NAMES.get(hashlib.md5(photo.tobytes()).hexdigest())
    if name is None:
        raise ValueError('The stand-in has answers only for the six photos in the notebook. Use schema_gemini.py.')
    return name


BROKEN = ['film-camera-1', 'guitar-1']  # the stand-in breaks the answers for these photos
CALLS: list[str] = []  # every photo the stand-in was called for, in order


@pxt.udf
def stand_in_gemini(contents: pxt.Json, *, model: str, config: dict | None = None) -> dict:
    """Takes the same arguments as pxtf.gemini.generate_content, and returns Gemini's answer as `parsed`."""
    prompt, photo = contents
    name = photo_name(photo)
    CALLS.append(name)
    answer = dict(ANSWERS[name]['answer'])
    if name in BROKEN:
        if name == 'film-camera-1':
            answer['color'] = ['Silver', 'Black']  # a list, not a string
        if name == 'guitar-1':
            del answer['condition']  # a required field, left out
    return {'parsed': answer}
