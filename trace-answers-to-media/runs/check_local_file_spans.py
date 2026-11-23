"""Run-only check, not part of the video: does a local photo (like an upload) get a pixeltable.media.fetch span?

A throwaway table with no model column, so no paid calls. Spans stay in memory; nothing goes to Logfire.
"""

import sys

import logfire
from opentelemetry.instrumentation.pixeltable import PixeltableInstrumentor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import pixeltable as pxt

local_photo = sys.argv[1]
BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
spans = InMemorySpanExporter()
logfire.configure(service_name='trace-check', send_to_logfire=False, console=False,
                  additional_span_processors=[SimpleSpanProcessor(spans)])
PixeltableInstrumentor().instrument(span_level='debug')

pxt.drop_table('trace_demo.local_check', if_not_exists='ignore')
t = pxt.create_table('trace_demo.local_check', {'photo': pxt.Image})
t.add_computed_column(width=t.photo.width)
for photo in (local_photo, BASE + 'salt-lamp-1.jpg'):
    spans.clear()
    t.insert([{'photo': photo}])
    names = [s.name for s in spans.get_finished_spans() if s.name.startswith('pixeltable.media')]
    print(photo.rsplit('/', 1)[-1], '->', names)
pxt.drop_table('trace_demo.local_check')
