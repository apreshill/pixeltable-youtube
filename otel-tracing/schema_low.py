"""Videos, and one row per frame with a description from gpt-4o-mini."""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()

PROMPT = 'Describe this video frame in one sentence.'


class Videos(TableModel, name='videos'):
    video: pxt.Video


class Frames(
    TableModel,
    name='frames',
    base=Videos,
    iterator=pxtf.video.frame_iterator(Videos.video, fps=0.5),  # one frame every 2 seconds
):
    response = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': PROMPT},
                    {'type': 'image_url', 'image_url': {'url': frame, 'detail': 'low'}},  # the same frame, at low detail
                ],
            }
        ],
        model='gpt-4o-mini',
    )
    description = response.choices[0].message.content
