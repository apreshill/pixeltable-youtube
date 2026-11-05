"""One row per photo: the photo, its average color, and that color's name."""

import pixeltable as pxt

from udfs import average_color, color_name

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    name = pxt.Column(type=pxt.String, primary_key=True)
    image: pxt.Image

    avg_color = average_color(image.convert('RGB'))
    color = color_name(avg_color)
