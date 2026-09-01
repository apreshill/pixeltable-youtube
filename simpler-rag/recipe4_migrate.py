"""Recipe 4: compare two embedding models on the same photos.

Add the second model without removing the first. Run the same questions against
both models, compare the results, and keep the model that works better.

Review, then apply, with:
    pxt schema diff   recipe4_migrate.py rag_demo
    pxt schema update recipe4_migrate.py rag_demo

To test a hosted provider, replace the second CLIP model with:
    embedding=pxtf.voyageai.multimodal_embed.using(model='voyage-multimodal-3')
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    """The same table, now carrying two image indexes so you can compare models safely."""

    photo_id: pxt.Required[pxt.Int]
    image: pxt.Required[pxt.Image]
    title: pxt.String | None
    search_title = title.lower()

    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )

    # Two embedding indexes on the same column. Adding the second is an additive change:
    # the database backfills it for every existing row, and both stay current on insert.
    __indexes__ = [
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32'),
            name='clip_idx',
        ),
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch16'),
            name='clip_idx_v2',
        ),
    ]
