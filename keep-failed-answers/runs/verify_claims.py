"""Claims the script makes beyond the notebook's own cells (pixeltable 0.7.25, stand-in, no API calls)."""
import pixeltable as pxt

import stand_in
from schema import ListingDetails

BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
NAMES = ['desk-lamp-1', 'film-camera-1', 'guitar-1', 'backpack-1', 'cruiser-bike-1', 'salt-lamp-1']
rows = [{'name': n, 'photo': f'{BASE}{n}.jpg'} for n in NAMES]
listings = pxt.get_table('verify.listings')

print('1. default insert: how many model calls happen before the insert is refused?')
stand_in.CALLS.clear()
try:
    listings.insert(rows)
except pxt.Error as e:
    print('   refused:', str(e).splitlines()[1])
print('   calls:', stand_in.CALLS, '| rows stored:', listings.count())

print("2. on_error='ignore', then errors_only=True on response (the call worked, so no rows?)")
listings.insert(rows, on_error='ignore')
failed = listings.details.errortype != None
stand_in.CALLS.clear()
print('   rows rerun:', listings.recompute_columns(listings.response, errors_only=True).num_rows,
      '| calls:', stand_in.CALLS, '| still failed:', listings.where(failed).count())

print("3. does the check pass a condition that isn't one of the Literal values?")
lit = pxt.create_table('verify.literal', {'answer': pxt.Json})
lit.add_computed_column(details=lit.answer.astype(pxt.Json[ListingDetails]))
good = dict(stand_in.ANSWERS['salt-lamp-1']['answer'])
lit.insert([{'answer': {**good, 'condition': 'barely used'}}], on_error='ignore')
print('   ', lit.select(lit.details.condition, lit.details.errortype).collect())
