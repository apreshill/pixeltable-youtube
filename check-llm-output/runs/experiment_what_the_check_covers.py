"""Experiment 2 (no model calls): what pxt.Json[ListingDetails] checks, and a UDF that runs model_validate."""

import pixeltable as pxt
import pixeltable.functions as pxtf

from exp_udfs import ListingDetails, validate_listing

GOOD = {'title': 'Lamp', 'category': 'home', 'condition': 'good', 'color': 'Black', 'description': 'd', 'pitch': 'p'}
CASES = {
    'good': GOOD,
    'literal': {**GOOD, 'condition': 'barely used'},
    'extra_key': {**GOOD, 'properties': {}},
    'missing': {k: v for k, v in GOOD.items() if k != 'condition'},
    'wrong_type': {**GOOD, 'color': 3},
}
TEXTS = {
    'fenced': '```json\n{"title": "x"}\n```',
    'trailing_comma': '{"title": "x",\n}',
}

pxt.drop_dir('exp2', force=True, if_not_exists='ignore')
pxt.create_dir('exp2')
t = pxt.create_table('exp2.t', {'case': pxt.String, 'answer': pxt.Json})
t.add_computed_column(checked=t.answer.astype(pxt.Json[ListingDetails]))
t.add_computed_column(validated=validate_listing(t.answer))
print(t.insert([{'case': k, 'answer': v} for k, v in CASES.items()], on_error='ignore'))
print(t.select(t.case, t.checked.errortype, t.checked.errormsg, t.validated.errortype).collect())
for r in t.select(t.case, t.validated.errormsg, t.checked.condition, t.validated.condition).collect():
    print('---', r)
print(t.columns() if hasattr(t, 'columns') else '')
t.describe() if hasattr(t, 'describe') else None

s = pxt.create_table('exp2.s', {'case': pxt.String, 'text': pxt.String})
s.add_computed_column(parsed=pxtf.json.loads(s.text).astype(pxt.Json[ListingDetails]))
print(s.insert([{'case': k, 'text': v} for k, v in TEXTS.items()], on_error='ignore'))
for r in s.select(s.case, s.parsed.errortype, s.parsed.errormsg).collect():
    print('---', r)

# default insert (on_error='abort')
try:
    t.insert([{'case': 'literal2', 'answer': CASES['literal']}])
except Exception as e:
    print(type(e).__name__, str(e)[:600])
