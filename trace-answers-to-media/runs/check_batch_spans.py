"""Run-only check, not part of the video: what one insert of two listings looks like as spans.

Does a batch insert still give one span per Gemini call, and does any span tie a call to its photo?
Uses the sandbox table the notebook built. Spans stay in memory; nothing goes to Logfire.
"""

import logfire
from opentelemetry.instrumentation.pixeltable import PixeltableInstrumentor
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import pixeltable as pxt

BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
spans = InMemorySpanExporter()
logfire.configure(service_name='trace-check', send_to_logfire=False, console=False,
                  additional_span_processors=[SimpleSpanProcessor(spans)])
PixeltableInstrumentor().instrument(span_level='debug')

listings = pxt.get_table('trace_demo.listings')
print(listings.insert([
    {'listing_id': 107, 'seller': 'sam', 'photo': BASE + 'road-bike-1.jpg'},
    {'listing_id': 108, 'seller': 'ana', 'photo': BASE + 'table-lamp-1.jpg'},
]))

finished = spans.get_finished_spans()
by_id = {s.context.span_id: s for s in finished}
print('traces in this insert:', len({s.context.trace_id for s in finished}))
for s in finished:
    if s.name in ('pixeltable.media.fetch', 'pixeltable.udf.generate_content', 'pixeltable.row'):
        parent = by_id.get(s.parent.span_id).name if s.parent and s.parent.span_id in by_id else None
        attrs = {k: v for k, v in s.attributes.items() if k in ('pxt.url', 'pxt.column', 'pxt.batch_size')}
        print(f'{s.context.trace_id:032x}', s.name, 'parent:', parent, attrs)
        for e in s.events:
            print('    event', e.name, dict(e.attributes))
