"""Recipe 6: answer a question from the retrieved images.

The question, source notes, retrieved images, and grounded answer stay together
so we can see which evidence the model used.

Apply it with:
    pxt schema update recipe6_answer.py rag_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Answers(TableModel, name='answers'):
    """A question, its retrieved image context, and the grounded answer."""

    question: pxt.Required[pxt.String]
    source_notes: pxt.Required[pxt.String]
    image_1: pxt.Required[pxt.Image]
    image_2: pxt.Required[pxt.Image]
    image_3: pxt.Required[pxt.Image]

    response = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Answer using only the supplied images and source notes. '
                'If they do not contain enough evidence, say so. Cite the photo IDs '
                'that support the answer.',
            },
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'text',
                        'text': 'Question: ' + question + '\n\nSource notes:\n' + source_notes,
                    },
                    {'type': 'image_url', 'image_url': image_1},
                    {'type': 'image_url', 'image_url': image_2},
                    {'type': 'image_url', 'image_url': image_3},
                ],
            },
        ],
        model='gpt-4o-mini',
    )
    answer = response.choices[0].message.content
