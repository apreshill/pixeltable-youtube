# Notes: Send Photos and Videos to Gemini Without Converting Them by Hand

The script is the notebook, `media-to-llm.ipynb`: markdown cells are the spoken beats, code cells are what's on screen. `runs/media-to-llm.executed.ipynb` is the notebook as executed on Nov 23, 2026. The folder README is `README.md`.

## Promise

By the end, a Pydantic developer has passed a photo column and a video column straight into `pxtf.gemini.generate_content` without reading a byte or stating a media type in their code, has compared that with Pydantic AI's `BinaryContent`, where their code reads the bytes and writes `image/jpeg`, and has seen a video over 3 MiB go through Gemini's Files API and get deleted after the call.

The question it answers, from the webinar teaser: "Why do I have to convert every media file before my LLM can read it?"

## The chain, and where each link is on screen

| Link | On screen |
|---|---|
| Pydantic AI: the viewer's code downloads the photo's bytes and states `media_type='image/jpeg'` | the Pydantic AI cell, its two commented lines |
| What comes back: one sentence, and 1,105 input tokens | that cell's output |
| Pixeltable: the viewer fills in `name` and `photo` (a URL) | the photo insert cell |
| Pixeltable downloads each photo on insert | said; the URLs are in the insert cell |
| The prompt: `PHOTO_PROMPT`, a fixed sentence, plus the `photo` column, in one list | `!sed -n '8,17p' schema.py` |
| The model call: `generate_content` in the computed column `response`; `answer` pulls out the text | the same lines |
| The filled prompt for one row: the fixed sentence plus that row's photo | the sentence in `schema.py`, the photo in its row in the select cell; the off-camera log shows the actual contents list (`runs/verify_paths.log`) |
| How the image reaches Gemini: the image column gives the call an image, not a string; the google-genai SDK sends `image/jpeg` bytes | `photo: pxt.Image` in the schema lines; said; `runs/verify_paths.log` (off camera) |
| What comes out: `answer`, and `input_tokens` of 1,105 per photo | the select cell |
| Videos: the viewer fills in `name` and `video` (a URL) | the video insert cell |
| The video prompt and call | `!sed -n '10p;21,26p' schema_video.py` |
| The path each video takes: up to 3 MiB inside the request, above that a Files API upload, deleted after the call | `watch_files.py`'s printed lines in the video insert cell; the `size_mib` column in the last cell |
| What comes out: each video's `answer` | the last cell |

## Traces for every claim

Source paths are in the Pixeltable 0.7.25 package the run used (`media-to-llm/.venv/lib/python3.14/site-packages/`). "In [n]" is a cell of `runs/media-to-llm.executed.ipynb`.

| Claim in the script | Evidence |
|---|---|
| "pass a photo column and a video column straight into a Gemini call in Pixeltable" | `schema.py` line 16, `schema_video.py` line 25 |
| "Pixeltable, a multimodal backend whose columns can call models" | `devrel-skills/profiles/pixeltable/positioning.md`, Names ("a multimodal backend"); the model script's "a database whose columns can call models" |
| "With Pydantic AI, our code builds a message part for each media file in each call, such as its bytes plus a media type" | the Pydantic AI input docs: every media input is a part in the call's list (`ImageUrl`, `BinaryContent`, `UploadedFile`); `BinaryContent(data=..., media_type=...)`; In [3]. Narrowed after the re-check: Pydantic AI also takes `ImageUrl` (media type inferred from the URL, and downloaded by Pydantic AI for the Gemini API) and `BinaryContent.from_path` (media type guessed from the extension), so the script no longer says the bytes and media type are always the developer's job |
| "In Pixeltable, we pass the column itself" | `schema.py` line 16: `[PHOTO_PROMPT, photo]`; the Pixeltable cells have no `read_bytes`, no `httpx.get`, no `media_type` |
| "A video over 3 MiB even goes through Gemini's Files API, and Pixeltable deletes the upload after the call" | `pixeltable/functions/gemini.py`: `GEMINI_INLINE_LIMIT_BYTES = 4 * 2**20`, and `_process_media_contents` sends a video inside the request when `size_bytes <= GEMINI_INLINE_LIMIT_BYTES * 3 // 4` (3,145,728 bytes), else queues it for upload; `_gemini_file_uploads` uploads, waits until the media file is active (`_poll_until_active`), and deletes it in `finally`. In [12]; `runs/verify_paths.log` ("You do not have permission to access the File ... or it may not exist" after the call) |
| "The notebook is in the `media-to-llm` folder of the repo linked below" | this folder |
| "I set `GEMINI_API_KEY` in my environment, where Pydantic AI and Pixeltable both read it" | `pydantic_ai/providers/google.py` line 189 (`GOOGLE_API_KEY` or `GEMINI_API_KEY`); `pixeltable/functions/gemini.py` module docstring; every call ran with only `GEMINI_API_KEY` set |
| "The Pydantic AI docs send an image as `BinaryContent`: the raw bytes, plus a media type written in the code" | https://ai.pydantic.dev/input (now a 301 to https://pydantic.dev/docs/ai/advanced-features/input/), "Image Input": `BinaryContent(data=image_response.content, media_type='image/png')`, with a callout to use `Path().read_bytes()` for a local file |
| "one desk lamp photo ... from the sample photos of a secondhand marketplace app" | `pixeltable-marketplace/samples/desk-lamp-1.jpg`, read from GitHub (200) |
| "our code builds a part like this for each media file in each call" | In [3]: the `BinaryContent` built for this call; a part per media file per call holds for `ImageUrl` and `from_path` too |
| "Gemini counted 1,105 input tokens" | In [3]: `1105` |
| "`schema.py` declares the `photos` table. The only columns you fill in are `name` and `photo`. `response` is a computed column that calls Gemini on every new row, and `answer` pulls the text out of the response." | `schema.py` lines 12 to 17 |
| "The list holds the same prompt and the `photo` column itself" | `PHOTO_PROMPT` in `schema.py` is the same string as `PROMPT` in the Pydantic AI cell |
| "Because `photo` is an image column, Pixeltable loads it as an image, not a string, and the google-genai SDK sends it as `image/jpeg` bytes" | `runs/verify_paths.log`: "PIL image JPEG (1024, 1024) (Pixeltable loaded it from file_cache/)", then "google-genai SDK pil_to_blob: image/jpeg, 136060 bytes"; `pixeltable/exprs/inline_expr.py` (`InlineList.eval` puts the column's value, a PIL image, in the list); `google/genai/_transformers.py` `pil_to_blob` (JPEG when the PIL image was read from a JPEG file); facts.md ("code gets the image, not a string") |
| "`pxt schema diff` shows the plan, and `pxt schema update` creates the table" | In [5], In [6] |
| "Pixeltable downloads each one when it inserts the row, and Gemini answers during the same insert" | In [7] (`Inserted 4 rows with 0 errors in 10.64 s`); the file cache path in `runs/verify_paths.log` |
| "Every photo used 1,105 input tokens, the same as the Pydantic AI call: the prompt plus one image" | In [8] (all four 1105); In [3]; `runs/verify_paths.log` (IMAGE 1089, TEXT 16). All four photos are 1024x1024, which is why the counts match |
| "Gemini takes a video inside the request, or as a media file uploaded to its Files API first" | `gemini.py`: `inline_data` for a small video, `file_data` with the uploaded media file's URI for a large one (`_replace_upload_placeholders`) |
| "Pixeltable picks by size: up to 3 MiB goes inside the request, and a bigger video goes through the Files API" | `_process_media_contents`, `_gemini_file_uploads` |
| "`schema_video.py` repeats `photos` and adds `videos`" | `schema_video.py`; In [10] |
| "Because `video` is a video column, the call gets the downloaded media file, not the URL" | the trial run's `videos.video.localpath`: a path in the sandbox's `file_cache/`; `_process_media_contents` reads the local path (`Path(data).expanduser()`, `stat()`), and returns any string that isn't an existing local video file unchanged |
| "`photos` shows no change, so its answers stay as they are, and `videos` is new" | In [10] (`= media_demo/photos no change`, `+ media_demo/videos create`), In [11] |
| "a small module that prints a line for each Files API upload and delete. It's only for this demo." | `watch_files.py` |
| "the same 18-second street video from the Pixeltable repo at two sizes" | PyAV on the cached files: both 18.48 s, 1280x720 and 640x360, no audio stream |
| "The module printed lines for only one video. Pixeltable uploaded it before the call and deleted it after, so the upload doesn't stay in your Gemini project." | In [12]; `_gemini_file_uploads` is an `async with` around the call; `runs/verify_paths.log` shows the upload placeholder, the upload, the delete, then the 403 for that media file's name |
| "The `size_mib` column shows which video that was" / "The 6.1 MiB video went through the Files API, and the 2.1 MiB video went inside the request" | In [13]: `size_mib` 6.1 and 2.1 (6,406,129 and 2,234,371 bytes); `runs/verify_paths.log`: "inline_data video/mp4, 2979164 base64 chars" for the small one |
| "In Pixeltable 0.7.25, this works for images and videos, not for audio or PDFs" | `_process_media_contents` converts only strings whose guessed type is `video/*`; a PIL image goes to the SDK, which converts it; an audio or PDF path stays a string, which the SDK sends as text (`_transformers.t_part`). From the source, not run |
| Close: "With Pydantic AI, our code read the bytes and wrote `image/jpeg`. In Pixeltable, the `photo` column went straight into `generate_content`." / "Pixeltable picked the path for each video by its size" | In [3], `schema.py` line 16, In [12], In [13] |
| "a star on Pixeltable's own GitHub repo helps other developers find it" | her own close (yt:lE_m6ot8P3U:034) |

## Gemini calls

All to `gemini-3.8-flash`, priced with `genai-prices` 0.2.1 at $0.75 per million input tokens and $3.75 per million output tokens (thinking tokens count as output). Nothing failed, and no call hit a rate limit.

| Run | Calls | Cost |
|---|---|---|
| Trial script (Pydantic AI, 2 photos, 2 videos) | 5 | about $0.009 |
| First notebook run | 7 | about $0.014 |
| `verify_paths.py`, first attempt | 0 (my logging patch failed before the call) | $0 |
| `verify_paths.py`, second attempt | 3 | about $0.005 |
| Second notebook run | 7 | about $0.0145 |
| `verify_paths.py`, final (`runs/verify_paths.log`) | 3 | $0.0049 |
| Third notebook run, after the first review's fixes | 7 | about $0.0134 |
| Final notebook run, after the last should (`runs/media-to-llm.executed.ipynb`) | 7: Pydantic AI about $0.002 (the trial's `RunUsage` for the same request showed $0.0021), photos $0.0020 to $0.0023 each, videos $0.0015 each | about $0.014 |
| Total | 39 | about $0.075 |

Seven Files API uploads (one per run with the big video), each deleted after its call.

## Versions run

Pixeltable 0.7.25, google-genai 2.34.0, pydantic-ai-slim 2.71.0, pydantic 2.14.4, on Python 3.14.0 (this folder's `.venv`). Every run used a sandbox Pixeltable home from `pxt-sandbox.sh 0.7.25` in the session scratchpad, so nothing touched `~/.pixeltable`. The notebook ran headless with `jupyter nbconvert --execute`. That run set `PYDANTIC_AI_NO_BANNER=1`, because Pydantic AI prints a first-run banner when it detects a terminal or a coding agent; a viewer's notebook isn't either, so it doesn't show there.

## Her real speech, by part

- Opening on what the video shows, then the media-file pain: yt:0Q5G7T2UWk0:000, yt:lE_m6ot8P3U:000
- A Gemini call in a computed column: yt:lE_m6ot8P3U:010, yt:SDnIeB63lfQ:013
- Saying Gemini's request-size limit out loud: yt:SDnIeB63lfQ:027
- Close, the parts retold in order: yt:92lsL395T6s:036
- Star ask with its reason: yt:lE_m6ot8P3U:034

## Choices and gaps

- **Two tables, not one.** The brief described one table with an image column and a video column. A row here is one media file, so `photos` and `videos` are separate tables, and videos arrive as a second schema file with its own `pxt schema diff`, as in the other videos in this repo.
- **The Pydantic AI code runs for real.** It downloads the photo with `httpx`, as the docs example does, because viewers clone pixeltable-youtube, not the marketplace.
- **Evidence for the Files API path.** `watch_files.py` wraps the google-genai SDK's async `files.upload` and `files.delete` and prints a line for each. The script calls it demo only. I tried HTTP request logs first, but google-genai uses aiohttp for async calls when it's installed, and aiohttp doesn't log requests.
- **1,105 tokens.** All four photos are 1024x1024, so all four show 1,105. The script says "the prompt plus one image", not "the same photo".
- **No claim that Pydantic AI fails on big videos.** The 3 MiB rule is Pixeltable's choice; Gemini takes much larger inline requests. The script says only that, in Pydantic AI, a Files API upload is the developer's code, per the docs.
- **Audio and PDFs** are from the source, not run. The README adds that `pxtf.gemini.transcribe` takes an audio column; not run either.
- **No Pydantic model for the output.** The other three videos cover output; this one is only about getting media into the call.
- **No GitHub-issue credit in the script.** The first draft opened with "Developers ask how to get media into the model call in GitHub issues for Pydantic AI and Instructor". The voice review flagged it as an opening line the video never shows, so the opening now states the viewer's own pain, which the Pydantic AI cell shows. The README keeps the issue link (instructor #1850).
- **No Pydantic AI upload code on screen.** The first draft said that, in Pydantic AI, a Files API upload is your code's job (the docs upload with Google's client, then pass an `UploadedFile`). Nothing showed it on screen, so the script cuts it and the README keeps it.

## Checks

- Spoken words: 581 by this folder's count (550 by `measure_voice.py`, which leaves out code spans) in 23 beats, median 28, longest 39. The model: 1,581 in 44 beats, median 20. Budget for a one-app tutorial: 500 to 900. About three minutes of speech at her 194 words a minute; with the cells on screen, the video should land well under 10 minutes. 13 code cells.
- Seconds to the promise: the first sentence. First code (`!uv sync`) after 119 spoken words, about 37 seconds (her median is 82).
- `measure_voice.py check --register talking`: 550 words, 0 outside her range.
- Headings read in order: Your Gemini key goes in the environment; With Pydantic AI, our code reads the bytes and states the media type; The photo column goes straight into the Gemini call; Each photo gets its answer when it's inserted; A video column goes into the call the same way; A video over 3 MiB goes through the Files API and is deleted after the call; Two columns went to Gemini with no conversion code.

## review-voice

Run in a fresh agent on the first draft (603 words). FAIL with five musts, all fixed:

- M1, no line said why a column goes in unconverted: the photo beat now says the image column is why the call gets an image, not a string; the video beat says the video column is why the call gets the downloaded media file, not the URL.
- M2, Pixeltable was never said to be anything: the first line names it as a multimodal backend whose columns can call models.
- M3, the GitHub-issues line was an opening line the video never shows: cut, and the opening states the viewer's own pain instead.
- M4, the Pydantic AI upload sentences had nothing on screen: cut.
- M5, "inside the request" and "inline" named one idea: "inside the request" everywhere.

Shoulds taken: the size column in MiB (`size_mib`) to match the speech; the video part opens on the reason before the schema file; `schema.py` named in the photo part; "our marketplace demo" made concrete; the delete in active voice, with why it matters; the repeated result and "the same line of schema" cut; the star ask names Pixeltable's own repo; where the code lives moved into the setup beat.

The notebook was executed again after these changes (`runs/media-to-llm.executed.ipynb`).

**Re-check** (same agent): M1 to M5 resolved. Two new musts, both fixed:

- N1, the opening and the Pydantic AI beat said more than the evidence: "your code turns each media file into bytes and a media type before the call" and "every media file goes through those two lines before each call". Pydantic AI 2.71 also takes `ImageUrl` and has `BinaryContent.from_path`. Both lines now say only that the code builds a message part for each media file in each call, which holds for every Pydantic AI input type. The README names `ImageUrl` and `from_path`.
- N2, "your code" and "our code" named the same code, and "In Pixeltable, our code does neither" could be heard as Pixeltable's own code: the script now says "our code" for the notebook's code throughout, and "In Pixeltable, we pass the column itself."

**Final check** (same agent): PASS. N1 and N2 resolved, no new musts. One should taken: the Pydantic AI heading and the code comment now say "our code" too, so the screen matches the speech. The notebook was executed once more after that change, so `runs/media-to-llm.executed.ipynb` is a full run of the final notebook.

The reviewer also raised one point for triage rather than voice: the photo contrast ("builds a part for each media file in each call" against "pass the column itself") is true but leans toward less code, which facts.md says is never the point. The stronger contrasts the code backs are that the column's type is declared once for every row, and that a big video's Files API upload and delete are handled for you. The full review is in the session scratchpad, `media-to-llm/review-voice.md`.
