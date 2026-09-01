"""Recipe 1: search the titles that come with each photo.

Titles give us enough text to try keyword search before we add another
retrieval method.

Apply it with:
    pxt schema update recipe1_store.py rag_demo
"""

import pixeltable as pxt

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    """Source photos and their titles."""

    photo_id: pxt.Required[pxt.Int]
    image: pxt.Required[pxt.Image]
    title: pxt.String | None  # a short human title
    search_title = title.lower()
