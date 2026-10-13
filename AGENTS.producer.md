# AGENTS.producer.md

Instructions for coding agents adding or changing tutorials in this repo. The user who maintains this repo is producing videos. The root `README.md` and `AGENTS.md` stay aimed at people running those videos.

Read `AGENTS.md` first.

## Add a new tutorial

From the repo root:

```bash
uv init --bare --no-package --no-readme --name my-tutorial my-tutorial
cd my-tutorial
uv add "pixeltable>=0.7.14"
uv run pxt init
```

The folder is a standalone uv project, not a workspace member. Do not add a `pyproject.toml` or `uv.lock` at the repo root. `pxt init` writes `[[tool.pixeltable.database]]` into that folder's `pyproject.toml`. Run `pxt init` inside the new folder, never at the repo root.

Put in the folder:

- a consumer `README.md`
- a notebook whose first cell is `!uv sync` and whose kernelspec is a kernel named after the folder, registered with `uv run python -m ipykernel install --user --name my-tutorial`
- schema files next to the notebook
- any extra dependencies with `uv add PACKAGE`, run inside the folder

Commit the folder's `pyproject.toml` and `uv.lock`. Do not commit `.venv`.

Point the root README's project list at the new folder README.

## Folder names

Prefer names that are valid Python identifiers if schema files will be imported as modules (`simpler_rag`). A hyphen (`simpler-rag`) is fine as a folder name only if that folder is the Pixeltable project root. Do not make the repo root the project root when a member folder has a hyphen.

## Imports

Always import Pixeltable functions as `pxtf`:

```python
import pixeltable as pxt
import pixeltable.functions as pxtf
```

Use `pxtf.huggingface...`, `pxtf.openai...`, and the same prefix for every provider. Do not write `from pixeltable.functions.huggingface import ...` or any other `from pixeltable.functions...` import.

## Schema files

Each recipe is a full table definition, not a patch. Later files repeat earlier columns and indexes they still need.

After Pixeltable 0.7.3, do not add `from __future__ import annotations`.

Show `pxt schema diff` before `pxt schema update` in the notebook.

## Consumer README

Write a README in the new folder for people watching the video. Use the same layout as `simpler-rag/README.md`: overview, architecture, prerequisites, setup, expected output, how to run the recipes, file layout, troubleshooting.

Do not document `uv init` or "add a new video" there.

Pixeltable is the database. Schema files declare tables. The notebook is one surface for applying and inspecting them.

## Dependencies

Each folder's `pyproject.toml` owns the version range. Its `uv.lock` records the resolved versions. Run these inside the folder:

```bash
uv add PACKAGE
uv lock --upgrade-package pixeltable
uv sync
```

Upgrading one tutorial does not change the others.

## Notebook

Run it with the video folder as the working directory. After schema updates, call `pxt.get_table` again.

Insert cells append. Include a commented reset such as `pxt.drop_dir('demo_name', force=True)`.

## Cursor settings

`.vscode/settings.json` turns off environment activation in the terminal. Commit it. `uv run` and `uv sync` find each tutorial's `.venv` on their own, and an activated environment from another folder sets a stale `VIRTUAL_ENV`.
