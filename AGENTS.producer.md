# AGENTS.producer.md

Instructions for coding agents adding or changing tutorials in this repo. The user who maintains this repo is producing videos. The root `README.md` and `AGENTS.md` stay aimed at people running those videos.

Read `AGENTS.md` first.

## Add a new tutorial

From the repo root:

```bash
uv init --bare --no-package --no-readme --name my-tutorial my-tutorial
uv add --package my-tutorial "pixeltable>=0.7.3"
cd my-tutorial
uv run --package my-tutorial pxt init
```

`uv init` adds the folder as a workspace member. `pxt init` writes `[[tool.pixeltable.database]]` into that folder's `pyproject.toml`. Run `pxt init` inside the new folder, never at the repo root.

Put in the folder:

- a consumer `README.md`
- a notebook whose first cell is `!uv sync --package my-tutorial`
- schema files next to the notebook
- any extra dependencies with `uv add --package my-tutorial PACKAGE`

Commit the member `pyproject.toml` and the root `uv.lock`. Do not commit `.venv`.

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

The member `pyproject.toml` owns the version range. The root `uv.lock` records the resolved version.

```bash
uv add --package my-tutorial PACKAGE
uv lock --upgrade-package pixeltable
uv sync --package my-tutorial
```

## Notebook

Run it with the video folder as the working directory. After schema updates, call `pxt.get_table` again.

Insert cells append. Include a commented reset such as `pxt.drop_dir('demo_name', force=True)`.

## Cursor settings

`.vscode/settings.json` points at the workspace `.venv`. Commit it. It is a project setting, not a personal editor preference.
