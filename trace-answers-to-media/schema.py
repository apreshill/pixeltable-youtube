"""One row per listing: its ID, its seller, its photo, and Gemini's answer about the photo."""

from typing import Literal

import pixeltable as pxt
import pixeltable.functions as pxtf
from pydantic import BaseModel, Field

MODEL = 'gemini-3.8-flash'
PROMPT = 'Write a marketplace listing for the item in this photo. Describe only what the photo shows.'


class ListingDetails(BaseModel):
    """What Gemini writes from a seller's photo."""

    title: str = Field(description='A listing title, under 60 characters')
    category: Literal['cameras', 'bikes', 'home', 'bags', 'instruments', 'other']
    condition: Literal['new', 'like new', 'good', 'fair']
    color: str
    description: str = Field(description='Two or three sentences for buyers, about only what the photo shows')


TableModel = pxt.model_base()


class Listings(TableModel, name='listings'):
    listing_id = pxt.Column(type=pxt.Int, primary_key=True)
    seller: pxt.String
    photo: pxt.Image

    response = pxtf.gemini.generate_content(
        [PROMPT, photo],
        model=MODEL,
        config={'response_mime_type': 'application/json', 'response_json_schema': ListingDetails.model_json_schema()},
    )
    details = response.parsed.astype(pxt.Json[ListingDetails])
