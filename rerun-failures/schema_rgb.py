"""One row per photo: the photo, its average color, that color's name, and an embedding."""

import pixeltable as pxt

from udfs import average_color, color_name, image_embedding

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    name = pxt.Column(type=pxt.String, primary_key=True)
    image: pxt.Image

    avg_color = average_color(image.convert('RGB'))
    color = color_name(avg_color)

    __indexes__ = [pxt.EmbeddingIndex(image, embedding=image_embedding, name='photo_embedding')]
