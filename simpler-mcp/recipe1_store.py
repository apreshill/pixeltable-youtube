"""Recipe 1: search photo titles and generated captions.

Apply it with:
    pxt schema diff recipe1_store.py mcp_demo
    pxt schema update recipe1_store.py mcp_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    """Photos that people can search through the MCP."""

    photo_id: pxt.Required[pxt.Int]
    image: pxt.Required[pxt.Image]
    title: pxt.String | None

    search_title = title.lower()
    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )


class Queries(TableModel, name='queries'):
    """Questions and images sent to the MCP search tools."""

    query_id: pxt.Required[pxt.String]
    tool: pxt.Required[pxt.String]
    text: pxt.String | None
    image: pxt.Image | None
    created_at: pxt.Required[pxt.Timestamp]
