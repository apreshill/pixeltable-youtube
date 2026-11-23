"""Pydantic's full check, and a demo-only stand-in for an answer with a value the Literal doesn't allow."""

import pixeltable as pxt

from listing import ListingDetails


@pxt.udf
def validate_listing(answer: pxt.Json) -> pxt.Json[ListingDetails]:
    """Run Pydantic's own validation on the answer: required keys, types, and Literal values."""
    return ListingDetails.model_validate(answer).model_dump()


@pxt.udf
def stand_in_model(name: str, answer: pxt.Json) -> pxt.Json:
    """Demo only: Gemini's answer as it is, except on desk-lamp-1, where `condition` becomes 'barely used'.

    In our runs, Gemini's answers kept to the Literal values. This stands in for an answer that doesn't,
    so the notebook can show what each check does with one.
    """
    if name == 'desk-lamp-1':
        return {**answer, 'condition': 'barely used'}
    return answer
