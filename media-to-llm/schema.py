"""Product photos, each sent to Gemini by passing the photo column into the call."""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()

MODEL = 'gemini-3.8-flash'
PHOTO_PROMPT = 'Describe the item in this photo in one sentence, for a secondhand listing.'


class Photos(TableModel, name='photos'):
    name = pxt.Column(type=pxt.String, primary_key=True)
    photo: pxt.Image

    response = pxtf.gemini.generate_content([PHOTO_PROMPT, photo], model=MODEL)
    answer = response.candidates[0].content.parts[0].text.astype(pxt.String)
