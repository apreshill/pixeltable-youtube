# Why the LLM's Answer Keeps Failing Validation

This notebook asks Gemini to describe six marketplace photos with one Pydantic model, `ListingDetails`, in two ways. The first call puts the model's JSON schema only in the prompt. The second call sends the same schema in the request, as Gemini's response schema. Each answer goes in its own column, its check against `ListingDetails` goes in the next column, and both sit on the same row as the photo. When a check fails, the answer stays on the row next to its error.

It answers a question Pydantic developers ask in public: why does the LLM's answer about my image keep failing validation? The source is the Pydantic AI issue [Structured output validation keeps failing](https://github.com/pydantic/pydantic-ai/issues/1192).

Pixeltable doesn't make an LLM return valid output. What the notebook shows is how to see exactly what the LLM returned, and why it failed your Pydantic model, without losing the answer.

## Overview

1. `ListingDetails` is the Pydantic model from the [marketplace app](https://github.com/apreshill/pixeltable-marketplace) for the Pydantic webinar. `category` and `condition` are `Literal` types.
2. `prompt_only` asks for JSON that matches the schema in the prompt text. `prompt_only_details` parses the answer's text with `json.loads` and checks it with `.astype(pxt.Json[ListingDetails])`.
3. `response` sends the same schema as `response_json_schema`, and `details` checks `response.parsed` with `.astype(pxt.Json[ListingDetails])`, the same way the marketplace app does.
4. `errortype` and `errormsg` show which answers failed the check and why, next to the raw answer, on the photo's row.
5. `pxt.Json[ListingDetails]` checks required keys and types, but not `Literal` values. A demo-only stand-in changes one answer's `condition` to `'barely used'`: the `astype` check lets it through, and a UDF that calls `ListingDetails.model_validate` catches it.

What came back in the run saved in `runs/`:

| How the schema was sent | Answers | What came back | Check |
|---|---|---|---|
| Only in the prompt | 6 | JSON wrapped in a Markdown code fence (```` ```json ````) | all 6 failed `json.loads`: `Expecting value: line 1 column 1 (char 0)` |
| In the request, as the response schema | 6 | plain JSON | all 6 passed |

Gemini's answers change from run to run. In each of the six runs we made while building this notebook, every prompt-only answer failed the check, and every answer with the response schema passed. The fence was there every time we looked (30 answers). What was inside the fence varied: in some runs an answer added a key that isn't in `ListingDetails` (`properties`, `required`, or `description_schema`), repeated a key, or ended with a trailing comma.

## Technical Architecture

1. **Pixeltable database (`llm_output_demo`)**
   - `photos`: one row per photo. You insert `name` and `photo`. Every other column is computed on insert.
   - `prompt_only`, `prompt_only_text`, `prompt_only_details`: Gemini's answer with the schema only in the prompt, its text, and the check.
   - `response`, `details`: Gemini's answer with the schema in the request, and the check.
   - `stand_in_answer`, `stand_in_details`, `stand_in_validated` (added by `schema_validate.py`): the stand-in's answer, checked with `astype` and with `model_validate`.

2. **Python files**
   - `listing.py`: `ListingDetails`, the two prompts, and `json_config`, which builds the Gemini config with the response schema.
   - `schema.py`: declares `photos` with both Gemini calls and their checks.
   - `schema_validate.py`: the same table, plus the three stand-in columns.
   - `udfs.py`: `validate_listing`, which runs `ListingDetails.model_validate`, and `stand_in_model`.

3. **Notebook (`check-llm-output.ipynb`)**
   - Resets `llm_output_demo`, applies `schema.py`, inserts five photos, and looks at the failures. Then it applies `schema_validate.py` and inserts a sixth photo.

`stand_in_model` is the demo-only part. In our runs, Gemini's answers kept to the `Literal` values, so the stand-in passes Gemini's answer through unchanged, except on `desk-lamp-1`, where it sets `condition` to `'barely used'`. That shows what each check does with a value the `Literal` doesn't allow. In your own table, use `validate_listing(response.parsed)` where `details` uses `astype`, when your code depends on a `Literal` value.

The photos are the marketplace app's sample photos. The notebook reads them from:

`https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/`

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**
- **A Gemini API key** from Google AI Studio

Each photo gets two calls to `gemini-3.8-flash`, so a full run makes 12 paid calls. In our runs, each call used about 1,100 to 1,400 input tokens (the photo is about 1,100 of them) and about 500 to 850 output tokens, most of them Gemini's thinking.

Set the key before you start Jupyter:

```bash
export GEMINI_API_KEY=...
```

Or put it in `~/.pixeltable/config.toml`:

```toml
[gemini]
api_key = '...'
```

This folder is a Pixeltable project root. `check-llm-output/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

```bash
cd check-llm-output
uv sync
```

That creates `check-llm-output/.venv` and installs Pixeltable 0.7.25 or newer, `google-genai`, and Pydantic.

### 3. Register the Kernel

```bash
uv run python -m ipykernel install --user --name check-llm-output --display-name check-llm-output
```

### 4. Open the Notebook

Run Jupyter from this folder:

```bash
uv run jupyter lab
```

Open `check-llm-output.ipynb` and pick the `check-llm-output` kernel.

### 5. Run the Notebook

Run it from top to bottom. The first insert takes about 20 seconds, for ten Gemini calls. The second insert takes about 15 seconds, for two more.

## Expected Output

The first insert keeps all five rows, with one failed check each:

```
Inserted 5 rows with 5 errors across 1 column (photos.prompt_only_details) in 23.26 s (0.21 rows/s)
```

Every failure is the same error, on the row of its photo:

```
  prompt_only_details_errortype               prompt_only_details_errormsg
0               JSONDecodeError  Expecting value: line 1 column 1 (char 0)
```

The raw answer next to it shows why. Each one starts with a Markdown fence:

````
```json
{
  "title": "Natural Finish 6-String Acoustic Guitar",
  "category": "instruments",
  ...
}
```
````

The answers to the call with the response schema are plain JSON, starting with `{`, and `details` has no errors.

After `schema_validate.py` and the desk lamp insert, `'barely used'` passes the `astype` check, and `validate_listing` fails with Pydantic's message:

```
             name    condition details_error  validated_error
2     desk-lamp-1  barely used          None  ValidationError

1 validation error for ListingDetails
condition
  Input should be 'new', 'like new', 'good' or 'fair' [type=literal_error, input_value='barely used', input_type=str]
```

Your answers will be worded differently, and the keys inside the fences can differ. `runs/notebook-output.txt` has the full output of our run.

## File Layout

```
check-llm-output/
  README.md
  check-llm-output.ipynb
  listing.py
  schema.py
  schema_validate.py
  udfs.py
  pyproject.toml
  uv.lock
  notes.md
  runs/
```

`runs/` holds the executed notebook, its output as text, and the scripts and logs of the experiments behind the notebook's claims. The local Pixeltable catalog is under `~/.pixeltable`. It is not stored in this repo.

## Troubleshooting

### Schema commands cannot find the project

`cd` into `check-llm-output` and run the notebook from there.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from this folder, register the kernel as above, then pick `check-llm-output`.

### Every Gemini call fails with a missing key

Set `GEMINI_API_KEY` in the shell that starts Jupyter, or put the key in `~/.pixeltable/config.toml`, then restart the kernel.

### `response.parsed` is empty

Gemini's SDK fills in `parsed` only when the request includes a response schema. That's why `prompt_only_details` reads the answer's text instead.

### `pxt schema update schema_validate.py` refuses the update

An update that adds a computed column computes it for the rows already in the table, and it refuses the whole update if any row fails. The notebook inserts the desk lamp after the update for that reason. If you change `stand_in_model` to alter a photo that's already in the table, `stand_in_validated` fails on that row and the update is refused.

### A UDF that returns a Pydantic model fails on insert

In Pixeltable 0.7.25, a UDF annotated `-> ListingDetails` that returns the model instance fails when the row is stored, with `TypeError: Object of type ListingDetails is not JSON serializable`, even with `on_error='ignore'`. Return a dict instead: `ListingDetails.model_validate(answer).model_dump()`, as `validate_listing` does.

### Duplicate primary key on insert

A row with that `name` is already in the table. Run the notebook from the top; its reset cell drops `llm_output_demo`.
