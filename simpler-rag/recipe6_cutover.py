"""Recipe 6, cutover: keep the new model and drop the old index."""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id = pxt.Column(type=pxt.Int, primary_key=True)
    image: pxt.Image
    title: pxt.String | None
    hot: pxt.Bool | None

    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )

    __indexes__ = [
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch16'),
            name='clip_idx_v2',
        ),
    ]
