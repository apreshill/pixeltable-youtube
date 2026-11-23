# Notes: Trace Each LLM Answer Back to Its Media File

The script is `trace-answers-to-media.ipynb`: markdown cells are spoken, code cells are on screen, italic lines are screen cues. The executed copy, with the real output of the last run, is `runs/trace-answers-to-media.executed.ipynb`.

## Promise

By the end, the viewer has seen each Gemini answer on the same row as the photo it read and its listing, gone from an answer back to its photo and URL with a `where`, and seen each Gemini call as its own span in Logfire, named by its column.

Problem 4 from the trailer GIF: "Once my images are just bytes in a message, how do I tell which one came from where?"

## The chain, and where each link is on screen

1. The viewer inserts `listing_id`, `seller`, and `photo` (a URL string). On screen: `sed -n '26,29p' schema.py`, then the insert cell.
2. Pixeltable downloads the photo. On screen: the `pixeltable.media.fetch` span with `pxt.url`, in the spans cell.
3. `response` calls `pxtf.gemini.generate_content([PROMPT, photo], model='gemini-3.8-flash', config=...)`. `PROMPT` is one fixed sentence (`sed -n '9,20p'`), and `photo` is that row's photo column. The config sends `ListingDetails.model_json_schema()`. There are no template variables to fill. On screen: `sed -n '31,36p'`.
4. `details = response.parsed.astype(pxt.Json[ListingDetails])` checks the answer's keys and types, not `Literal` values (said aloud).
5. Out: `select(... photo, details.title, details.condition)`, then `where(details.category == 'home')` with `photo.fileurl`.
6. Tracing: `logfire.configure(...)` plus `PixeltableInstrumentor().instrument(span_level='debug')`. One insert per listing gives one `pixeltable.insert` trace per listing, holding the photo's `pixeltable.media.fetch` span (`pxt.url`) and its `pixeltable.udf.generate_content` span (`pxt.column = 'response'`). On screen: the in-memory copy printed, then Logfire.

## Traces (every claim, and what backs it)

| Claim in the script | Evidence |
|---|---|
| #2139: a tool couldn't tell which image to act on; there wasn't a good way to tag `BinaryContent` with where it came from | pydantic/pydantic-ai#2139 (opened 2025-07-07, closed 2025-07-18): "There isn't a good way to tag BinaryContent with metadata" and "which binary object the tool should act upon" |
| Pydantic AI added an `identifier` for that; #2635 asked for one on URLs because presigned URLs change; both are in Pydantic AI today | #2139 thread (maintainer: "it would be good to have `BinaryContent.identifier`"); #2635 (closed 2025-09-10) cites PR #2231. In pydantic-ai-slim 2.71.0, `BinaryContent(...).identifier` and `ImageUrl(...).identifier` both exist (ran both). |
| By default the identifier is a six-character hash of the bytes; you can pass your own | Ran it: `'ec44bc'`. The constructor takes `identifier: str \| None = None`. |
| Pixeltable is a multimodal backend | `profiles/pixeltable/positioning.md`, Names |
| `photo` is an `Image` column, so the URL you insert is read as an image | run: Gemini read each photo from its URL; `pixeltable.media.fetch` spans |
| `details` checks each field and type before the row is stored, but not `Literal` values | webinar `outline.md` steps 2 and 4; the brief's known limits; reviewer cited `type_system.py` mapping a `Literal` to its common type |
| One paid call per photo; these four take about 15 seconds | runs: 13.62 s, 14.64 s, 14.46 s, 14.52 s |
| `photo.fileurl` gives back the URL we inserted | run output |
| At `debug`, every Gemini call on every row gets its own span | `UdfCallAttrs` docstring in `pixeltable/telemetry_schemas.py` ("per-call `pixeltable.udf.<name>` spans (DEBUG/TRACE)"); run output |
| Each insert is one trace, with the photo's URL and the call's column | run output: two trace IDs, each with one `media.fetch` (`pxt.url`) and one `generate_content` (`pxt.column: 'response'`) |
| In a multi-row insert, the trace doesn't say which call read which photo | `runs/check_batch_spans.log`: two fetches and two `generate_content` spans, all children of `pixeltable.store.insert_rows`; the `pixeltable.row` spans hold neither. Source: `exec/expr_eval/schedulers.py` starts the UDF span under the current span. |
| An uploaded photo has no download span | `runs/check_local_file_spans.log`: a local file gets no `pixeltable.media.*` span; a URL gets `pixeltable.media.fetch`. Source: the span is only in `exec/cache_prefetch_node.py`. |
| The spans reached Logfire | `runs/logfire_export.log` (last run): five `POST /v1/traces` to logfire-us.pydantic.dev, all 200. Not checked in the Logfire UI. |
| The Gemini span's duration is how long Gemini took on that photo | the span wraps one call (`schedulers.py`); not checked in the Logfire UI |

## Changes from the plan

- **Tracing setup.** The plan said `PixeltableInstrumentor().instrument()` with the Logfire OTLP environment variables. `PixeltableInstrumentor` only attaches to a tracer provider that already exists; with the OTLP variables alone, nothing creates one, so nothing is exported. In a notebook, `logfire.configure()` creates it from `LOGFIRE_TOKEN`, which is the webinar outline's "in a script" path (step 8). The `OTEL_EXPORTER_OTLP_*` variables in the marketplace README step 11 are for `pxt service update ... --otel`. Setting them as well would make `logfire.configure()` add a second exporter (logfire 6.0.1, `_internal/config.py` line 1567), so each span would reach Logfire twice. The README says so.
- **One insert per listing in the Logfire part.** In a multi-row insert, the trace has one span per call but doesn't pair calls with photos (checked). One insert per listing, which is how an app posts listings, gives one trace per photo.
- **Seeing the spans.** An `InMemorySpanExporter`, passed to `logfire.configure(additional_span_processors=...)`, keeps a copy of the spans in the notebook. The script says it's demo-only.
- **#2243** is in the README, not the script. Its `e4fcfe` came from a model asked to return image bytes it can't output, so it's a weaker example than it looks.
- **Cut after review:** a step from a span's `pxt.url` back to the row with `where(photo.fileurl == ...)`. It worked here, but `pxt.url` has the query string stripped, so it fails for presigned URLs, and uploads have no download span.
- **`ListingDetails`** is the app's model without `pitch`, with "photo" for "photos" in the description field. The prompt is the app's `DETAILS_PROMPT` for one photo.
- **Pydantic AI** runs only for one free line: `BinaryContent(...).identifier`. No agent and no model call.

## Exemplars pulled (`voice_corpus.py`, era pixeltable)

- Opening with the viewer's pain: yt:0Q5G7T2UWk0:000, yt:iI5En37duSE:000
- Tables live in the database; the column you fill in: yt:92lsL395T6s:008
- Saying what the output shows and what it missed: yt:nbfaL_Vb6SE:006
- Close that walks the parts in order: yt:92lsL395T6s:036, yt:J8kgbKcA9w8:020

Taken for how she moves through a part, not for phrases.

## Checks

- Spoken words: 719 by paragraph (28 paragraphs, median 27, largest 44). Model script: 1,581 words, median 20. At her 194 words a minute, about 3.7 minutes spoken; with the inserts (about 15 s, then 7 to 11 s each) and the Logfire screen, about 6 to 8 minutes.
- Seconds to the promise: 0 (first line). First code on screen (`!uv sync`): about 175 spoken words in, about 55 seconds.
- `measure_voice.py check --register talking`: 1 flag, `i_rate` just under her range (few "I"s). Flags are questions; no words added for it.
- Headings, read in order, tell the video.
- No spoken list of three or more in one line; no line opens with "So" or "And".
- Review (`review-voice`, fresh agent): FAIL on 7 must-fix lines in round 1, all fixed. Round 2: PASS. Its optional note on the closing heading (the trace holds no answer) was taken.

## Gaps

- The Logfire UI beat is checked against the exported span attributes, not the UI. Alison checks it before recording.
- Gemini's titles differ a little from run to run. The script names no titles, only "both lamps", which held in all four runs.

## Gemini calls

31 calls to `gemini-3.8-flash` while building this, each one photo: 3 while exploring, 6 per notebook run (four runs), and 2 per multi-row check (two runs). Each used about 1,108 input tokens (1,089 for the image), 75 to 105 output tokens, and 380 to 510 thinking tokens (`response.usage_metadata` and the `pixeltable.udf.tokens` span event). Neither Pixeltable nor Gemini printed a price.
