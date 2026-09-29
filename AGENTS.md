# AGENTS.md

Instructions for coding agents working in this repo.

This repo is the local code for Pixeltable YouTube tutorials. People clone it to run a video's notebook on their machine.

Pixeltable is an OLTP database. The catalog is the durable thing. The notebook, the Python SDK, the `pxt` CLI, and `pxt dashboard` are surfaces for the same catalog.

If you are adding a new tutorial folder, also read `AGENTS.producer.md`.

## Layout

One folder per video. That folder is the Pixeltable project root.

```
simpler-rag/     RAG Is Simpler Than You Think
```

Each video folder has:

- `README.md` for people running that tutorial
- a notebook
- schema files (`recipe*.py`)
- `pyproject.toml` with dependencies and `[[tool.pixeltable.database]]`

Each video folder is its own uv project with its own `uv.lock` and `.venv`. There is no Python project at the repo root, so tutorials can pin different dependency versions.

## Run a tutorial

Work from the video folder so `pxt schema` can find the schema files:

```bash
cd simpler-rag
uv sync
uv run jupyter lab
```

The first notebook cell is `!uv sync`. Each notebook's kernel is a named kernel for that folder's `.venv` (`simpler-rag`, `simpler-mcp`). Register it once with `uv run python -m ipykernel install --user --name <folder>`.

## Schema and catalog

Apply schema from the video folder:

```bash
pxt schema diff recipe1_fulltext.py rag_demo
pxt schema update recipe1_fulltext.py rag_demo
```

After a schema change, reload tables in Python with `pxt.get_table(...)`.

The local catalog is under `~/.pixeltable`. It is not in this repo.

Do not run `pxt init` at the repo root. A hyphenated folder name such as `simpler-rag` is not a valid Python module path from the root.

## Pixeltable skill, pixeltable-new, and the starter kit

This repo teaches with notebooks. When the user wants to write Pixeltable code, extend a tutorial into an app, or start a new Pixeltable project, do not invent a stack. Use the official tools.

1. **Pixeltable skill.** Read and follow [pixeltable-skill](https://github.com/pixeltable/pixeltable-skill) before writing tables, computed columns, indexes, views, or `pxt` commands. If the skill is installed locally, open that `SKILL.md` first. Computed columns run on insert. Embedding indexes live on the table. Do not add LangChain, a separate vector database, or pandas as the store.

2. **pixeltable-new.** Scaffold a new app with `uvx pixeltable-new`. Run `uvx pixeltable-new --list` and pick a name from that list. Do not guess template slugs.

   ```bash
   uvx pixeltable-new --list
   uvx pixeltable-new --template knowledge-base my-kb
   ```

   Create the new app in a fresh directory. `pixeltable-new` refuses to overwrite an existing folder. Do not scaffold into a tutorial folder in this repo unless the user asks for that.

3. **Starter kit.** Templates come from the [Pixeltable starter kit](https://github.com/pixeltable/pixeltable-starter-kit). After `pixeltable-new` prints next steps, follow those. Typical path: `uv sync`, apply schema with `pxt schema update`, then serve or run as the template says.

These videos are one catalog plus a notebook. A starter-kit app is a different project. Keep them separate unless the user wants them joined.

## Do not

- Do not add a new video folder unless the user asks. See `AGENTS.producer.md`.
- Do not put maintainer setup (`uv init`, `uv add`, `pxt init`) in the root README. That README is for people running a tutorial.
- Do not commit `.venv` or `.env`.
- Do not invent Pixeltable as a framework, backend, or data layer. It is a database.

## Troubleshooting

- `there is no project root`: the shell or notebook cwd is not the video folder.
- Empty keyword matches on titles: `contains()` is case sensitive by default. Pass `case=False`.
- `Duplicate primary key` on insert: the insert cell ran twice. Run the notebook from the top; its reset cell drops the demo directory.

## Read first

1. `README.md`
2. The video folder's `README.md`
3. The notebook and schema files in that folder
