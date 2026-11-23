# Notes: Why the LLM's Answer Keeps Failing Validation

This is the script for problem 2 of the Pydantic webinar series, "/getting valid output back": "Why does the LLM's answer about my image keep failing validation?" The notebook is the script. Its markdown cells are the spoken beats, and its code cells are what's on screen.

## Promise

By the end, the viewer has seen why Gemini's answers about the photos failed the Pydantic model. With the schema only in the prompt, every answer came back in a Markdown code fence. Sending the schema in the request fixed that in our runs. Each failed answer stays on its photo's row, next to the error that explains it. The viewer also learns the check's limit: `pxt.Json[Model]` doesn't check `Literal` values. A UDF that runs Pydantic's full validation catches them.

What the video doesn't promise: Pixeltable doesn't make an LLM return valid output, and the close says so.

## The chain, and where each link is on screen

Cell numbers are the indices in `runs/notebook-output.txt`.

1. **What the viewer types.** `name` and a photo URL go into `photos.insert(...)` (cell 17). `photo` is a `pxt.Image` column. The beat says the insert downloads the photo, so Gemini gets the image.
2. **Prompt 1, with the schema only in the prompt.**
   - Cell 7 shows how it's built (`listing.py` lines 22 to 25) and then prints the whole prompt.
   - The call is in `schema.py` (cell 11, lines 6 to 22): `[PROMPT_WITH_SCHEMA, photo]` with `MODEL`.
   - `MODEL` is shown as `gemini-3.8-flash` in cell 5.
3. **The first answer and its check.**
   - `prompt_only` holds the whole answer, and `prompt_only_text` holds its text.
   - `prompt_only_details` runs `pxtf.json.loads`, then `.astype(pxt.Json[ListingDetails])`.
4. **Prompt 2, with the schema in the request.**
   - The prompt is `PROMPT`, the first line shown in cell 7.
   - `json_config` is in cell 9.
   - `response` and `details = response.parsed.astype(...)` are in cell 11.
5. **Errors and raw answers.**
   - Cell 20 queries `errortype` and `errormsg`.
   - Cell 22 shows the raw prompt-only text.
   - Cell 25 shows the guitar's text from the second call, and cell 27 shows the `details` table.
6. **The stand-in and full validation.**
   - Cells 30 and 32 show `udfs.py`, and cell 34 shows `!diff schema.py schema_validate.py`.
   - Then come the schema diff and update and the desk lamp insert.
   - Cell 40 shows the two checks side by side, and cell 42 shows Pydantic's message.

Not on screen: the advice in the last beat of that part, to use `validate_listing(response.parsed)` in your own table. It's one spoken pointer, and the README shows it.

## Decisions where the plan and the code differed

- **The prompt-only check reads the text, not `parsed`.**
  - google-genai fills `response.parsed` only when the request has `response_schema` or `response_json_schema` (`GenerateContentResponse._from_response`). In our runs, every prompt-only `parsed` was `None`.
  - So `prompt_only.parsed.astype(...)` would fail every row with `Expected non-None value`, which says nothing about the answer.
  - The notebook parses `candidates[0].content.parts[0].text` with `pxtf.json.loads` instead, and a beat says why.
  - The brief's `response.parsed.astype(pxt.Json[Model])` is the check for the second call, as in the marketplace app.
- **The prompt-only run failed for a real reason, so no failure is scripted.** Every prompt-only answer we looked at (30 across six runs) started with a ```` ```json ```` fence, so `json.loads` failed at line 1, column 1. In the final run, the JSON inside each fence would pass (`runs/inside_the_fences.log`).
- **The `Literal` limit needed a stand-in.**
  - In every run, all of Gemini's answers to both calls kept to the `Literal` values.
  - To show a value getting through `astype`, `udfs.stand_in_model` changes `condition` to `'barely used'` on `desk-lamp-1` only.
  - Its docstring, the beat, and the README all say it's demo-only.
- **The desk lamp goes in after `schema_validate.py`.**
  - `pxt schema update` computes a new column for the rows already stored, and it aborts on the first error (`TableVersion.materialize_schema_change` in 0.7.25).
  - So a column that fails on a stored row stops the whole update. `runs/verify_update_refuses_failing_column.log` shows this.
  - Inserting the desk lamp afterward, with `on_error='ignore'`, puts the failure on a row.
- **One photo per row,** not three per listing as in the app, so "the answer about my image" maps to one photo. `ListingDetails` keeps the app's fields. The `description` field's text says "photo" instead of "photos".
- **Five photos, then a sixth.** Each run makes 12 Gemini calls.

## Claims and their evidence

| Claim in the script | Evidence |
|---|---|
| With the schema only in the prompt, all five answers failed validation | `runs/notebook-output.txt`, cells 17 and 20 |
| Every failure is `JSONDecodeError` at line 1, column 1, and every text starts with a fence | cells 20 and 22; `runs/inside_the_fences.log` |
| In this run, the JSON inside each fence would pass the check | `runs/inside_the_fences.log`: with the fence stripped, all six pass `json.loads` and `ListingDetails.model_validate` |
| Gemini's SDK fills in `parsed` only when the request has a schema | google-genai source; `runs/experiment_prompt_vs_schema.log` (`prompt_only parsed: None` on all six) |
| `astype(pxt.Json[ListingDetails])` checks keys and types, not `Literal` values | `runs/experiment_what_the_check_covers.log`; `type_system.py` maps a `Literal` to its common type (`infer_common_literal_type`) |
| Without `on_error='ignore'`, one failed check stops the whole insert, and no rows are saved | `runs/experiment_what_the_check_covers.log` (the default insert raises); the trailer run in pxt-social-ops (`rows stored: 0`) |
| The insert downloads the photo, so Gemini gets the image | `functions/gemini.py` `_process_media_contents` (a PIL image goes inline); `rerun-failures/README.md` says the same about URLs |
| With the schema in the request, every answer passed, and the text starts with a brace | cells 25 and 27 |
| `validate_listing` catches the `Literal` value with Pydantic's message | cells 40 and 42 |
| The schema update computed the new columns from stored answers and didn't call Gemini | `runs/verify_no_gemini_calls.log`: the update succeeds with `GEMINI_API_KEY` unset and the daemon stopped first |
| "a Pydantic AI issue called 'Structured output validation keeps failing'" | https://github.com/pydantic/pydantic-ai/issues/1192. That is its title. The author later traced the problem to JSON mode not being on for their provider. |
| Pixeltable is "a multimodal backend"; "you declare tables as Python classes" | `devrel-skills/profiles/pixeltable/positioning.md`, Names |

## Lines that depend on the run

Gemini's wording changes on every run. If Alison reruns the notebook while recording, check this beat against what's on screen:

- **"In this run, the JSON inside each fence would pass the check."** This was true in the final three runs. In the first experiment, the guitar's answer ended with a trailing comma, which would fail even without the fence. If that happens on camera, cut the sentence or say what's on screen.

These lines held in every run, so they don't need checking: "all five answers failed", "every answer passed", the `JSONDecodeError` at line 1, column 1, and the stand-in results.

Inside the fences, answers often add a key that isn't in `ListingDetails`:
- `properties`: the backpack in the final run, and the salt lamp in two earlier runs
- `description_schema`: the salt lamp in the final run, and the cruiser bike in run 3
- `required`: the desk lamp in run 3

One run had a repeated `description`. The script doesn't mention any of these, because they vary and the review flagged the caveat as too long.

## Runs

All runs used pixeltable 0.7.25 and google-genai 3.6.1, each in a sandbox Pixeltable home.

| Run | What it did | Gemini calls |
|---|---|---|
| Experiment 1 (`runs/experiment_prompt_vs_schema.*`) | six photos, both calls, raw answers and token counts | 12 |
| Experiment 2 (`runs/experiment_what_the_check_covers.*`, `runs/experiment_udf_returns_model_instance.log`) | what `astype` and `model_validate` accept | 0 |
| Notebook runs 1, 2, and 3 | earlier drafts of the notebook | 36 |
| Verify no calls (`runs/verify_no_gemini_calls.*`) | one photo, then the schema update with no key | 2 |
| Refusal test (`runs/verify_update_refuses_failing_column.log`) | a failing column added to a stored row | 0 |
| Notebook run 4, final (`runs/check-llm-output.executed.ipynb`, `runs/notebook-output.txt`, `runs/inside_the_fences.*`) | the notebook as saved, run top to bottom, with code cells identical to the clean notebook | 12 |

That's 62 Gemini calls in all. Gemini doesn't return a price. Each call used these tokens, from experiment 1's usage metadata:
- input: 1,108 for the second call or 1,357 for the first, with 1,089 of them for the image
- thinking: about 400 to 700
- answer: 90 to 150

## Checks

- **Spoken words.** 774 by `measure_voice.py`, or about 840 counted by paragraph, in 35 beats. The median beat is 24 words and the longest is 43. The model script has a median of 20 and a longest of 58. That's about 4 minutes of speech at 194 words a minute. With the two inserts (about 20 and 15 seconds) and time on the output, the video runs about 7 to 9 minutes.
- **Seconds to the promise:** 0, because it's the first sentence. **Seconds to the first code on screen:** about 50, and about 60 to `ListingDetails`. Her median is 82.
- **`measure_voice.py check --register talking`.** It flagged one measure: `i_rate` is 5.17, just under her range of 5.49 to 93.6. I left it, since the skill says flags are questions, not targets.
- **The headings, in order:**
  1. Start from an empty `llm_output_demo` directory
  2. `ListingDetails` is the answer we want for each photo
  3. The schema goes in the prompt, or in the request
  4. Each answer and its check get their own column
  5. A failed check keeps the answer on its photo's row
  6. With the schema only in the prompt, every answer failed `json.loads`
  7. With the schema in the request, every answer passed
  8. `pxt.Json[ListingDetails]` checks keys and types, not `Literal` values
  9. A UDF with `model_validate` catches the `Literal` value
  10. Each failed answer sat next to its error
- **One name per concept.** The two calls are always "the schema only in the prompt" and "the schema in the request". Other names that stay fixed: "the check", "the raw answer", and "the stand-in".

## Review (review-voice, fresh agent)

The first draft got **FAIL**, with three must-fix findings. All three are fixed:
1. **Pixeltable and its terms were never introduced.** The opening now says "In Pixeltable, a multimodal backend". Short beats now define a directory, `pxt schema diff` and `pxt schema update`, tables as Python classes, and a UDF.
2. **Each call had several names.** Now there's one name for each call, as listed under Checks. "The second prompt is only the request" is gone. The `ListingDetails` beat now tells the Pydantic model apart from the Gemini `MODEL`.
3. **The caveat about the cruiser bike's extra key ran past one sentence.** I cut it. It was also a line that depended on the run.

I also took these "should" findings:
- "checks it against the Pydantic model" now says "checks its keys and types".
- The setup beat now says six photos, 12 calls.
- The `parsed` explanation moved to after both calls are introduced.
- "the marketplace app" now says it's an app built for the Pydantic webinar.
- The close now retells the second part (`astype` against `model_validate`).
- "refusing the whole insert" became "stops the whole insert, and no rows are saved".
- The star ask now follows her own wording.

I also fixed these gaps in the chain:
- How the first prompt is built is now on screen.
- The `schema.py` excerpt now includes its import and `TableModel` lines.
- A beat is now spoken over the schema commands.
- A beat now says the URL becomes the image Gemini gets.
- The stand-in beat now names the answer from `response`.

These code changes meant running the notebook again from the top. That final run is run 4.

## Exemplars pulled (voice_corpus.py, register talking, era pixeltable)

- Openings: `yt:92lsL395T6s:000`, `yt:lE_m6ot8P3U:000`, `yt:0Q5G7T2UWk0:000`.
- Errors as data: `yt:iI5En37duSE:012` and `:013`.
- Close: `yt:92lsL395T6s:036`. The star ask is from `yt:lE_m6ot8P3U:034`, which the reviewer found.

## Gaps

- No bracketed prompts. Every line traces to a run or to the source.
- Not shown: how other providers handle a response schema, or Pydantic AI's own output modes.
