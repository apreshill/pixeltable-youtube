# Trace Each LLM Answer Back to Its Media File

This notebook sends marketplace photos to Gemini and keeps each answer on the same row as the photo it read, the listing ID, and the seller. A `where` on an answer gives back the photo and the URL it came from. Then it sends Pixeltable's traces to Logfire, where each Gemini call on each row is its own span, named by the column it filled.

It takes up a question from Pydantic AI's issues: once your images are bytes in a message, how do you tell which one came from where? In [pydantic-ai #2139](https://github.com/pydantic/pydantic-ai/issues/2139), a tool couldn't tell which image to act on, because there wasn't a good way to tag `BinaryContent` with where it came from. Pydantic AI added an `identifier` to `BinaryContent`, which by default is a short hash of its bytes, and [#2635](https://github.com/pydantic/pydantic-ai/issues/2635) asked for one on URLs too, because a presigned URL changes each time you make one. Both are in Pydantic AI today. In [#2243](https://github.com/pydantic/pydantic-ai/issues/2243), the developer's workaround for referencing data across agents was to "store the data in a database and reference it by id." Keeping track of which listing each photo belongs to, and what the model said about it, is still up to your code.

For more on tracing Pixeltable, including Phoenix and how the span levels differ, see [Trace a Video Insert with OpenTelemetry](../otel-tracing/README.md).

## Overview

1. One free line of Pydantic AI shows a photo the way it goes into a message: `BinaryContent(...)`, whose `identifier` is a six-character hash of the bytes. You can pass your own string instead.
2. `schema.py` declares `listings`. You insert `listing_id`, `seller`, and `photo`. Pixeltable computes `response`, Gemini's answer about the photo, and `details`, that answer typed as the Pydantic model `ListingDetails`.
3. Four listings go in with one insert. Reading them back shows each answer next to its photo.
4. `where(listings.details.category == 'home')` finds the lamps, and `photo.fileurl` gives back the URL each photo came from.
5. `logfire.configure()` and `PixeltableInstrumentor().instrument(span_level='debug')` send Pixeltable's spans to Logfire. Two more listings go in, one insert each. Each insert is one trace, with a `pixeltable.media.fetch` span that names the photo's URL (`pxt.url`) and a `pixeltable.udf.generate_content` span that names the column it filled (`pxt.column`).

## Technical Architecture

1. **Pixeltable database (`trace_demo`)**
   - `listings`: one row per listing. You insert `listing_id` (the primary key), `seller`, and `photo`. Pixeltable computes `response` and `details` on every insert.

2. **Schema file**
   - `schema.py` holds `ListingDetails`, the prompt, and the `listings` table. `response` calls `pxtf.gemini.generate_content([PROMPT, photo], model='gemini-3.8-flash', ...)` with `ListingDetails.model_json_schema()` as the response schema. `details = response.parsed.astype(pxt.Json[ListingDetails])`.

3. **Notebook (`trace-answers-to-media.ipynb`)**
   - Shows a photo as Pydantic AI's `BinaryContent`, resets `trace_demo`, applies `schema.py`, inserts and reads the listings, turns on Logfire, inserts two more listings, and prints their spans.

4. **Logfire**
   - `logfire.configure()` reads `LOGFIRE_TOKEN` and sets up the exporter to your Logfire project. `PixeltableInstrumentor().instrument()` sends Pixeltable's spans through it. At `span_level='debug'`, each model call on each row gets its own `pixeltable.udf.<name>` span.
   - The notebook also passes an `InMemorySpanExporter` to `logfire.configure()`, so it can print the spans. That's only for the video. Leave it out in your own code.

The photos are the marketplace app's sample photos. The notebook reads them from:

`https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/`

The `photo` column holds each URL as you inserted it, and `photo.fileurl` returns it. Pixeltable downloads each photo into its file cache under `~/.pixeltable` when a computed column needs it.

### What goes to Logfire

Pixeltable's spans record what ran and how long it took: the operation, the table ID, the column, the UDF, and the URL of each media file it downloads. Each Gemini span also has a `pixeltable.udf.tokens` event with the call's input and output token counts and the model name. The spans don't carry the photo or Gemini's answer. Nothing in this notebook instruments the Gemini client itself, so the prompt and the answer stay out of the trace. Gemini's answers stay in your Pixeltable database.

### Which trace goes with which photo

Each listing in the notebook goes in with its own insert, the way an app posts a listing. Then each `pixeltable.insert` trace holds one photo's download and one Gemini call. When you insert several rows at once, you still get one `generate_content` span per call, but they all sit under `pixeltable.store.insert_rows` in one trace, and nothing in the trace says which call read which photo. The row in the table is where each answer stays with its photo.

A photo that Pixeltable doesn't download, such as a local file or an upload, gets no `pixeltable.media.fetch` span, so its trace has no URL. A downloaded photo's `pxt.url` has its query string and any credentials removed, so a presigned URL shows up without its signature, and it won't match the full URL in `photo.fileurl`.

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**
- **A Gemini API key**
- **A Logfire write token**, from a project at [logfire.pydantic.dev](https://logfire.pydantic.dev). Without one, the notebook still runs, and the spans only print in the notebook.

The notebook makes 6 calls to `gemini-3.8-flash`, one per photo. In our runs, each call used about 1,100 input tokens, about 100 output tokens, and 380 to 510 thinking tokens.

This folder is a Pixeltable project root. `trace-answers-to-media/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

```bash
cd trace-answers-to-media
uv sync
```

That installs Pixeltable 0.7.25 or newer with its `otel` extra (`opentelemetry-instrumentation-pixeltable` and the OpenTelemetry SDK), plus `google-genai`, `logfire`, and `pydantic-ai-slim`.

### 3. Register the Kernel

```bash
uv run python -m ipykernel install --user --name trace-answers-to-media --display-name trace-answers-to-media
```

### 4. Set Your Keys

Set both in the shell you start Jupyter from:

```bash
export GEMINI_API_KEY=<your Gemini API key>
export LOGFIRE_TOKEN=<your Logfire write token>
```

You can put the Gemini key in `~/.pixeltable/config.toml` instead:

```toml
[gemini]
api_key = '...'
```

`logfire.configure()` works out your Logfire region from the token, so the same code works for US and EU projects.

### 5. Open the Notebook

Run Jupyter from this folder:

```bash
uv run jupyter lab
```

Open `trace-answers-to-media.ipynb`, pick the `trace-answers-to-media` kernel, and run it from top to bottom. The first insert takes about 15 seconds, and each of the two traced inserts takes about 5 to 11 seconds. Spans reach Logfire in batches, a few seconds after each cell finishes.

## Expected Output

### The `BinaryContent` identifier

```
'ec44bc'
```

### The first insert

```
Inserted 4 rows with 0 errors in 14.52 s (0.28 rows/s)
```

Reading the listings back shows each photo next to its answer. Gemini's titles change a little from run to run. In one run:

```
   listing_id seller  photo                                            details_title details_condition
0         101    lee  [img]  Vintage Style Brown Leather Backpack with Front Pockets          like new
1         102   omar  [img]        Vintage Brass Banker's Desk Lamp with Green Shade              good
2         103    eva  [img]                 Vintage Bicycle with Front Wicker Basket              fair
3         104    raj  [img]                           Black Adjustable LED Desk Lamp          like new
```

The `where` on `category == 'home'` returns listings 102 and 104, the two lamps, with their photos and URLs.

### The spans

The two traced inserts print one `pixeltable.media.fetch` span and one `pixeltable.udf.generate_content` span per listing, with a different trace ID for each insert:

```
trace ...a86b3025 pixeltable.media.fetch {'pxt.url': 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/film-camera-1.jpg'} 0.2 s
trace ...a86b3025 pixeltable.udf.generate_content {'pxt.column': 'response'} 7.1 s
trace ...9ee238da pixeltable.media.fetch {'pxt.url': 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/guitar-1.jpg'} 0.3 s
trace ...9ee238da pixeltable.udf.generate_content {'pxt.column': 'response'} 10.3 s
```

The notebook prints the end of each trace ID. Logfire's trace IDs start with a timestamp, so two traces made a minute apart share their first characters.

### In Logfire

Filter to the service `trace-answers-to-media`. Each traced insert is a `pixeltable.insert` trace:

```text
pixeltable.insert
└─ pixeltable.store.insert_rows
   ├─ pixeltable.media.fetch            pxt.url: the photo's URL
   ├─ pixeltable.udf.generate_content   pxt.column: response, and a pixeltable.udf.tokens event
   └─ pixeltable.row
```

The last query in the notebook is traced too, as a `pixeltable.collect` trace with no model call.

## Trace a Service Instead of a Notebook

To trace an app served with `pxt service`, the marketplace app sets Logfire's OTLP endpoint and token in the environment and starts the service with `--otel`. See step 11 of its [README](https://github.com/apreshill/pixeltable-marketplace#11-see-every-step-in-logfire). This notebook doesn't run that path.

Don't set `OTEL_EXPORTER_OTLP_ENDPOINT` in the shell you start this notebook from. When it's set, `logfire.configure()` adds a second exporter for it, and each span reaches Logfire twice.

## File Layout

```
trace-answers-to-media/
  README.md
  trace-answers-to-media.ipynb
  schema.py
  notes.md
  runs/
  pyproject.toml
  uv.lock
```

`notes.md` and `runs/` are the script notes and the real output of the recorded run. The local Pixeltable catalog is under `~/.pixeltable`. It is not stored in this repo.

## Troubleshooting

### No traces show up in Logfire

Check that `LOGFIRE_TOKEN` is set in the shell you started Jupyter from, and that it's a write token. With no token, `send_to_logfire='if-token-present'` sends nothing and says nothing. Restart the kernel after you set it.

### Each span shows up twice in Logfire

Unset `OTEL_EXPORTER_OTLP_ENDPOINT` and restart the kernel. See "Trace a Service Instead of a Notebook".

### The trace has no `pixeltable.udf.generate_content` spans

Pass `span_level='debug'` to `instrument()`. At the default level, `info`, you get the operation and its store spans, but no span per model call.

### `details` holds a category Gemini wasn't asked for

`pxt.Json[ListingDetails]` checks that each field is there and has the right type. It doesn't check `Literal` values, such as `category`. Gemini gets the allowed values in the response schema. If you rely on them, call `ListingDetails.model_validate()` on the answer yourself.

### Schema commands cannot find the project

`cd` into `trace-answers-to-media` and run the notebook from there.

### `Duplicate primary key` on insert

An insert cell ran twice. Run the notebook from the top; its reset cell drops `trace_demo`.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from this folder, register the kernel as above, then pick `trace-answers-to-media`.
