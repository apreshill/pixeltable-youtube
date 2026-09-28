# Pixeltable YouTube

Code that goes with Pixeltable YouTube videos. Clone this repo to run a tutorial on your machine.

Pixeltable is an OLTP database for multimodal AI applications. Media, model outputs, and app state live in one database and stay consistent as data changes.

**Pixeltable:** [GitHub](https://github.com/pixeltable/pixeltable) · [Docs](https://docs.pixeltable.com/) · [YouTube](https://www.youtube.com/@PixeltableHQ)

## Overview

This repo holds one folder per video. Open the folder that matches the video you are watching. Run its notebook from top to bottom.

You can:

- Clone the repo and install that folder's packages
- Run the notebook locally while you watch
- Inspect the same Pixeltable catalog with the Python SDK, the `pxt` CLI, or `pxt dashboard`

## Technical Architecture

Each video folder is a Pixeltable project.

1. **Schema files**
   - Declare tables, computed columns, and indexes
   - The notebook applies them with `pxt schema diff` and `pxt schema update`

2. **Notebook**
   - Follows the video
   - Inserts sample data and runs the searches you see on screen

3. **Pixeltable catalog**
   - Lives on your machine under `~/.pixeltable`
   - Photos, captions, indexes, and answers stay there after a cell runs

## Prerequisites

Before you begin, you need:

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**

Some recipes call OpenAI. Those cells need `OPENAI_API_KEY`. The folder README says which recipes that is.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

Pick the folder for the video you are watching. From the repo root:

```bash
uv sync --package simpler-rag
# or
uv sync --package simpler-mcp
```

### 3. Open the Notebook

Run commands from that video folder so `pxt schema` can find the schema files.

```bash
cd simpler-rag
uv run --package simpler-rag jupyter lab
```

Open `rag-is-simpler.ipynb`. Select the `pixeltable-youtube` kernel if Jupyter offers it.

You can also open the notebook in Cursor or VS Code and run the first cell:

```python
!uv sync --package simpler-rag
```

### 4. Follow the Folder README

Each video has its own README with recipes, expected output, and troubleshooting.

- [`simpler-rag`](simpler-rag/README.md)
- [`simpler-mcp`](simpler-mcp/README.md)

## Expected Output

### When Installing Dependencies

```
Resolved 205 packages in 20ms
Audited 160 packages in 23ms
```

### When Applying the First Schema File

The notebook prints a plan before it changes the catalog. For Recipe 1 in `simpler-rag`, that plan looks like this:

```
+ rag_demo/photos          create

Plan: 1 create, 0 update, 0 unchanged, 0 extra  |  0 destructive
```

## Using a Tutorial

Watch the video and run the matching notebook. For `simpler-rag`, you insert sample photos and try six retrieval recipes on one catalog.

If a cell fails because there is no project root, you are not in the video folder. `cd` into that folder and run it again.

## Data Structure

```
pixeltable-youtube/
  simpler-rag/
    README.md
    rag-is-simpler.ipynb
    recipe1_store.py
    recipe2_rewrite.py
    recipe3_caption.py
    recipe4_search.py
    recipe5_compare.py
    recipe5_cutover.py
    recipe6_answer.py
  simpler-mcp/
    README.md
    multimodal-mcps-are-simpler.ipynb
    recipe1_store.py
    recipe2_search.py
    recipe3_video.py
    recipe4_transcript.py
```

The local Pixeltable catalog is under `~/.pixeltable`. It is not stored in this repo.

## Troubleshooting

### Schema commands cannot find the project

`cd` into the video folder and run the notebook from there.

### The notebook kernel cannot import Pixeltable

Run `uv sync --package simpler-rag` from the repo root, then select the workspace `.venv` as the kernel.

### Duplicate rows after rerunning insert cells

In `simpler-rag`, uncomment the two reset lines in the last cell, run it, then run the notebook from the first recipe.

## Project Details

### Resources

- [Pixeltable on GitHub](https://github.com/pixeltable/pixeltable)
- [Pixeltable docs](https://docs.pixeltable.com/)
- [Pixeltable on YouTube](https://www.youtube.com/@PixeltableHQ)
- [`simpler-rag` README](simpler-rag/README.md)
- [`simpler-mcp` README](simpler-mcp/README.md)
