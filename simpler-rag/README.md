# RAG Is Simpler Than You Think

Pixeltable is the database for this multimodal RAG app. People ask questions in text. The evidence lives in images. You retrieve the right photos, then a vision model answers from them.

Photos, captions, embeddings, rewritten queries, and answers live in one Pixeltable database, `rag_demo`. Schema files declare the tables, computed columns, and indexes. The database runs those columns on every row and every new insert, and it keeps the indexes current. The notebook is how you apply each recipe and inspect the results on a catalog of 14 photos.

## Overview

You can try six retrieval recipes on the same photos:

- Search photos by words that already appear in their titles
- Generate a caption for every photo and search that caption
- Search the image content itself when the question uses different words
- Compare two CLIP embedding models on the same question
- Rewrite a vague question into a short search query
- Give the retrieved photos to a vision model and answer from that evidence

CLIP (Contrastive Language-Image Pretraining) maps text and images into the same space, so a text question can retrieve photos. Trying another retrieval method is another column or index on the same tables. You do not stand up a vector store or an ingestion job for each recipe.

This is an OLTP app. You insert photos, query them, and derive AI outputs from that data. It is not a warehouse for batch analytics.

This tutorial was inspired by Rafael Pierre's [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think) and Hugo Bowne-Anderson's account of Doug Turnbull's talk, [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)

## Technical Architecture

The database is the app. Everything else declares it, fills it, or queries it.

1. **Pixeltable database (`rag_demo`)**
   - Holds the `photos`, `queries`, and `answers` tables
   - Computed columns run on every existing row and every new insert
   - Embedding indexes stay current as photos come in
   - Adding a second CLIP index does not overwrite the first, so you can compare models

2. **Schema files (`recipe1_store.py` through `recipe6_answer.py`)**
   - Each file is the full table definition for that recipe
   - Recipe 1 stores each photo with a title and a lowercase `search_title`
   - Recipe 2 adds a BLIP caption as a computed column
   - Recipe 3 adds a CLIP index on the image
   - Recipe 4 adds a second CLIP index so you can compare models
   - Recipe 5 adds a `queries` table that rewrites a question
   - Recipe 6 adds an `answers` table that calls a vision model on three retrieved photos

3. **Notebook (`rag-is-simpler.ipynb`)**
   - Applies each schema file with `pxt schema diff` and `pxt schema update`
   - Inserts a catalog of 14 photos
   - Runs keyword search, CLIP search, reranking, query rewriting, and answers from retrieved photos

4. **Sample photo catalog**
   - 14 JPEG files hosted in the Pixeltable repository
   - Each row has a `photo_id`, an image URL, and a short title
   - Two zebra photos (`Zebra grazing` and `Zebra in an enclosure`) are the main comparison case

## Prerequisites

Before you begin, you need:

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)** for installing this folder's dependencies
- **Git** for cloning the repository
- **An OpenAI API key** if you run Recipe 5 or Recipe 6

Recipes 1 through 4 run locally. Recipe 5 rewrites questions with `gpt-4o-mini`. Recipe 6 answers from retrieved images with `gpt-4o-mini`. Set `OPENAI_API_KEY` where the `pxt` daemon runs before those cells.

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

That installs Pixeltable 0.7.3 or newer, plus OpenAI, sentence-transformers, torch, transformers, and Jupyter.

### 3. Open the Notebook

The notebook must run with this folder as the working directory. The `pxt schema` cells look for `recipe1_store.py` and the other schema files next to the notebook.

```bash
cd simpler-rag
uv run --package simpler-rag jupyter lab
```

Open `rag-is-simpler.ipynb`. Select the `pixeltable-youtube` kernel if Jupyter offers it.

You can also open the notebook in Cursor or VS Code and run the first cell:

```python
!uv sync --package simpler-rag
```

### 4. Run the Recipes

Run the notebook from top to bottom.

Each recipe follows the same pattern:

1. Read the schema file
2. Preview the change with `pxt schema diff FILE rag_demo`
3. Apply the change with `pxt schema update FILE rag_demo -f`
4. Run a question that shows what that recipe can do

You can stop after any recipe if the results are good enough.

### 5. Start Over

The last cell resets the demo database. Uncomment it and run it, then run the notebook again:

```python
pxt.drop_dir('rag_demo', force=True)
```

## Expected Output

### When Installing Dependencies

```
Resolved 189 packages in 19ms
Audited 160 packages in 24ms
```

### When Applying Recipe 1

```
+ rag_demo/photos          create

Plan: 1 create, 0 update, 0 unchanged, 0 extra  |  0 destructive
```

After the insert cell, you should see 14 rows inserted.

### When Searching Titles for `zebra`

Two photos should appear:

```
photo_id  title
6         Zebra grazing
13        Zebra in an enclosure
```

### When Searching Titles for `striped`

The result table should have no rows. Two photos fit the question, but neither title uses that word.

### When Searching Images for `a striped animal`

CLIP should rank the two zebra photos first. The table shows each photo, its title, its caption, and a similarity score.

## Using the Application

### Recipe 1: Search Titles

1. Apply `recipe1_store.py`
2. Insert the 14 sample photos
3. Search `search_title` for `zebra`

`search_title` is a lowercase copy of `title`, so `zebra` matches `Zebra grazing`.

**Example output:**

```
Searching titles for: "zebra"

Results:
1. Photo ID: 6
   Title: Zebra grazing
2. Photo ID: 13
   Title: Zebra in an enclosure
```

### Recipe 2: Search Captions

1. Apply `recipe2_caption.py`
2. Reload the table so Python can see the new `caption` column
3. Search captions for `striped`

BLIP is a computed column. The database runs it on every image and stores the caption. Those captions still use the word `zebra`, not `striped`, so this keyword search still returns no rows.

### Recipe 3: Search Image Content

1. Apply `recipe3_search.py`
2. Reload the table so Python can see the CLIP index
3. Search with `photos.image.similarity(string='a striped animal', idx='clip_idx')`

The question is text. The embedding index is on the image column, like any other index the database keeps current. There is nothing to split into chunks because each photo is one item.

A later cell reranks a CLIP shortlist with a cross-encoder on the captions.

### Recipe 4: Compare Embedding Models

1. Apply `recipe4_migrate.py`
2. Run the same question, `public transportation`, against `clip_idx` (ViT-B/32) and `clip_idx_v2` (ViT-B/16)
3. Insert two new photos and confirm Pixeltable fills both indexes for them

Adding the second index does not remove the first. Both stay, so you can compare results and keep the model that works better.

### Recipe 5: Rewrite the Question

1. Set `OPENAI_API_KEY`
2. Apply `recipe5_rewrite.py`
3. Insert a vague question such as `what are the big animals with really long necks?`
4. Search the photos with the rewritten query

**Example output:**

```
Raw question: what are the big animals with really long necks?
Search query: giraffe
```

The exact rewrite can vary. The next cell searches CLIP with that rewritten string and shows the top three photos.

### Recipe 6: Answer from Retrieved Images

1. Apply `recipe6_answer.py`
2. Build source notes from the retrieved photo IDs, titles, and captions
3. Insert those three images into the `answers` table

The vision model answers only from the supplied images and source notes. It cites the photo IDs that support the answer.

## Testing and Verification

There is no separate test suite. Use the notebook's comparison questions, and use `pxt schema diff` before each update.

From this folder:

```bash
# Confirm this folder is the Pixeltable project root
uv run --package simpler-rag pxt init --json

# Preview Recipe 1 against an empty rag_demo directory
uv run --package simpler-rag pxt schema diff recipe1_store.py rag_demo
```

`pxt init --json` should report this folder as the project root. If you already applied Recipe 1, the diff shows what would change on the live tables rather than a create plan.

In the notebook, confirm:

- `zebra` on `search_title` returns photo IDs 6 and 13
- `striped` on `search_title` returns no rows
- `a striped animal` on CLIP ranks those zebra photos first

## Data Structure

This folder uses this file layout:

```
simpler-rag/
  rag-is-simpler.ipynb   # apply the recipes and inspect results
  pyproject.toml         # dependencies and Pixeltable project config
  recipe1_store.py       # photos table: photo_id, image, title, search_title
  recipe2_caption.py     # adds caption
  recipe3_search.py      # adds clip_idx on image
  recipe4_migrate.py     # adds clip_idx_v2 on image
  recipe5_rewrite.py     # queries table: raw question and search_query
  recipe6_answer.py      # answers table: question, notes, three images, answer
```

The sample images are not stored in this folder. The insert cell loads them from:

```
https://raw.githubusercontent.com/pixeltable/pixeltable/main/docs/resources/images/
```

The local Pixeltable database is under `~/.pixeltable`.

## Troubleshooting

### Schema commands cannot find the project

If `pxt schema diff` reports that there is no project root, you ran the command from the wrong directory. `cd` into `simpler-rag` and run it again. Do not run `pxt init` at the repo root. Pixeltable records module paths relative to the project root, and `simpler-rag` is not a valid Python module name because of the hyphen.

### Keyword search for `zebra` returns no rows

`contains()` is case sensitive. Search `search_title`, not `title`. `search_title` is the lowercase column from Recipe 1. If that column is missing, apply `recipe1_store.py` again from the top after resetting `rag_demo`.

### Duplicate zebra rows

The insert cell appends rows. If you run it twice, every photo appears twice. Uncomment `pxt.drop_dir('rag_demo', force=True)`, run it, then run the notebook from the first recipe.

### Recipe 5 or Recipe 6 fails

Set `OPENAI_API_KEY` in the environment where the `pxt` daemon runs. Restart the daemon if you set the key after it started.

### The notebook kernel cannot import Pixeltable

Run `uv sync --package simpler-rag` from the repo, then select the workspace environment as the kernel. The first notebook cell runs that sync command.

### CLIP or BLIP runs out of memory

Close other large programs. These models load locally with `torch` and `transformers`. Recipe 4 loads a second CLIP model, so it uses more memory than Recipe 3.

## Extending the Database

### Adding New Photos

To add photos to the same catalog:

1. Insert rows with a new `photo_id`, an image path or URL, and a title
2. Pixeltable fills `search_title` from the title
3. If you already applied later recipes, Pixeltable also fills `caption` and both CLIP indexes

The notebook shows this after Recipe 4 with two extra photos.

### Changing a Recipe

To change the table layout:

1. Edit the matching `recipeN_*.py` file
2. Run `pxt schema diff FILE rag_demo` and read the plan
3. Run `pxt schema update FILE rag_demo` if the plan is what you want
4. Reload the table in Python with `pxt.get_table('rag_demo.photos')` so the notebook sees the new columns

Keep `search_title`, `caption`, and the CLIP indexes in later recipe files if those recipes still need them. Each schema file is the full table as of that recipe, not a patch.

## Project Details

### Dependencies

- Pixeltable 0.7.3 or newer. Tables, computed columns, embedding indexes, and `pxt schema`
- OpenAI. Query rewriting and the vision model answer
- transformers and torch. BLIP captions and CLIP embeddings
- sentence-transformers. Cross-encoder reranking
- JupyterLab and ipykernel. Running the notebook

### Resources

- [RAG Is Simpler Than You Think](https://www.lighthousenewsletter.com/p/rag-is-simpler-than-you-think)
- [RAG Isn't Dead. It's Sleeping.](https://www.vanishinggradients.com/p/rag-isnt-dead-its-sleeping)
- [Pixeltable documentation](https://docs.pixeltable.com/)
- [CLIP](https://github.com/openai/CLIP)
- [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)
