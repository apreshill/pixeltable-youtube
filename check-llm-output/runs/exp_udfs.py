from typing import Literal

import pixeltable as pxt
from pydantic import BaseModel, Field


class ListingDetails(BaseModel):
    title: str = Field(description='A listing title, under 60 characters')
    category: Literal['cameras', 'bikes', 'home', 'bags', 'instruments', 'other']
    condition: Literal['new', 'like new', 'good', 'fair']
    color: str
    description: str
    pitch: str


@pxt.udf
def validate_listing(answer: pxt.Json) -> pxt.Json[ListingDetails]:
    return ListingDetails.model_validate(answer).model_dump()
