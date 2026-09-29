"""Recipe 1: The MVP. Store the photos and search their titles by keyword."""

import pixeltable as pxt

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id = pxt.Column(type=pxt.Int, primary_key=True)  # inserting the same photo_id twice is an error
    image: pxt.Image
    title: pxt.String | None
