"""Recipe 4: add an embedding index on the images and search by meaning."""

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

    # CLIP embeds images and text in one space, so a text question can find a photo.
    __indexes__ = [
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32'),
            name='clip_idx',
        ),
    ]
