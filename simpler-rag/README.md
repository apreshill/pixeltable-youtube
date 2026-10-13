# RAG Is Simpler Than You Think

Pixeltable is the database behind this multimodal RAG app. People ask questions in text. The evidence lives in images. The app inserts a question, and Pixeltable retrieves the right photos and has a vision model answer from them.

Photos, captions, embeddings, questions, and answers live in one Pixeltable database, `rag_demo`. The `queries` table is the app's backend: an app inserts a question and reads back the retrieved photos (`hits`) and the `answer`. Each recipe changes only how `hits` is computed. The answer step never changes. The notebook applies each recipe, re-answers the same questions, and ends by serving `queries` as an API.

The six recipe names and the idea come from Rafael Pierre's [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think) and Hugo Bowne-Anderson's account of Doug Turnbull's talk, [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)

## Overview

The six recipes go from simplest to most complex. Each one ends with the answers to the same questions, so you can see what it fixes. Add the next recipe only when the one before it misses a question you care about.

1. **The MVP: Full-Text Search Only.** `hits` is the photos whose title shares a word with the question.
2. **Agentic Query Rewriting.** An LLM turns the question into keywords, searches the titles, and tries broader keywords if nothing matched.
3. **Hybrid Search (Sparse + Dense Reranking).** Keyword matches from titles and BLIP captions, ranked by a CLIP image embedding.
4. **On-The-Fly Embedding (The Fresh Data Play).** New photos are captioned and indexed on insert, so they answer questions right away.
5. **Pre-Embedding with Hot/Cold Tiers.** `hits` searches only the photos marked hot. Promoting a photo is one `update`.
6. **Full Pre-Embedding (The Scale Play).** Every photo gets a newer CLIP model next to the old one. Compare them, drop the old index, and search every photo.

A bonus splits a question that asks for two things into two searches. The last section serves `queries` as `POST /ask`, so an app can send questions and read answers.

CLIP (Contrastive Language-Image Pretraining) maps text and images into the same space, so a text question can retrieve photos. Each recipe is a column, a query, or an index on the same tables. You do not stand up a vector store or an ingestion job for each recipe.

## Technical Architecture

1. **Pixeltable database (`rag_demo`)**
   - `photos`: the image, its title, and later a caption, a `hot` flag, and CLIP indexes
   - `queries`: one row per question, with computed `hits`, `answer`, and the columns each recipe adds
   - `hits` is a query column. Each recipe edits it in place, and `pxt recompute` re-runs it and the answer for the questions already stored.

2. **Schema files**
   - Each file is the full definition of the tables it declares
   - `rag_udfs.py`: keyword matching, the answer prompt, and merging two lists of photos
   - `recipe1_fulltext.py`: `photos`, and `queries` with `hits` from title words and an `answer`
   - `recipe2_agentic.py`: two LLM tries at keywords; `hits` searches the titles with them
   - `recipe3a_captions.py`: a BLIP `caption` and a CLIP index (`clip_idx`, ViT-B/32)
   - `recipe3b_hybrid.py`: `hits` becomes keyword matches from titles and captions, ranked by CLIP
   - Recipe 4 has no schema file. It inserts two photos and a question.
   - `recipe5a_tiers.py`: a `hot` column
   - `recipe5b_hot_search.py`: `hits` searches only the hot photos
   - `recipe6a_compare.py`: a second CLIP index (`clip_idx_v2`, ViT-B/16) for every photo
   - `recipe6b_cutover.py`: drops `clip_idx`; `hits` searches every photo with `clip_idx_v2`
   - `bonus_multi.py`: splits the question in two and combines the photos from both searches. It also declares the API route, `POST /ask`, so the same file serves the app

   Steps a and b are separate updates on purpose. Pixeltable 0.7.14 fails when one update adds a column or index to `photos` and also points `hits` at a search that uses it.

3. **Notebook (`rag-is-simpler.ipynb`)**
   - Resets `rag_demo`, then applies each schema file with `pxt schema diff` and `pxt schema update`
   - Inserts 14 photos and four questions, then two more photos and a fifth question in Recipe 4
   - Ends every recipe with the questions, their `hits`, and their answers

4. **Sample photo catalog**
   - JPEG files hosted in the Pixeltable repository
   - Each row has a `photo_id`, an image URL, and a short title

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)** for installing this folder's dependencies
- **Git** for cloning the repository
- **An OpenAI API key**

Every recipe answers with `gpt-4o-mini`, and Recipe 2 on also rewrites questions with it. BLIP and CLIP run locally.

Both the notebook and the `pxt` daemon call OpenAI. The daemon runs `pxt recompute`. The simplest way to give both of them the key is to put it in `~/.pixeltable/config.toml`:

```toml
[openai]
api_key = 'sk-...'
```

Then restart the daemon once from `simpler-rag/` with `uv run pxt daemon restart`.

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

That creates `simpler-rag/.venv` and installs Pixeltable 0.7.14 or newer, plus OpenAI, torch, transformers, and Jupyter.

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
4. If `hits` changed, re-run it for the stored questions with `pxt recompute rag_demo/queries hits -f`. The answers follow.
5. Show the questions, their `hits`, and their answers

### 6. Start Over

The cell after `uv sync` drops `rag_demo`, so running the notebook from the top always starts from empty tables. It drops `queries` first because that table searches `photos`.

## Expected Output

The four questions are `show me a zebra`, `any pets?`, `do you have a photo of the subway?`, and `anything with stripes?`. Recipe 4 adds `anything with an umbrella?`. The answers come from an LLM and vary from run to run. The photos in `hits` are what to check.

### Recipe 1

- `show me a zebra`: photos 6 and 13
- The other three: no photos, because `pets`, `subway`, and `stripes` are not in any title

### Recipe 2

- When the first keywords find nothing, the second try broadens them. Expect `any pets?` to reach `dog` (photo 7) and the subway question to reach `train` (photo 12). The exact keywords vary.

### Recipe 3

- Every photo gets a BLIP caption. Photo 4's caption calls the giraffe a "gife".
- The four questions find the same photos as in Recipe 2, now ranked by CLIP
- `anything in a field?`: the cow (photo 14) and the grazing zebra (photo 6). No title says field, but their captions do.

### Recipe 4

- `anything with an umbrella?`: photo 15, which has no title

### Recipe 5

- With photos 4, 6, 7, and 9 marked hot, every question gets the three closest hot photos, even when none fit. The subway question cannot reach the train.
- After marking photo 13 hot, the zebra and stripes questions include it

### Recipe 6

- `a pet` on `clip_idx` (ViT-B/32): the two zebras rank above the dog
- `a pet` on `clip_idx_v2` (ViT-B/16): the dog ranks first
- The diff for `recipe6b_cutover.py` marks the dropped `clip_idx` as `DESTRUCTIVE`
- After the cutover, `hits` holds the top 2 photos for each question from every photo

### Bonus

- One search for `show me flowers and a zebra` keeps the two zebras and misses the vase of flowers
- Split into two parts, its hits include the vase of flowers (photo 5) and the zebras (photos 13 and 6)

### Serve it as an app

- `POST /ask` with `is there a clock?` returns the street clock (photo 11) and an answer, and saves the question in `queries`

## Troubleshooting

### Schema commands cannot find the project

You ran the command from the wrong directory. `cd` into `simpler-rag` and run it again. Do not run `pxt init` at the repo root. `simpler-rag` is not a valid Python module name because of the hyphen.

### Keyword search returns no rows

`contains()` is case sensitive by default. The notebook passes `case=False` for titles.

### The cutover update is refused

Dropping an index destroys its data, so `pxt schema update` needs `--allow-destructive`. The notebook passes it for `recipe6b_cutover.py`.

### The update says stored values were not recomputed

That's expected when a recipe changes `hits`. Pixeltable keeps stored results, so it does not rerun model calls you already paid for. To re-answer the stored questions with the new search, run `pxt recompute rag_demo/queries hits -f`. It re-runs `hits` and the answer for those rows. Without `-f`, the command asks for confirmation, which a notebook cell cannot give.

### `pxt service update` says FastAPIRouter requires fastapi

The `pxt` daemon started before `pixeltable[serve]` was installed. Restart it once from `simpler-rag/` with `uv run pxt daemon restart`, then run the cell again.

### `pxt service update` says port 8000 is already in use

An API from an earlier run is still serving. Stop it from `simpler-rag/` with `uv run pxt service stop rag`, then run the cell again.

### Duplicate rows

`photo_id` is a primary key, so inserting the same photos twice fails with `Duplicate primary key` instead of adding copies. Run the notebook from the top: the reset cell starts it from empty tables.

### Answers are empty or the insert fails

The notebook or the `pxt` daemon cannot find your OpenAI key. Put it in `~/.pixeltable/config.toml` as shown in Prerequisites, then run `uv run pxt daemon restart` from `simpler-rag/` and restart the kernel.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from `simpler-rag/`, register the kernel (Setup step 3), then pick the `simpler-rag` kernel.

### `uv sync` warns that `VIRTUAL_ENV` does not match

Another virtual environment is active in the shell that started Jupyter or your editor. uv ignores it and uses `simpler-rag/.venv`, so the sync still works. To clear the warning, run `deactivate` or open a new terminal, then start Jupyter again from `simpler-rag/`.

### `!pxt` says command not found

The notebook's shell cannot see `simpler-rag/.venv/bin`. Start Jupyter with `uv run jupyter lab` from `simpler-rag/`. Selecting `.venv` as the kernel in an editor does not always put `.venv/bin` on the shell path.

### CLIP or BLIP runs out of memory

Close other large programs. These models load locally with `torch` and `transformers`. Recipes 5 and 6 load a second CLIP model.

## Data Structure

```
simpler-rag/
  rag-is-simpler.ipynb     # apply the recipes and see the answers
  pyproject.toml           # dependencies and Pixeltable project config
  uv.lock                  # pinned versions for this tutorial
  rag_udfs.py              # keyword matching, the answer prompt, merging photos
  recipe1_fulltext.py      # photos; queries with hits and answer
  recipe2_agentic.py       # queries: two keyword tries; hits searches titles
  recipe3a_captions.py     # photos: caption and clip_idx
  recipe3b_hybrid.py       # queries: hits from titles and captions, ranked by CLIP
  recipe5a_tiers.py        # photos: hot
  recipe5b_hot_search.py   # queries: hits from the hot photos only
  recipe6a_compare.py      # photos: clip_idx_v2 next to clip_idx
  recipe6b_cutover.py      # photos: drops clip_idx; queries: hits from every photo
  bonus_multi.py           # queries: split the question, search both parts; the POST /ask route
  images/                  # the notebook graphics: cold open, RAG steps, three knobs (sources in images/src)
```

The sample images load from:

```
https://raw.githubusercontent.com/pixeltable/pixeltable/main/docs/resources/images/
```

The local Pixeltable database is under `~/.pixeltable`.

## Extending the Database

### Adding Photos

Insert rows with a new `photo_id` and an image path or URL. The title is optional. Pixeltable fills the caption and every index for the new rows. Questions asked after that can retrieve them. Pixeltable keeps the stored answers for earlier questions, so it does not call the models again for them. Run `pxt recompute` if you want those questions to search the new photos too.

### Changing a Recipe

1. Edit the matching `recipe*.py` file
2. Run `pxt schema diff FILE rag_demo` and read the plan
3. Run `pxt schema update FILE rag_demo -f` if the plan is what you want
4. Reload the table in Python with `pxt.get_table(...)` so the notebook sees the change

## Project Details

### Dependencies

- Pixeltable 0.7.14 or newer, with the `serve` extra: tables, computed columns, query columns, embedding indexes, `pxt schema`, `pxt recompute`, and `pxt service`
- OpenAI: the answer in every recipe, question rewriting, and splitting
- transformers and torch: BLIP captions and CLIP embeddings
- JupyterLab, ipykernel, and ipywidgets: running the notebook

### Resources

- [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think)
- [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)
- [Pixeltable documentation](https://docs.pixeltable.com/)
- [CLIP](https://github.com/openai/CLIP)
- [uv projects](https://docs.astral.sh/uv/concepts/projects/)
