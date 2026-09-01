# pixeltable-youtube

Notebooks and schema files that go with Pixeltable YouTube videos. This is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/). Each video is a member in its own folder, with its own `pyproject.toml`. The repo shares one `uv.lock` at the root.

You need [uv](https://docs.astral.sh/uv/).

## Manage dependencies

Each video folder lists its own dependencies and accepted versions in its `pyproject.toml`. For example, `simpler-rag/pyproject.toml` requires Pixeltable 0.7.3 or newer.

The root `uv.lock` records the exact versions that uv installs. All workspace members share this lockfile and the root `.venv`, but each dependency still belongs to the member that declares it.

To add a dependency to one member:

```bash
uv add --package simpler-rag PACKAGE
```

To upgrade Pixeltable to the newest version allowed by `simpler-rag/pyproject.toml`:

```bash
uv lock --upgrade-package pixeltable
uv sync --package simpler-rag
```

The first command updates the Pixeltable version in the shared lockfile. It does not upgrade every package in the workspace. The second command installs the locked dependencies for `simpler-rag` in the shared environment.

When a new Pixeltable release becomes the minimum version for this project, update the member requirement too:

```bash
uv add --package simpler-rag "pixeltable>=0.7.3"
```

## Pixeltable project roots

Each video folder that contains Pixeltable schema files must also be a Pixeltable project root. Its `pyproject.toml` contains a `[[tool.pixeltable.database]]` section created by `pxt init`.

This configuration belongs in the video folder, not at the workspace root. Pixeltable records schema functions using module paths relative to that folder. After cloning the repo, the configuration is already present and you do not need to run `pxt init` again.

## Run a notebook

Open the notebook and run the first cell. That cell installs that folder's dependencies into the kernel with uv.

From the terminal:

```bash
uv sync --package simpler-rag
uv run --package simpler-rag jupyter lab
```

## Add a new video

From the repo root, `uv init` adds the folder as a workspace member.

```bash
uv init --bare --no-package --no-readme --name my-video my-video
uv add --package my-video pixeltable
cd my-video
uv run pxt init
```

Run `pxt init` from inside the new video folder. Put the notebook and any schema files in that folder. Commit the member `pyproject.toml` and the root `uv.lock`. Do not commit `.venv`.

## Projects

- [`simpler-rag`](simpler-rag/README.md): multimodal RAG that starts with image titles, adds CLIP retrieval, and answers from retrieved images
