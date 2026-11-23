"""Product photos and videos, each sent to Gemini by passing its column into the call."""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()

MODEL = 'gemini-3.8-flash'
PHOTO_PROMPT = 'Describe the item in this photo in one sentence, for a secondhand listing.'
VIDEO_PROMPT = 'Describe what happens in this video in one sentence.'


class Photos(TableModel, name='photos'):
    name = pxt.Column(type=pxt.String, primary_key=True)
    photo: pxt.Image

    response = pxtf.gemini.generate_content([PHOTO_PROMPT, photo], model=MODEL)
    answer = response.candidates[0].content.parts[0].text.astype(pxt.String)


class Videos(TableModel, name='videos'):
    name = pxt.Column(type=pxt.String, primary_key=True)
    video: pxt.Video

    response = pxtf.gemini.generate_content([VIDEO_PROMPT, video], model=MODEL)
    answer = response.candidates[0].content.parts[0].text.astype(pxt.String)
