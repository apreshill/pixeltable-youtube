# Keep the LLM's Answer When It Fails Validation

This notebook asks an LLM to write a marketplace listing from a photo, in the shape of a Pydantic model. When one field of the answer is wrong, Pydantic's `model_validate` raises a `ValidationError` for the whole model and returns nothing, so the fields that passed are lost too. In Pixeltable, the LLM's whole answer goes in one column and its check against the Pydantic model goes in another. Every row is stored with its error, and the notebook reruns the LLM only for the rows that failed.

It answers two questions from the Pydantic repo. [pydantic #9371](https://github.com/pydantic/pydantic/issues/9371) asks how to keep the fields that passed when one field fails. [Discussion #13811](https://github.com/pydantic/pydantic/discussions/13811) asks how to fall back to a default instead of crashing. In both threads, Pydantic's maintainers suggest a `WrapValidator` on each field that falls back to that field's default. That works per field. What this notebook shows works per row.

The Pydantic model, the prompt, and the photos come from the marketplace app in our Pydantic webinar, [apreshill/pixeltable-marketplace](https://github.com/apreshill/pixeltable-marketplace) (`ListingDetails` and the `response` and `details` columns in `app.py`). Here each row has one photo instead of three.

## Overview

1. **Plain Pydantic.** Gemini's answer for the film camera photo, with `color` changed to a list, fails `ListingDetails.model_validate`. The other five fields were fine, and no `ListingDetails` comes back.
2. **Two columns.** In `listings`, `response` holds the LLM's whole answer, and `details = response.parsed.astype(pxt.Json[ListingDetails])` checks it.
3. **The default insert.** One answer fails the check, so the insert of six photos is refused and stores no rows.
4. **`on_error='ignore'`.** All six rows are stored. The two failed rows have their error in `details.errortype` and `details.errormsg`, `details` is empty on those rows, and `response` still holds each whole answer. This works per row, not per field: Pixeltable doesn't keep a partial `ListingDetails`.
5. **Rerunning the check.** `recompute_columns(listings.details, errors_only=True)` checks the same stored answers again. They fail again, and the LLM isn't called.
6. **Rerunning the LLM call.** `recompute_columns(listings.response, where=listings.details.errortype != None)` calls the LLM again for the two failed rows only, then recomputes `details` for them. `errors_only=True` on `response` finds no rows, because the LLM call itself worked.

### What the check covers

`.astype(pxt.Json[ListingDetails])` checks that each field of the model is in the answer and has the right type. It doesn't run your Pydantic validators, and it doesn't check `Literal` values: a `condition` of `'barely used'` passes (`runs/verify_claims.log`). If you rely on those, call `ListingDetails.model_validate()` on the answer yourself.

For big batches, [Rerun Only the Failures](../rerun-failures/README.md) covers chunked inserts, `pxt errors`, and `errors_only=True` retries on 1,673 photos.

## Technical Architecture

1. **Pixeltable database (`answers_demo`)**
   - `listings`: one row per photo. You insert `name` and `photo`. `response` and `details` are computed columns, so Pixeltable computes them for every row you insert.

2. **Schema files**
   - `schema.py` declares `ListingDetails`, the prompt, and `listings`, with the stand-in as the LLM call.
   - `schema_gemini.py` is the same table, with `pxtf.gemini.generate_content` in place of the stand-in.

3. **The stand-in (`stand_in.py` and `gemini_answers.json`)**
   - This is the demo-only part. On Nov 23, 2026, we sent these six photos to `gemini-3.8-flash` twice, with `ListingDetails` as the response schema. All 12 answers passed the check (`runs/gemini_probe.log`, `runs/gemini_swap.log`). A real failure couldn't be shown without planting one, so the stand-in simulates it.
   - `stand_in_gemini` takes the same arguments as `pxtf.gemini.generate_content` and returns the answers from the first of those runs, from `gemini_answers.json`, under `parsed`. It breaks two of them: the film camera's `color` becomes `['Silver', 'Black']`, and the guitar's answer leaves out `condition`.
   - It tells the photos apart by a hash of their pixels, so it only has answers for these six photos.
   - `CALLS` records every photo it was called for. The notebook clears `BROKEN` before the rerun, so the rerun gets the answers unchanged. With a real LLM, a rerun is a new call, and its answer can come back whole or fail the same way again. The rerun doesn't send the error back to the LLM.

4. **Notebook (`keep-failed-answers.ipynb`)**
   - Resets `answers_demo`, shows the failure in plain Pydantic, applies `schema.py`, inserts the photos both ways, and reruns the failed rows.

The six photos are from the marketplace's samples. The notebook reads them from:

`https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/`

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**

The notebook needs no API key. To call Gemini for real with `schema_gemini.py`, you need a Gemini API key.

This folder is a Pixeltable project root. `keep-failed-answers/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

```bash
cd keep-failed-answers
uv sync
```

That creates `keep-failed-answers/.venv` and installs Pixeltable 0.7.25 or newer, plus `google-genai` for `schema_gemini.py`.

### 3. Register the Kernel

```bash
uv run python -m ipykernel install --user --name keep-failed-answers --display-name keep-failed-answers
```

### 4. Open the Notebook

Run Jupyter from this folder:

```bash
uv run jupyter lab
```

Open `keep-failed-answers.ipynb` and pick the `keep-failed-answers` kernel.

### 5. Run the Notebook

Run it from top to bottom. It takes a few seconds, most of it downloading the six photos. To run it again, restart the kernel first, because the notebook clears the stand-in's `BROKEN` list.

## Expected Output

Plain Pydantic, on the film camera's answer with `color` as a list:

```
1 validation error for ListingDetails
color
  Input should be a valid string [type=string_type, input_value=['Silver', 'Black'], input_type=list]
    For further information visit https://errors.pydantic.dev/2.14/v/string_type
None
```

The default insert prints the check's error and stores no rows:

```
Expected string, got list
0
```

The insert with `on_error='ignore'`:

```
Inserted 6 rows with 2 errors across 1 column (listings.details) in 0.04 s (139.55 rows/s)
```

```
  details_errortype                   details_errormsg
0         TypeError          Expected string, got list
1         TypeError  Missing required key: 'condition'
2               NaN                                NaN
...
```

The failed rows still have each whole answer in `response`, and `details` is `None` on them. `recompute_columns(listings.details, errors_only=True)` returns `2`, the stand-in's `CALLS` stays `[]`, and two rows still fail. `recompute_columns(listings.response, where=failed)` returns `2`, and `CALLS` is `['film-camera-1', 'guitar-1']`. After that, all six rows pass the check.

The full output of our run is in `runs/keep-failed-answers.outputs.txt`, and the executed notebook is `runs/keep-failed-answers.executed.ipynb`.

## Call Gemini for Real

`schema_gemini.py` changes one line of the table: `response` calls `pxtf.gemini.generate_content` instead of the stand-in.

Set `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) in the environment you start from, or put it in `~/.pixeltable/config.toml`:

```toml
[gemini]
api_key = '...'
```

Then, from this folder, create the table in its own directory and run the same steps:

```bash
pxt schema update schema_gemini.py answers_gemini -f
```

```python
import pixeltable as pxt

BASE = 'https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/'
NAMES = ['desk-lamp-1', 'film-camera-1', 'guitar-1', 'backpack-1', 'cruiser-bike-1', 'salt-lamp-1']
listings = pxt.get_table('answers_gemini.listings')
listings.insert([{'name': n, 'photo': f'{BASE}{n}.jpg'} for n in NAMES], on_error='ignore')
failed = listings.details.errortype != None
listings.recompute_columns(listings.response, where=failed)
```

That makes six Gemini calls, one per photo. In our run, each used 1,108 input tokens, 94 to 134 output tokens, and 404 to 617 thinking tokens. All six answers passed the check, so the rerun had no rows to rerun:

```
Inserted 6 rows with 0 errors in 17.52 s (0.34 rows/s)
```

Your answers will differ from ours, and so will the stand-in's, because the stand-in replays our first run.

## File Layout

```
keep-failed-answers/
  README.md
  keep-failed-answers.ipynb
  schema.py
  schema_gemini.py
  stand_in.py
  gemini_answers.json
  notes.md
  runs/
  pyproject.toml
  uv.lock
```

`notes.md` and `runs/` are the production notes and the logs of the runs behind the video. The local Pixeltable catalog is under `~/.pixeltable`. It is not stored in this repo.

## Troubleshooting

### Schema commands cannot find the project

`cd` into `keep-failed-answers` and run the notebook from there.

### `ModuleNotFoundError: No module named 'stand_in'`

The notebook's working directory isn't this folder. Start Jupyter from `keep-failed-answers`.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from this folder, register the kernel as above, then pick `keep-failed-answers`.

### The insert shows no errors on a second run

The notebook clears the stand-in's `BROKEN` list before the rerun, and the list stays empty until the kernel restarts. Restart the kernel and run from the top. The reset cell drops `answers_demo`.

### `The stand-in has answers only for the six photos in the notebook`

The stand-in only has answers for the six photos in `NAMES`. For other photos, use `schema_gemini.py`.

### Twelve rows instead of six

The `on_error='ignore'` insert ran twice. Run the notebook from the top. The reset cell drops `answers_demo`.
