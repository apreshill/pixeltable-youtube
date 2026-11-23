"""Run schema_gemini.py's table with real Gemini calls on the notebook's six photos."""
import pixeltable as pxt

BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
NAMES = ['desk-lamp-1', 'film-camera-1', 'guitar-1', 'backpack-1', 'cruiser-bike-1', 'salt-lamp-1']
listings = pxt.get_table('answers_gemini.listings')
print(listings.insert([{'name': n, 'photo': f'{BASE}{n}.jpg'} for n in NAMES], on_error='ignore'))
print(listings.select(listings.name, listings.details.condition, listings.details.color, listings.details.errortype).collect())
failed = listings.details.errortype != None
print('failed:', listings.where(failed).count())
print('rerun rows:', listings.recompute_columns(listings.response, where=failed).num_rows)
for r in listings.select(listings.name, listings.response.usage_metadata, listings.response.model_version).collect():
    u = r['response_usage_metadata']
    print(r['name'], r['response_model_version'], u['prompt_token_count'], u['candidates_token_count'], u.get('thoughts_token_count'))
