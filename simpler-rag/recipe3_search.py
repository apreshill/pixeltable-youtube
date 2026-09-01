"""Recipe 3: add an embedding index and search by meaning.

Keyword search misses questions that use different words. An embedding index lets
us compare the meaning of a question with what each photo shows. Each photo is one
item, so there is nothing to split into chunks.

Apply it with:
    pxt schema update recipe3_search.py rag_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    """Source photos, a generated caption, and an embedding index over the image."""

    photo_id: pxt.Required[pxt.Int]
    image: pxt.Required[pxt.Image]
    title: pxt.String | None
    search_title = title.lower()

    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )

    # An embedding index over the image column. CLIP maps images and text into the same
    # space, so a text query can retrieve photos. The database backfills and maintains it.
    __indexes__ = [
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32'),
            name='clip_idx',
        )
    ]
