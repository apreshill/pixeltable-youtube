"""The Pydantic model for what Gemini writes about each photo, and the two ways to ask for it."""

import json
from typing import Literal

from pydantic import BaseModel, Field

MODEL = 'gemini-3.8-flash'


class ListingDetails(BaseModel):
    """What Gemini writes about a seller's photo."""

    title: str = Field(description='A listing title, under 60 characters')
    category: Literal['cameras', 'bikes', 'home', 'bags', 'instruments', 'other']
    condition: Literal['new', 'like new', 'good', 'fair']
    color: str
    description: str = Field(description='Two or three sentences for buyers, about only what the photo shows')
    pitch: str = Field(description='Narration for a 10-second listing video: two short spoken sentences, 15 to 25 words')


PROMPT = 'Write a marketplace listing for the item in this photo. Describe only what the photo shows.'

# The schema only in the prompt.
PROMPT_WITH_SCHEMA = f'{PROMPT} Answer in JSON that matches this schema: {json.dumps(ListingDetails.model_json_schema())}'


def json_config(model: type[BaseModel]) -> dict:
    """The schema in the request: Gemini config that asks for JSON in the shape of `model`."""
    return {'response_mime_type': 'application/json', 'response_json_schema': model.model_json_schema()}
