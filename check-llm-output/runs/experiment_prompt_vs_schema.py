"""Experiment 1: the same Pydantic model, once only in the prompt, once as Gemini's response schema."""

import json
from typing import Literal

import pixeltable as pxt
import pixeltable.functions as pxtf
from pydantic import BaseModel, Field

MODEL = 'gemini-3.8-flash'
BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
NAMES = ['film-camera-1', 'cruiser-bike-1', 'desk-lamp-1', 'guitar-1', 'backpack-1', 'salt-lamp-1']


class ListingDetails(BaseModel):
    """What Gemini writes from a seller's photos."""

    title: str = Field(description='A listing title, under 60 characters')
    category: Literal['cameras', 'bikes', 'home', 'bags', 'instruments', 'other']
    condition: Literal['new', 'like new', 'good', 'fair']
    color: str
    description: str = Field(description='Two or three sentences for buyers, about only what the photos show')
    pitch: str = Field(description='Narration for a 10-second listing video: two short spoken sentences, 15 to 25 words')


PROMPT = 'Write a marketplace listing for the item in this photo. Describe only what the photo shows.'
PROMPT_WITH_SCHEMA = PROMPT + ' Answer in JSON that matches this schema: ' + json.dumps(ListingDetails.model_json_schema())

pxt.drop_dir('exp', force=True, if_not_exists='ignore')
pxt.create_dir('exp')
t = pxt.create_table('exp.photos', {'name': pxt.String, 'photo': pxt.Image})
t.add_computed_column(prompt_only=pxtf.gemini.generate_content([PROMPT_WITH_SCHEMA, t.photo], model=MODEL))
t.add_computed_column(
    with_schema=pxtf.gemini.generate_content(
        [PROMPT, t.photo],
        model=MODEL,
        config={'response_mime_type': 'application/json', 'response_json_schema': ListingDetails.model_json_schema()},
    )
)
print(t.insert([{'name': n, 'photo': f'{BASE}{n}.jpg'} for n in NAMES], on_error='ignore'))

for r in t.select(t.name, t.prompt_only, t.with_schema).collect():
    print('=' * 30, r['name'])
    po = r['prompt_only']
    ws = r['with_schema']
    print('--- prompt_only parsed:', po['parsed'] if po else None)
    print('--- prompt_only text:')
    print(po['candidates'][0]['content']['parts'][0].get('text') if po else None)
    print('--- prompt_only parts count:', len(po['candidates'][0]['content']['parts']) if po else None)
    print('--- with_schema parsed:', ws['parsed'] if ws else None)
    print('--- with_schema text:')
    print(ws['candidates'][0]['content']['parts'][0].get('text') if ws else None)
    print('--- usage prompt_only:', po.get('usage_metadata') if po else None)
    print('--- usage with_schema:', ws.get('usage_metadata') if ws else None)
print(t.select(t.name, t.prompt_only.errortype, t.prompt_only.errormsg, t.with_schema.errortype).collect())
