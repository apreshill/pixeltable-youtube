# RAG Is Simpler Than You Think

Pixeltable is the database for this multimodal RAG app. People ask questions in text. The evidence lives in images. You retrieve the right photos, then a vision model answers from them.

Photos, captions, embeddings, questions, and answers live in one Pixeltable database, `rag_demo`. Schema files declare the tables, computed columns, queries, and indexes. The database runs those columns on every row and every new insert, and it keeps the indexes current. The notebook applies each recipe and shows the results on a catalog of 14 photos.

This tutorial was inspired by Rafael Pierre's [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think) and Hugo Bowne-Anderson's account of Doug Turnbull's talk, [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)

## Overview

The six recipes go from cheapest to most complex. Add the next one only when the one before it misses a question you care about.

1. Search the titles that come with each photo
2. Rewrite a vague question into one search word, then search the titles
3. Generate a caption for every photo and search the captions
4. Search the image content with a CLIP embedding index
5. Add a second embedding model, compare the two, and drop the old one
6. Retrieve three photos for each question and answer from them

CLIP (Contrastive Language-Image Pretraining) maps text and images into the same space, so a text question can retrieve photos. Each recipe is another column, query, or index on the same tables. You do not stand up a vector store or an ingestion job for each recipe.

## Technical Architecture

1. **Pixeltable database (`rag_demo`)**
   - Holds the `photos` and `queries` tables
   - Computed columns run on every existing row and every new insert
   - Query columns (`title_hits`, `photo_hits`) search `photos` for each new question
   - Embedding indexes stay current as photos come in

2. **Schema files**
   - Each file is the full definition of the tables it declares
   - `recipe1_store.py`: the `photos` table with a `photo_id`, an image, and a title
   - `recipe2_rewrite.py`: adds a `queries` table that rewrites each question and searches the titles
   - `recipe3_caption.py`: adds a BLIP caption as a computed column
   - `recipe4_search.py`: adds a CLIP index on the image (`clip_idx`, ViT-B/32)
   - `recipe5_compare.py`: adds a second CLIP index (`clip_idx_v2`, ViT-B/16)
   - `recipe5_cutover.py`: keeps only `clip_idx_v2`
   - `recipe6_answer.py`: adds `photo_hits` and a vision model `answer` to `queries`

3. **Notebook (`rag-is-simpler.ipynb`)**
   - Applies each schema file with `pxt schema diff` and `pxt schema update`
   - Inserts 14 photos, then two more in Recipe 5
   - Runs one or two searches per recipe to show what it finds and what it misses

4. **Sample photo catalog**
   - JPEG files hosted in the Pixeltable repository
   - Each row has a `photo_id`, an image URL, and a short title

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)** for installing this folder's dependencies
- **Git** for cloning the repository
- **An OpenAI API key** for Recipe 2 and Recipe 6

Recipes 2 and 6 call `gpt-4o-mini`. Set `OPENAI_API_KEY` where the `pxt` daemon runs before you apply Recipe 2. The other recipes run locally.

This folder is a Pixeltable project root. `simpler-rag/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

This repo is a uv workspace. `simpler-rag` lists its packages in `simpler-rag/pyproject.toml`. The shared lockfile is `uv.lock` at the repo root.

From the repo root:

```bash
uv sync --package simpler-rag
```

That installs Pixeltable 0.7.11 or newer, plus OpenAI, torch, transformers, and Jupyter.

### 3. Open the Notebook

Run the notebook with this folder as the working directory. The `pxt schema` cells look for the recipe files next to the notebook.

```bash
cd simpler-rag
uv run --package simpler-rag jupyter lab
```

Open `rag-is-simpler.ipynb`. You can also open it in Cursor or VS Code and select the workspace `.venv` as the kernel.

### 4. Run the Recipes

Run the notebook from top to bottom. Each recipe follows the same pattern:

1. Print the schema file
2. Preview the change with `pxt schema diff FILE rag_demo`
3. Apply the change with `pxt schema update FILE rag_demo -f`
4. Run a search that shows what the recipe finds and what it misses

### 5. Start Over

The last cell resets the demo database. Uncomment both lines and run it, then run the notebook again. It drops `queries` first because that table queries `photos`.

## Expected Output

### Recipe 1

- `zebra` in titles: photos 6 and 13
- `long neck` in titles: no rows

### Recipe 2

- `what are the big animals with really long necks?` is rewritten to `giraffe`
- `title_hits` holds photo 4, `Giraffe at the zoo`

The exact rewrite can vary.

### Recipe 3

- `field` in captions: photos 6 (`Zebra grazing`) and 14 (`Cow in a pasture`)
- `giraffe` in captions: no rows, because BLIP captions photo 4 as `a gife standing on a rock`

### Recipe 4

- `a striped animal`: photos 6 and 13 rank first
- Captions that contain `riding`, ranked by `a jungle`: photo 10 (elephant trek) above photo 8 (horse riders)

### Recipe 5

- `a racket sport` on `clip_idx`: the dog photo ranks just above the tennis match
- `a racket sport` on `clip_idx_v2`: the tennis match ranks first
- After inserting photos 15 and 16, `an umbrella` on `clip_idx_v2` ranks photo 15 first
- The diff for `recipe5_cutover.py` marks the dropped `clip_idx` as `DESTRUCTIVE`

### Recipe 6

- The Recipe 2 question gets `photo_hits` and an `answer` without a new insert
- A new question runs the whole chain on insert

## Troubleshooting

### Schema commands cannot find the project

You ran the command from the wrong directory. `cd` into `simpler-rag` and run it again. Do not run `pxt init` at the repo root. `simpler-rag` is not a valid Python module name because of the hyphen.

### Keyword search returns no rows

`contains()` is case sensitive by default. The notebook passes `case=False` for titles.

### The cutover update is refused

Dropping an index destroys its data, so `pxt schema update` needs `--allow-destructive`. The notebook passes it for `recipe5_cutover.py`.

### Duplicate rows

The insert cell appends rows. If you run it twice, every photo appears twice. Reset with the last cell, then run the notebook from the first recipe.

### Recipe 2 or Recipe 6 fails

Set `OPENAI_API_KEY` in the environment where the `pxt` daemon runs. Restart the daemon if you set the key after it started.

### The notebook kernel cannot import Pixeltable

Run `uv sync --package simpler-rag` from the repo root, then select the workspace environment as the kernel.

### CLIP or BLIP runs out of memory

Close other large programs. These models load locally with `torch` and `transformers`. Recipe 5 loads a second CLIP model.

## Data Structure

```
simpler-rag/
  rag-is-simpler.ipynb   # apply the recipes and inspect results
  pyproject.toml         # dependencies and Pixeltable project config
  recipe1_store.py       # photos: photo_id, image, title
  recipe2_rewrite.py     # queries: raw, search_query, title_hits
  recipe3_caption.py     # photos: adds caption
  recipe4_search.py      # photos: adds clip_idx
  recipe5_compare.py     # photos: adds clip_idx_v2
  recipe5_cutover.py     # photos: drops clip_idx
  recipe6_answer.py      # queries: adds photo_hits and answer
```

The sample images load from:

```
https://raw.githubusercontent.com/pixeltable/pixeltable/main/docs/resources/images/
```

The local Pixeltable database is under `~/.pixeltable`.

## Extending the Database

### Adding Photos

Insert rows with a new `photo_id` and an image path or URL. The title is optional. Pixeltable fills the caption and every index for the new rows.

### Changing a Recipe

1. Edit the matching `recipe*.py` file
2. Run `pxt schema diff FILE rag_demo` and read the plan
3. Run `pxt schema update FILE rag_demo -f` if the plan is what you want
4. Reload the table in Python with `pxt.get_table(...)` so the notebook sees the change

## Project Details

### Dependencies

- Pixeltable 0.7.11 or newer: tables, computed columns, query columns, embedding indexes, and `pxt schema`
- OpenAI: question rewriting and the vision model answer
- transformers and torch: BLIP captions and CLIP embeddings
- JupyterLab, ipykernel, and ipywidgets: running the notebook

### Resources

- [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think)
- [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)
- [Pixeltable documentation](https://docs.pixeltable.com/)
- [CLIP](https://github.com/openai/CLIP)
- [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)
