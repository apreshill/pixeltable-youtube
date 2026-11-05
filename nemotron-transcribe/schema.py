"""One recording, one prompt, one transcript.

Apply it with:
    pxt schema diff schema.py nemotron_demo
    pxt schema update schema.py nemotron_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

from udfs import nemotron_transcribe

TableModel = pxt.model_base()


class Recordings(TableModel, name='recordings'):
    """A video, the instruction for how to transcribe it, and the transcript."""

    label: pxt.String
    video: pxt.Video
    prompt: pxt.String

    audio = pxtf.video.extract_audio(video, format='mp3')
    transcript = nemotron_transcribe(audio, prompt)
