"""The functions the photos table runs on every photo."""

import hashlib

import numpy as np
import pixeltable as pxt

_timed_out: set[str] = set()


def _busy_api(image) -> None:
    """Demo only: time out the first time on about 1 photo in 50, the way a busy model API does."""
    key = hashlib.md5(image.convert('L').tobytes()).hexdigest()
    if int(key, 16) % 50 == 3 and key not in _timed_out:
        _timed_out.add(key)
        raise TimeoutError('model API did not answer within 30 seconds')


@pxt.udf
def average_color(image: pxt.Image) -> str:
    """The photo's average color, as a hex code. Stands in for a model call."""
    _busy_api(image)
    r, g, b = np.asarray(image).mean(axis=(0, 1))
    return f'#{round(r):02x}{round(g):02x}{round(b):02x}'


@pxt.udf
def color_name(hex_code: str) -> str:
    """Red, green, or blue: whichever channel of the hex code is highest."""
    rgb = [int(hex_code[i : i + 2], 16) for i in (1, 3, 5)]
    return ['red', 'green', 'blue'][int(np.argmax(rgb))]
