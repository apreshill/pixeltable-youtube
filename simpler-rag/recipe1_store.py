"""Recipe 1: store the photos and search their titles."""

import pixeltable as pxt

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id: pxt.Int
    image: pxt.Image
    title: pxt.String | None
