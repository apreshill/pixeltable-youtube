"""Recipe 5a: add a second embedding model next to the first and compare them."""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id: pxt.Int
    image: pxt.Image
    title: pxt.String | None

    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )

    __indexes__ = [
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32'),
            name='clip_idx',
        ),
        # The new model. The old index keeps serving while this one fills.
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch16'),
            name='clip_idx_v2',
        ),
    ]
