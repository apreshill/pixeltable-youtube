# Notes: Keep the LLM's Answer When It Fails Validation

Production notes for the script in `keep-failed-answers.ipynb` (markdown cells are spoken, code cells are on screen). Written Nov 23, 2026, for the Pydantic webinar's follow-up videos, problem 3, "/handling failed answers".

## Promise

By the end, the viewer keeps an LLM's whole answer about a photo when it fails a Pydantic model, with the error on its row, and reruns the LLM only for the rows that failed.

## The chain, and where each link is on screen

1. The viewer fills in `name` and `photo` (a raw.githubusercontent.com URL). Cell `sed -n '10,12p;25,40p' schema.py` and the insert cell.
2. `response` calls the LLM: `stand_in_gemini([DETAILS_PROMPT, photo], model=MODEL, config=json_config(ListingDetails))`. The prompt text, `MODEL`, and `json_config` are on screen in the same cell.
3. The stand-in returns `{'parsed': <answer>}`. Cell `sed -n '25,41p' stand_in.py`.
4. `details = response.parsed.astype(pxt.Json[ListingDetails])` checks the answer. Same schema cell.
5. Each row gets the checked details, or its error in `details.errortype` and `details.errormsg`. The two select cells after the `on_error='ignore'` insert.
6. `recompute_columns(listings.response, where=failed)` calls the LLM again for the failed rows, then recomputes `details`. `stand_in.CALLS` shows which photos.

## What runs, and the evidence (all on Pixeltable 0.7.25, Pydantic 2.14.4)

| Claim | Evidence |
|---|---|
| `model_validate` raises for the whole model and returns nothing | `runs/keep-failed-answers.outputs.txt`, In [5] |
| The default insert stores no rows when one check fails | outputs, In [10]: `Expected string, got list`, `0` |
| The default insert called the stand-in for all six photos before it was refused | `runs/verify_claims.log`, 1 (not said in the script; the script says "you'd pay for those calls" with no number, because Gemini's async calls weren't tested this way) |
| `on_error='ignore'` stores all six rows, two with errors in `details` | outputs, In [11] and In [12] |
| `response` keeps the whole answer; `details` is `None` on failed rows | outputs, In [13] |
| `errors_only=True` on `details` reruns the check, calls nothing, and both still fail | outputs, In [14] and In [15]: `2`, `([], 2)` |
| `errors_only=True` on `response` finds no rows | `runs/verify_claims.log`, 2: `rows rerun: 0` |
| `recompute_columns(response, where=...)` calls the LLM only for the two failed rows, then recomputes `details` | outputs, In [16] to In [18] |
| The check doesn't check `Literal` values (`'barely used'` passes) | `runs/verify_claims.log`, 3; also the Nov 23 trailer run (`pxt-social-ops/content/voice/2026-11-pydantic-webinar-trailer/runs/`); source: `type_system.py` turns `Literal` into `String`, and `JsonType.TypeSchema.validate_literal` checks required keys and types only |
| With the schema in the request, Gemini's answers passed the check on all six photos | `runs/gemini_probe.log` (6 calls) and `runs/gemini_swap.log` (6 calls, through `schema_gemini.py`) |
| Pydantic's maintainers suggest a `WrapValidator` fallback per field | pydantic #9371 (sydney-runkle's reply), discussion #13811 (Viicos's `FallbackToDefault`), read with `gh` on Nov 23 |

## Gemini calls

12 calls to `gemini-3.8-flash`, all in a sandbox, all returned `STOP` and passed the check:

- `runs/gemini_probe.py`: 6 calls with app.py's exact prompt and config, one photo each. Each 1,108 input tokens, 83 to 116 output tokens, 467 to 828 thinking tokens. These answers are `gemini_answers.json`.
- `runs/gemini_swap.py` after `pxt schema update schema_gemini.py answers_gemini`: 6 calls. Each 1,108 input tokens, 94 to 134 output tokens, 404 to 617 thinking tokens. The rerun had 0 rows.

The API showed no cost. In total, about 13,300 input tokens, 1,300 output tokens, and 7,100 thinking tokens.

## Where the plan and the code differ

- **A stand-in, not a real failure.** The plan preferred a real Gemini failure without planting one. With `response_json_schema`, Gemini passed on 12 of 12 calls, so the stand-in stays, named as demo only in the setup beat, on screen, and in the README, the way `rerun-failures/udfs.py` does. Unlike the Nov 23 run's stand-in, this one replays Gemini's real answers from the probe run and breaks two of them (a wrong type and a missing key), so the rows that pass hold real answers.
- **The stand-in has to be told to stop breaking answers.** It breaks the same two answers on every call, so the default insert and the `on_error='ignore'` insert both fail. The notebook clears `stand_in.BROKEN` before the rerun, and the script says why out loud. A "first time only" stand-in (as in rerun-failures) would have let the default insert use up the failures.
- **An extra step: rerunning the check.** The plan had only the rerun of `response`. The script first runs `errors_only=True` on `details`, which reruns the check on the same answers and fails again with no LLM call. That's why the rerun targets `response` with a `where` on `details.errortype`, which differs from rerun-failures' `errors_only=True`.
- **One photo per row**, not app.py's three, to keep six rows small and cheap. The prompt still says "these photos", as in app.py and the webinar's `steps.py`.
- **The default insert's error is printed as one line** (`str(e).splitlines()[1]`), because the full message repeats the whole expression, JSON schema included.

## Voice

Exemplars pulled with `voice_corpus.py search --register talking --era pixeltable` (read for how she moves, not copied):

- Openings: `yt:lE_m6ot8P3U:000`, `yt:N0-j7reElhc:000`
- Errors as data, `on_error`: `yt:iI5En37duSE:011`, `yt:iI5En37duSE:012`, `yt:iI5En37duSE:013`
- Rerunning failed rows: `yt:SDnIeB63lfQ:022`
- Saying what's free or demo only: `yt:0Q5G7T2UWk0:005`
- Close and star ask: `yt:lE_m6ot8P3U:034`

## Checks

- Spoken words: 828 by beat count (762 by `measure_voice.py`, which leaves out code identifiers), with headings and cue lines left out. 33 beats, median 25 words, longest 45. At her 194 words a minute, that's about 4.3 minutes of speech. With the code on screen, the video should land well under 10 minutes.
- The promise comes in the first sentence. The first code (`!uv sync`) comes after about 130 spoken words, about 40 seconds in.
- `measure_voice.py check`: one flag, a low rate of "I" (3.94 per 1,000 words against her range of 5.49 to 93.6). Kept as is: adding "I" lines to meet it would pad the script, and the reviewer agreed.
- No dashes, no "So" or "And" openers, no spoken list of three in one line, no "let me show you".
- Headings in order: start from an empty directory; one wrong field fails the whole Pydantic model; the answer and its check go in two columns; by default, one failed check stores none of the rows; with `on_error='ignore'`, every row is stored with its error; rerun the LLM call, not the check; for real Gemini calls, `schema_gemini.py` changes the `response` line; each failed answer stayed on its row.

## Review (review-voice, register talking, fresh agent)

First pass: FAIL. Findings and what changed:

- Opening line about the two Pydantic threads, and the maintainers' suggestion, had nothing on screen. Added screen cues for #9371, #13811, and the maintainer's reply.
- The stand-in caveat ran three sentences and was repeated after the `schema_gemini.py` diff. The reason moved to the setup beat, the stand-in beat is two sentences, and the repeat is gone.
- "Model" named both the Pydantic model and the LLM. The LLM is now always "the LLM", calls that went to the stand-in say "the stand-in was called", and the heading says "Rerun the LLM call".
- "I'll show why when we get to it" left the question open. The reason is said there now.
- Computed columns and what Pixeltable is weren't said. One beat now says both where the table appears.
- "Their rows went through" implied the failed rows didn't. Now "passed the check".
- "Its Pydantic check" overstated the check. Now "its check against the Pydantic model".
- "Stores none of the photos" became "none of the rows".
- "The stand-in can't tell" became "The stand-in always breaks the same two answers".
- The `WrapValidator` line was circular. It now says each field needs its own validator and its own default.
- The rerun-failures video had no context. It's named, with "linked below".
- Chain gaps: `parsed`, `errortype`, `errormsg`, and `failed` are now named where they appear.

Second pass (same agent): everything above confirmed fixed, all six chain links on screen and said plainly, and one new must caused by a fix. "Every field needs its own validator" contradicted the reply on screen, which is one reusable `FallbackToDefault` wrapper. It now says "you have to wrap every field and give each one a default." Also applied: the stand-in beat no longer repeats the setup beat, and the close says "linked in the description" for the other video so "linked below" isn't said twice. Overruled: renaming `json_config`'s `model` parameter (on screen, not spoken), because it matches app.py in the webinar.

## Gaps

- With real Gemini, nothing in this video failed, so the video shows no real failure. The stand-in's broken answers (a list for `color`, a missing `condition`) are the kinds of mistakes the commenters in pydantic #9371 list, not ones we saw from Gemini.
- Not tested: how many Gemini calls run before an async `generate_content` insert is refused under the default `on_error`.
- `runs/keep-failed-answers.executed.ipynb` holds the photos as inline thumbnails (about 1 MB).
