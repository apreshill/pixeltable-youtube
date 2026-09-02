# Multimodal MCPs Are Simpler Than You Think

Publish an MCP over your Pixeltable catalog. Other people can point their agent at it and search your photos and video.

This tutorial builds four recipes. Each recipe adds search to the database, runs it in the notebook, then exposes the same search through MCP. The server can search titles and captions, search image content, return short video clips, and answer from video captions and transcripts.

The notebook inserts the sample media. The MCP has no tool for inserting media or dropping tables.

This tutorial was inspired by Miguel Otero Pedrido's [How real AI Engineers build MCP Servers](https://theneuralmaze.substack.com/p/how-real-ai-engineers-build-mcp-servers), Alex Razvant's [Building MCP Servers for Video Search Engines](https://read.theaimerge.com/p/building-mcp-servers-for-video-search), and Avi Chawla's [Build the Ultimate MCP Server for Multimodal AI](https://blog.dailydoseofds.com/p/build-the-ultimate-mcp-server-for/).

## See what you will build

You will add these tools:

- `search_photo_text` searches titles and generated captions.
- `search_photo_content` searches the pixels with CLIP.
- `get_clip_for_text` returns eight seconds of video for a text query.
- `get_clip_for_image` returns eight seconds of video for an image query.
- `ask_about_video` answers from frame captions and transcripts.

The MCP also has resources for listing the catalog and describing a table. A `queries` table stores each tool call so the data owner can see how people search the catalog.

## Understand the architecture

Pixeltable is the database. It stores the source media, generated columns, indexes, tool calls, and answers in `mcp_demo`.

Schema files declare the catalog:

- `recipe1_store.py` adds photos, BLIP captions, and the query log.
- `recipe2_search.py` adds CLIP search for photos.
- `recipe3_video.py` adds videos, frames, frame captions, short clips, and CLIP search over frames.
- `recipe4_transcript.py` adds audio, local Whisper transcripts, text indexes, and grounded answers.

`server.py` reads the current schema when it starts. It registers only the tools that the schema can support. Restart the server after each schema update.

`tools.py` stays thin. It queries Pixeltable and returns results. Pixeltable runs BLIP, CLIP, Whisper, clip extraction, and the final answer.

## Check the prerequisites

You need:

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Git
- ffmpeg for audio and video clips
- `OPENAI_API_KEY` for the final answer in Recipe 4

Recipes 1 through 3 run locally. Recipe 4 uses a local Whisper model for transcription. The answer column calls `gpt-4o-mini`.

## Install the tutorial

Clone the repository:

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

Install this workspace member:

```bash
uv sync --package simpler-mcp
```

Run Jupyter from the tutorial folder:

```bash
cd simpler-mcp
uv run --package simpler-mcp jupyter lab
```

Open `multimodal-mcps-are-simpler.ipynb`. Use the workspace `.venv` as the kernel.

## Run the recipes

### Recipe 1: Search titles and captions

Apply `recipe1_store.py`. Insert the six sample photos. Search titles for `zebra`, then search captions for `striped`.

Title search returns the two zebra photos. Caption search can still miss because BLIP uses the word `zebra`, not `striped`.

Start the MCP from the notebook. It exposes `search_photo_text`. The same call also writes a row to `queries`.

### Recipe 2: Search image content

Apply `recipe2_search.py`. Search `photos.image` for `a striped animal`.

CLIP compares the text with the pixels. The zebra photos should rank first. Restart the MCP and call `search_photo_content`.

### Recipe 3: Search video

Apply `recipe3_video.py`. Insert the two sample podcast clips. Pixeltable samples frames, captions them, and maintains a CLIP index.

Search the frames from the notebook. Restart the MCP. Call `get_clip_for_text` with a scene description. Call `get_clip_for_image` with a local image path or public image URL.

Both tools return a short clip from the stored video. Speech questions still need Recipe 4.

### Recipe 4: Answer from captions and transcripts

Apply `recipe4_transcript.py`. Pixeltable extracts audio and runs `openai/whisper-tiny.en` locally. It also adds embedding indexes to frame captions and transcripts.

Search the transcript from the notebook. Restart the MCP and call `ask_about_video`. The tool retrieves caption and transcript evidence, inserts an `answers` row, then returns the computed answer.

## Connect another agent

Start the server from this folder:

```bash
uv run --package simpler-mcp python server.py
```

Copy `cursor-mcp.json.example` to `.cursor/mcp.json` in a project that should use the server. Enable the server in Cursor's MCP settings.

Any MCP client that supports streamable HTTP can use:

```text
http://127.0.0.1:8000/mcp
```

The notebook uses the MCP Python client against the same URL.

## Check the expected output

After Recipe 1, the tool list contains `search_photo_text`.

After Recipe 2, it also contains `search_photo_content`.

After Recipe 3, it also contains `get_clip_for_text` and `get_clip_for_image`.

After Recipe 4, it also contains `ask_about_video`.

No recipe adds a tool for dropping tables or inserting photos and videos.

## Find the files

```text
simpler-mcp/
  README.md
  multimodal-mcps-are-simpler.ipynb
  pyproject.toml
  recipe1_store.py
  recipe2_search.py
  recipe3_video.py
  recipe4_transcript.py
  resources.py
  tools.py
  server.py
  cursor-mcp.json.example
```

## Fix common problems

### The schema command cannot find the project

Run the notebook and `pxt schema` commands from the `simpler-mcp` folder.

### A tool does not appear

Apply the matching schema, then restart `server.py`. The server registers tools from the schema it sees at startup.

### Port 8000 is already in use

Stop the old server process. You can also run `python server.py --port 8001` and update the MCP URL.

### A model cannot find its API key

Set `OPENAI_API_KEY` where the Pixeltable daemon runs, then restart the daemon:

```bash
pxt daemon restart
```

### ffmpeg is missing

Install ffmpeg, then rerun the video schema or insert. Pixeltable uses it to extract audio and short clips.

### The insert cell creates duplicates

The notebook skips sample inserts when the table already has rows. For a full reset, run:

```python
pxt.drop_dir('mcp_demo', force=True)
```

Then start again with Recipe 1.
