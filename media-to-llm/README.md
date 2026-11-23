# Send Photos and Videos to Gemini Without Converting Them by Hand

This notebook sends product photos and videos to Gemini by passing a Pixeltable column straight into `pxtf.gemini.generate_content`. The notebook's code never reads a media file's bytes or states a media type. For comparison, it first sends one photo the usual way, with Pydantic AI's `BinaryContent`.

It answers a question developers ask in GitHub issues for Pydantic AI and Instructor: how do I get a photo or a video into the model call? For example, [instructor #1850](https://github.com/567-labs/instructor/issues/1850) asks how to get structured output from a video with Gemini.

## Overview

1. With Pydantic AI, an image goes into the call as `BinaryContent`: the bytes your code reads, plus a media type your code states, such as `media_type='image/jpeg'` ([Pydantic AI input docs](https://ai.pydantic.dev/input)). Pydantic AI also takes an `ImageUrl`, which it downloads for the Gemini API, and `BinaryContent.from_path` guesses a local file's media type from its extension. Either way, your code builds a message part for each media file in each call. For Gemini's Files API, the docs upload the media file with Google's own client and pass the result as an `UploadedFile`.
2. In Pixeltable, `schema.py` declares `photos`. Its `response` column passes the `photo` column straight into the call: `pxtf.gemini.generate_content([PHOTO_PROMPT, photo], model=MODEL)`. Because `photo` is an image column, the call gets each image itself, not a string, and the google-genai SDK sends it as `image/jpeg` bytes.
3. `schema_video.py` adds `videos`, with the `video` column in the same kind of list. Pixeltable sends a video of up to 3 MiB inside the request, base64-encoded. A bigger video goes through Gemini's Files API: Pixeltable uploads it, waits until Gemini has processed it, makes the call, and deletes the upload afterward.
4. `watch_files.py` is demo only. It prints a line for each Files API upload and delete, so you can see which video took that path.

In Pixeltable 0.7.25, `generate_content` does this for images and videos, not for audio or PDFs. Its media handling (`_process_media_contents` in `pixeltable/functions/gemini.py`) converts only video paths, so an audio or PDF path would reach Gemini as plain text (read from the source, not run). For audio, `pxtf.gemini.transcribe` takes an audio column and sends it to Gemini for you; this notebook doesn't run it.

## Technical Architecture

1. **Pixeltable database (`media_demo`)**
   - `photos`: one row per photo. You insert `name` and `photo`. Pixeltable computes `response` (the Gemini call) and `answer` (the text of its answer).
   - `videos`: one row per video. You insert `name` and `video`. Pixeltable computes the same two columns.

2. **Schema files**
   - `schema.py` declares `photos`.
   - `schema_video.py` declares the same `photos`, plus `videos`.

3. **`watch_files.py`**
   - Demo only. It wraps the google-genai SDK's async `files.upload` and `files.delete` so each call prints a line. Leave it out of a real app.

4. **Notebook (`media-to-llm.ipynb`)**
   - Resets `media_demo`, sends one photo with Pydantic AI, applies `schema.py`, inserts four photos, applies `schema_video.py`, and inserts two videos.

The photos are four of the 57 sample photos from the secondhand marketplace app in the Pixeltable and Pydantic webinar. The notebook reads them from:

`https://raw.githubusercontent.com/apreshill/pixeltable-marketplace/main/samples/`

The videos are the same 18-second street video from the Pixeltable repo, at two sizes: `bangkok_half_res.mp4` (640x360, 2.1 MiB) and `bangkok.mp4` (1280x720, 6.1 MiB). The notebook reads them from:

`https://raw.githubusercontent.com/pixeltable/pixeltable/main/tests/data/`

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**
- **A Gemini API key**

The notebook makes seven calls to `gemini-3.8-flash`: one from Pydantic AI, four for the photos, and two for the videos. In our run, they came to under 2 cents in all, priced with `genai-prices`, the price data Pydantic AI uses.

Set the key in the environment you start Jupyter from:

```bash
export GEMINI_API_KEY='...'
```

Pydantic AI reads `GOOGLE_API_KEY` or `GEMINI_API_KEY` from the environment. Pixeltable reads the same variables, or `api_key` in the `[gemini]` section of `~/.pixeltable/config.toml`. The Pydantic AI cell needs the environment variable.

This folder is a Pixeltable project root. `media-to-llm/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

```bash
cd media-to-llm
uv sync
```

That creates `media-to-llm/.venv` and installs Pixeltable 0.7.25 or newer, `google-genai`, `pydantic-ai-slim[google]`, and Jupyter.

### 3. Register the Kernel

```bash
uv run python -m ipykernel install --user --name media-to-llm --display-name media-to-llm
```

### 4. Open the Notebook

Run Jupyter from this folder, in a shell where `GEMINI_API_KEY` is set:

```bash
uv run jupyter lab
```

Open `media-to-llm.ipynb` and pick the `media-to-llm` kernel.

### 5. Run the Notebook

Run it from top to bottom. The photo insert took about 11 seconds in our run, and the video insert about 15. The reset cell drops `media_demo`, so running from the top always starts from empty tables.

## Expected Output

Gemini's answers vary from run to run. The token counts, sizes, and printed lines are what to check.

The Pydantic AI cell prints a one-sentence description of the desk lamp, and `1105`, the input tokens Gemini counted: 16 for the prompt and 1,089 for the image.

The photo insert:

```
Inserted 4 rows with 0 errors in 10.64 s (0.38 rows/s)
```

Each of the four photos shows `input_tokens` of 1105, the same as the Pydantic AI call. All four photos are 1024x1024.

The video insert prints two lines from `watch_files.py`, both for the bigger video, then the insert:

```
uploaded a 6.1 MiB video to the Files API as files/<id>
deleted files/<id> from the Files API
Inserted 2 rows with 0 errors in 14.37 s (0.14 rows/s)
```

The last cell shows each video's size in MiB, with its answer:

```
                   name  size_mib
0           bangkok.mp4       6.1
1  bangkok_half_res.mp4       2.1
```

`runs/` has the notebook as we executed it, and `runs/verify_paths.log`, an off-camera check of what each call sent: the photo as a PIL image that the SDK turned into `image/jpeg` bytes, the small video as inline `video/mp4` data, and the big video as a Files API upload that was gone after the call.

## File Layout

```
media-to-llm/
  README.md
  media-to-llm.ipynb
  schema.py
  schema_video.py
  watch_files.py
  notes.md
  runs/
    media-to-llm.executed.ipynb
    verify_paths.py
    verify_paths.log
  pyproject.toml
  uv.lock
```

The local Pixeltable catalog is under `~/.pixeltable`. It is not stored in this repo. The photos and videos Pixeltable downloads go to its file cache there too.

## Troubleshooting

### The Pydantic AI cell asks for `GOOGLE_API_KEY`

The key isn't in the environment Jupyter started from. Export `GEMINI_API_KEY` or `GOOGLE_API_KEY`, restart Jupyter from that shell, and run the notebook from the top.

### Schema commands cannot find the project

`cd` into `media-to-llm` and run the notebook from there.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from this folder, register the kernel as above, then pick `media-to-llm`.

### `watch_files.py` prints nothing

Import it before the video insert, in the same kernel. It prints only for a video over 3 MiB, because a smaller one goes inside the request and never touches the Files API.

### The big video's row fails with a timeout

Pixeltable waits up to 10 minutes for Gemini to finish processing an uploaded video, then raises a timeout. By default an insert saves all of its rows or none, so neither video is saved, and you can run the video insert cell again.

### Duplicate primary key on insert

A row with that `name` is already in the table. Run the notebook from the top; the reset cell drops `media_demo`.
