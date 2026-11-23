"""One row per photo, with Gemini's answer about it asked for two ways, and each answer's check."""

import pixeltable as pxt
import pixeltable.functions as pxtf

from listing import MODEL, PROMPT, PROMPT_WITH_SCHEMA, ListingDetails, json_config
from udfs import stand_in_model, validate_listing

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    name = pxt.Column(type=pxt.String, primary_key=True)
    photo: pxt.Image

    # 1. The schema only in the prompt
    prompt_only = pxtf.gemini.generate_content([PROMPT_WITH_SCHEMA, photo], model=MODEL)
    prompt_only_text = prompt_only.candidates[0].content.parts[0].text.astype(pxt.String)
    prompt_only_details = pxtf.json.loads(prompt_only_text).astype(pxt.Json[ListingDetails])

    # 2. The schema in the request
    response = pxtf.gemini.generate_content([PROMPT, photo], model=MODEL, config=json_config(ListingDetails))
    details = response.parsed.astype(pxt.Json[ListingDetails])

    # 3. Demo only: the stand-in's answer, checked two ways
    stand_in_answer = stand_in_model(name, response.parsed)
    stand_in_details = stand_in_answer.astype(pxt.Json[ListingDetails])  # keys and types
    stand_in_validated = validate_listing(stand_in_answer)  # Pydantic's full validation
