"""One row per photo: the LLM's answer about the item in it, and that answer checked against ListingDetails."""

from typing import Literal

import pixeltable as pxt
from pydantic import BaseModel, Field

from stand_in import stand_in_gemini

MODEL = 'gemini-3.8-flash'
DETAILS_PROMPT = 'Write a marketplace listing for the item in these photos. Describe only what the photos show.'


class ListingDetails(BaseModel):
    """What the LLM writes from a seller's photo."""

    title: str = Field(description='A listing title, under 60 characters')
    category: Literal['cameras', 'bikes', 'home', 'bags', 'instruments', 'other']
    condition: Literal['new', 'like new', 'good', 'fair']
    color: str
    description: str = Field(description='Two or three sentences for buyers, about only what the photos show')
    pitch: str = Field(description='Narration for a 10-second listing video: two short spoken sentences, 15 to 25 words')


def json_config(model: type[BaseModel]) -> dict:
    """Gemini config that asks for JSON in the shape of `model`."""
    return {'response_mime_type': 'application/json', 'response_json_schema': model.model_json_schema()}


TableModel = pxt.model_base()


class Listings(TableModel, name='listings'):
    name: pxt.String
    photo: pxt.Image

    # The LLM's whole answer, as it came back. The stand-in is demo only.
    response = stand_in_gemini([DETAILS_PROMPT, photo], model=MODEL, config=json_config(ListingDetails))
    # The answer checked against ListingDetails. A missing field or a wrong type is an error on this row.
    details = response.parsed.astype(pxt.Json[ListingDetails])
