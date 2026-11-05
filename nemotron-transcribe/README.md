# Promptable transcription with Nemotron

Pixeltable stores the recording and fills in the transcript. The transcript column calls [NVIDIA Nemotron 3.5 Transcribe](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B) on Hugging Face. The prompt is a column on the same row, so a second wording is a second insert, not a second model.

This follows the Whisper and WhisperX transcription notebook: a video, audio extracted from it, then a computed transcript. That notebook split the recording and added one column per model. Nemotron takes a recording up to an hour, and the prompt tells it how to write the transcript.

## Overview

1. `recordings` stores a video, a label, and a prompt.
2. `audio` is the soundtrack, extracted when the video is inserted.
3. `transcript` sends that audio and the prompt to Nemotron through Hugging Face.

The notebook inserts the same short clip three times. The prompts ask for a verbatim transcript, a cleaned transcript, and a transcript that keeps the name Lex Fridman.

## Technical Architecture

1. **Pixeltable database (`nemotron_demo`)**
   - `recordings`: the video, the prompt, the extracted audio, and the transcript

2. **Schema file**
   - `schema.py` declares `recordings`
   - `udfs.py` calls the Hugging Face router. The model id is `nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B`

3. **Notebook (`nemotron-transcribe.ipynb`)**
   - Resets `nemotron_demo`, applies `schema.py`, and inserts the three prompts

The clip is a public excerpt used in the transcription cookbook:

`https://raw.githubusercontent.com/pixeltable/pixeltable/main/docs/resources/audio-transcription-demo/Lex-Fridman-Podcast-430-Excerpt-0.mp4`

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**
- **A Hugging Face token with Inference Providers credits**

Hugging Face serves this checkpoint through its inference router. Create a token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) and add credits at [huggingface.co/settings/inference-providers](https://huggingface.co/settings/inference-providers). Each inserted row is one transcription request.

Put the token where the Pixeltable worker can see it. Either export it before you start Jupyter:

```bash
export HF_TOKEN='hf_...'
```

or add it to `~/.pixeltable/config.toml`:

```toml
[hf]
token = 'hf_...'
```

A token saved by `hf auth login` is also read, from `~/.cache/huggingface/token`.

This folder is a Pixeltable project root. `nemotron-transcribe/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

```bash
cd nemotron-transcribe
uv sync
```

That creates `nemotron-transcribe/.venv` and installs Pixeltable 0.7.14 or newer, plus the OpenAI client used to call the Hugging Face router.

### 3. Register the Kernel

```bash
uv run python -m ipykernel install --user --name nemotron-transcribe --display-name nemotron-transcribe
```

### 4. Open the Notebook

Run Jupyter from this folder:

```bash
uv run jupyter lab
```

Open `nemotron-transcribe.ipynb` and pick the `nemotron-transcribe` kernel.

### 5. Run the Notebook

Run it from top to bottom.

1. `!uv sync`
2. The reset cell drops `nemotron_demo` if a previous run left it behind
3. `pxt schema diff schema.py nemotron_demo`
4. `pxt schema update schema.py nemotron_demo -f`
5. The insert cell adds the clip three times, with a different prompt each time

The diff prints a plan before anything changes. For a fresh catalog it looks like this:

```
+ nemotron_demo/recordings          create

Plan: 1 create, 0 update, 0 unchanged, 0 extra  |  0 destructive
```

## Expected Output

The last cell prints `label`, `prompt`, and `transcript` for the three rows. The wording of `transcript` follows the prompt on that row. The first run also downloads the clip and extracts the audio, so it takes longer than a later query of the same rows.

## File Layout

```
nemotron-transcribe/
  README.md
  nemotron-transcribe.ipynb
  schema.py
  udfs.py
  pyproject.toml
  uv.lock
```

The local Pixeltable catalog is under `~/.pixeltable`. It is not stored in this repo.

## Troubleshooting

### Schema commands cannot find the project

`cd` into `nemotron-transcribe` and run the notebook from there.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from this folder, register the kernel as above, then pick `nemotron-transcribe`.

### A Hugging Face token is required

Set `HF_TOKEN`, or `token` under `[hf]` in `~/.pixeltable/config.toml`, then run the insert cell again. Pixeltable reruns the transcript cells that failed.

### You have no remaining credits

The router answered, and the account has no Inference Providers credits. Add credits, then run the insert cell again.

### Duplicate rows after rerunning the insert cell

Run the notebook from the top. The reset cell drops `nemotron_demo`.
