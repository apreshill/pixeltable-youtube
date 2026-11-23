"""Probe: does real Gemini, with app.py's exact config, ever fail the ListingDetails check on the sample photos?"""
from typing import Literal

import pixeltable as pxt
import pixeltable.functions as pxtf
from pydantic import BaseModel, Field, ValidationError

MODEL = 'gemini-3.8-flash'
DETAILS_PROMPT = 'Write a marketplace listing for the item in these photos. Describe only what the photos show.'


class ListingDetails(BaseModel):
    title: str = Field(description='A listing title, under 60 characters')
    category: Literal['cameras', 'bikes', 'home', 'bags', 'instruments', 'other']
    condition: Literal['new', 'like new', 'good', 'fair']
    color: str
    description: str = Field(description='Two or three sentences for buyers, about only what the photos show')
    pitch: str = Field(description='Narration for a 10-second listing video: two short spoken sentences, 15 to 25 words')


BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
NAMES = ['desk-lamp-1', 'film-camera-1', 'guitar-1', 'backpack-1', 'cruiser-bike-1', 'salt-lamp-1']

print('pixeltable', pxt.__version__)
pxt.drop_dir('probe', force=True, if_not_exists='ignore')
pxt.create_dir('probe')
t = pxt.create_table('probe.listings', {'name': pxt.String, 'photo': pxt.Image})
t.add_computed_column(response=pxtf.gemini.generate_content(
    [DETAILS_PROMPT, t.photo], model=MODEL,
    config={'response_mime_type': 'application/json', 'response_json_schema': ListingDetails.model_json_schema()}))
t.add_computed_column(details=t.response.parsed.astype(pxt.Json[ListingDetails]))
print(t.insert([{'name': n, 'photo': f'{BASE}{n}.jpg'} for n in NAMES], on_error='ignore'))
rows = t.select(t.name, t.response, t.details.errortype, t.details.errormsg).collect()
for r in rows:
    resp = r['response'] or {}
    usage = resp.get('usage_metadata') or {}
    parsed = resp.get('parsed')
    try:
        ListingDetails.model_validate(parsed)
        pyd = 'ok'
    except ValidationError as e:
        pyd = f'FAILS ({e.error_count()} errors): {str(e)[:200]}'
    print(r['name'], '| pxt check:', r['details_errortype'], '| pydantic:', pyd,
          '| tokens in/out:', usage.get('prompt_token_count'), usage.get('candidates_token_count'), usage.get('thoughts_token_count'))
    print('   ', parsed)
