# RAG Is Simpler Than You Think

Pixeltable is the database for this multimodal RAG app. People ask questions in text. The evidence lives in images. You retrieve the right photos, then a vision model answers from them.

Photos, captions, embeddings, questions, and answers live in one Pixeltable database, `rag_demo`. Schema files declare the tables, computed columns, queries, and indexes. The database runs those columns on every row and every new insert, and it keeps the indexes current. The notebook applies each recipe and shows the results on a catalog of 14 photos, then two more.

The six recipe names and the idea come from Rafael Pierre's [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think) and Hugo Bowne-Anderson's account of Doug Turnbull's talk, [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)

## Overview

The six recipes go from simplest to most complex. Add the next one only when the one before it misses a question you care about.

1. **The MVP: Full-Text Search Only.** Keyword search on the titles that come with each photo.
2. **Agentic Query Rewriting.** An LLM turns each question into keywords, searches the titles, and tries broader keywords if nothing matched.
3. **Hybrid Search (Sparse + Dense Reranking).** Keyword candidates from BLIP captions, ranked by a CLIP image embedding.
4. **On-The-Fly Embedding (The Fresh Data Play).** New photos are searchable as soon as they are inserted. The index updates on insert, so it is never stale.
5. **Pre-Embedding with Hot/Cold Tiers.** The hot tier is a view of the most viewed photos with its own index on a newer model. Promoting a photo is one `update`.
6. **Full Pre-Embedding (The Scale Play).** Every photo gets the newer model next to the old one. Compare them, then drop the old index.

A bonus section splits a question with two requests into two searches and answers from the retrieved photos.

CLIP (Contrastive Language-Image Pretraining) maps text and images into the same space, so a text question can retrieve photos. Each recipe is a column, a query, an index, or a view on the same tables. You do not stand up a vector store or an ingestion job for each recipe.

## Technical Architecture

1. **Pixeltable database (`rag_demo`)**
   - Holds the `photos` and `queries` tables and the `hot_photos` view
   - Computed columns run on every existing row and every new insert
   - Query columns (`first_hits`, `title_hits`, `photos_1`, `photos_2`) search `photos` for each new question
   - Embedding indexes stay current as photos come in or change

2. **Schema files**
   - Each file is the full definition of the tables it declares
   - `recipe1_fulltext.py`: the `photos` table with a `photo_id` primary key, an image, and a title
   - `recipe2_agentic.py`: adds a `queries` table that rewrites each question, searches the titles, and retries once
   - `recipe3_hybrid.py`: adds a BLIP `caption` and a CLIP index (`clip_idx`, ViT-B/32)
   - Recipe 4 has no schema file. It inserts new photos and searches them.
   - `recipe5_tiers.py`: adds a `hot` column and a `hot_photos` view with its own index (`hot_idx`, ViT-B/16)
   - `recipe6_compare.py`: adds `clip_idx_v2` (ViT-B/16) for every photo
   - `recipe6_cutover.py`: keeps only `clip_idx_v2`
   - `bonus_answer.py`: adds `parts`, `photos_1`, `photos_2`, and a vision model `answer` to `queries`

3. **Notebook (`rag-is-simpler.ipynb`)**
   - Resets `rag_demo`, then applies each schema file with `pxt schema diff` and `pxt schema update`
   - Inserts 14 photos, then two more in Recipe 4
   - Runs one or two searches per recipe to show what it finds and what it misses

4. **Sample photo catalog**
   - JPEG files hosted in the Pixeltable repository
   - Each row has a `photo_id`, an image URL, and a short title

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)** for installing this folder's dependencies
- **Git** for cloning the repository
- **An OpenAI API key** for Recipe 2 and the bonus

Recipe 2 and the bonus call `gpt-4o-mini`. Set `OPENAI_API_KEY` where the `pxt` daemon runs before you apply Recipe 2. The other recipes run locally.

This folder is a Pixeltable project root. `simpler-rag/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

Each tutorial in this repo is its own uv project. `simpler-rag/pyproject.toml` lists the packages and `simpler-rag/uv.lock` pins their versions.

```bash
cd simpler-rag
uv sync
```

That creates `simpler-rag/.venv` and installs Pixeltable 0.7.11 or newer, plus OpenAI, torch, transformers, and Jupyter.

### 3. Register the Kernel

Register this folder's `.venv` as a Jupyter kernel named `simpler-rag`. The notebook is set to use it:

```bash
uv run python -m ipykernel install --user --name simpler-rag --display-name simpler-rag
```

### 4. Open the Notebook

Run the notebook with this folder as the working directory. The `pxt schema` cells look for the recipe files next to the notebook.

```bash
uv run jupyter lab
```

Open `rag-is-simpler.ipynb`. In Jupyter, Cursor, or VS Code, pick the `simpler-rag` kernel.

### 5. Run the Recipes

Run the notebook from top to bottom. Each recipe follows the same pattern:

1. Print the schema file
2. Preview the change with `pxt schema diff FILE rag_demo`
3. Apply the change with `pxt schema update FILE rag_demo -f`
4. Run a search that shows what the recipe finds and what it misses

### 6. Start Over

The cell after `uv sync` drops `rag_demo`, so running the notebook from the top always starts from empty tables. It drops `queries` first because that table searches `photos`.

## Expected Output

### Recipe 1

- `zebra` in titles: photos 6 and 13
- `puppy` in titles: no rows, because photo 7's title calls it a dog

### Recipe 2

- When the first keywords find nothing, the second try broadens them. `any puppies?` ends with keywords that include `dog` and finds photo 7. `do you have a photo of the subway?` ends with keywords that include `train` and finds photo 12.

The exact keywords can vary.

### Recipe 3

- `a striped animal`: photos 6 and 13 rank first
- Captions that contain `riding`, ranked by `a jungle`: photo 10 (elephant trek) above photo 8 (horse riders)

### Recipe 4

- After inserting photos 15 and 16 without titles, `an umbrella` ranks photo 15 first

### Recipe 5

- With photos 4, 6, 7, and 9 marked hot, `a striped animal` in the hot tier ranks photo 6 first
- After marking photo 13 hot, it ranks second in the hot tier

### Recipe 6

- `a pet` on `clip_idx` (ViT-B/32): the two zebras rank above the dog
- `a pet` on `clip_idx_v2` (ViT-B/16): the dog ranks first
- The diff for `recipe6_cutover.py` marks the dropped `clip_idx` as `DESTRUCTIVE`

### Bonus

- `show me a zebra and something to eat` splits into two requests, retrieves two photos for each, and the answer cites the photo IDs

## Troubleshooting

### Schema commands cannot find the project

You ran the command from the wrong directory. `cd` into `simpler-rag` and run it again. Do not run `pxt init` at the repo root. `simpler-rag` is not a valid Python module name because of the hyphen.

### Keyword search returns no rows

`contains()` is case sensitive by default. The notebook passes `case=False` for titles.

### The cutover update is refused

Dropping an index destroys its data, so `pxt schema update` needs `--allow-destructive`. The notebook passes it for `recipe6_cutover.py`.

### Duplicate rows

`photo_id` is a primary key, so inserting the same photos twice fails with `Duplicate primary key` instead of adding copies. Run the notebook from the top: the reset cell starts it from empty tables.

### Recipe 2 or the bonus fails

Set `OPENAI_API_KEY` in the environment where the `pxt` daemon runs. Restart the daemon if you set the key after it started.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from `simpler-rag/`, register the kernel (Setup step 3), then pick the `simpler-rag` kernel.

### `uv sync` warns that `VIRTUAL_ENV` does not match

Another virtual environment is active in the shell that started Jupyter or your editor. uv ignores it and uses `simpler-rag/.venv`, so the sync still works. To clear the warning, run `deactivate` or open a new terminal, then start Jupyter again from `simpler-rag/`.

### `!pxt` says command not found

The notebook's shell cannot see `simpler-rag/.venv`. Start Jupyter with `uv run jupyter lab` from `simpler-rag/`, or select `simpler-rag/.venv` as the kernel in your editor.

### CLIP or BLIP runs out of memory

Close other large programs. These models load locally with `torch` and `transformers`. Recipes 5 and 6 load a second CLIP model.

## Data Structure

```
simpler-rag/
  rag-is-simpler.ipynb   # apply the recipes and inspect results
  pyproject.toml         # dependencies and Pixeltable project config
  uv.lock                # pinned versions for this tutorial
  recipe1_fulltext.py    # photos: photo_id, image, title
  recipe2_agentic.py     # queries: raw, first_keywords, first_hits, keywords, title_hits
  recipe3_hybrid.py      # photos: adds caption and clip_idx
  recipe5_tiers.py       # photos: adds hot; hot_photos view with hot_idx
  recipe6_compare.py     # photos: adds clip_idx_v2
  recipe6_cutover.py     # photos: drops clip_idx
  bonus_answer.py        # queries: adds parts, photos_1, photos_2, answer
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

- Pixeltable 0.7.11 or newer: tables, views, computed columns, query columns, embedding indexes, and `pxt schema`
- OpenAI: question rewriting, splitting, and the vision model answer
- transformers and torch: BLIP captions and CLIP embeddings
- JupyterLab, ipykernel, and ipywidgets: running the notebook

### Resources

- [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think)
- [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)
- [Pixeltable documentation](https://docs.pixeltable.com/)
- [CLIP](https://github.com/openai/CLIP)
- [uv projects](https://docs.astral.sh/uv/concepts/projects/)
