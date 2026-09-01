"""Recipe 2: add a description for every photo.

Titles leave out most of what a photo shows. A generated caption gives keyword
search more words to match.

Apply it with:
    pxt schema update recipe2_caption.py rag_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    """Source photos, their titles, and a generated caption."""

    photo_id: pxt.Required[pxt.Int]
    image: pxt.Required[pxt.Image]
    title: pxt.String | None
    search_title = title.lower()

    # A computed column: the database runs this model on every image and keeps it current.
    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )
