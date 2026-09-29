"""Recipe 5: Hot/cold tiers. A view of the hot photos gets its own index, with the newer model."""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id = pxt.Column(type=pxt.Int, primary_key=True)
    image: pxt.Image
    title: pxt.String | None
    hot: pxt.Bool | None  # the photos people look at most

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
    ]


# The hot tier is a view. Its rows follow `hot`, and only those rows get the newer model's embedding.
class HotPhotos(TableModel, name='hot_photos', base=Photos.where(Photos.hot == True)):  # noqa: E712
    __indexes__ = [
        pxt.EmbeddingIndex(
            Photos.image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch16'),
            name='hot_idx',
        ),
    ]
