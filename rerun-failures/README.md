# Rerun only the failures

This notebook runs 1,673 photos through one Pixeltable table. 59 photos fail, for three different reasons. The run keeps going past every failure, saves each error on its row, and then reruns only the photos that failed.

It answers two questions from people running big image jobs. If a run stops partway, is the whole batch lost? And can you rerun only the cells that failed?

## Overview

1. A default insert stops at the first failed photo and saves none of the batch.
2. `on_error='ignore'`, with photos inserted 200 at a time, keeps going past failures. If the run stops, the chunks that finished stay saved.
3. `avg_color.errortype` and `avg_color.errormsg` show which photos failed and why. `pxt errors` lists the same failures from the command line.
4. `recompute_columns('avg_color', errors_only=True)` reruns only the failed rows, along with the columns built on them.

| Failure | Photos | Fix |
|---|---|---|
| Timeout | 30 (about 1 in 50) | retry with `errors_only=True` |
| Grayscale photo | 28 | change the column in `schema_rgb.py`, then retry with `errors_only=True` |
| Not an image | 1 | delete the row, or `update` it with a good file |

## Technical Architecture

1. **Pixeltable database (`rerun_demo`)**
   - `photos`: one row per photo. You insert `name` and `image`. Pixeltable computes `avg_color` and `color`.

2. **Schema files**
   - `schema.py` declares `photos`.
   - `schema_rgb.py` is the same table with one change: each photo is converted to RGB before `average_color` runs.
   - `udfs.py` holds `average_color` and `color_name`.

3. **Notebook (`rerun-failures.ipynb`)**
   - Resets `rerun_demo`, applies `schema.py`, inserts the photos, and fixes each kind of failure.

`average_color` stands in for a model call, so the notebook needs no API key. It is the one demo-only part: it raises `TimeoutError` the first time it sees about 1 photo in 50, the way a busy model API does. To use a real model, replace the body of `average_color`, and the rest of the notebook stays the same.

The photos are 1,673 small ImageNet images (Imagenette, 160 pixels) from the Pixeltable repo. `photo_names.txt` lists their file names. The notebook reads them from:

`https://raw.githubusercontent.com/pixeltable/pixeltable/main/tests/data/imagenette2-160/`

28 of them are grayscale, and `bad_image.JPEG` is a short text file with an image's name.

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**

No API keys are needed.

This folder is a Pixeltable project root. `rerun-failures/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

```bash
cd rerun-failures
uv sync
```

That creates `rerun-failures/.venv` and installs Pixeltable 0.7.23 or newer.

### 3. Register the Kernel

```bash
uv run python -m ipykernel install --user --name rerun-failures --display-name rerun-failures
```

### 4. Open the Notebook

Run Jupyter from this folder:

```bash
uv run jupyter lab
```

Open `rerun-failures.ipynb` and pick the `rerun-failures` kernel.

### 5. Run the Notebook

Run it from top to bottom. The chunked insert cell takes about 25 seconds, because it downloads all 1,673 photos. To see a stopped run, interrupt that cell after a few chunks, then run the next cells. The cell after that runs the same function again and inserts only the photos that are not in the table yet.

## Expected Output

The default insert of the first 200 photos stops on a grayscale photo, and `photos.count()` prints `0`:

```
In row 0 the expression average_color(image) encountered exception TypeError:
cannot unpack non-iterable numpy.float64 object
```

After all 1,673 photos are in, the failures grouped by error type look like this:

```
  avg_color_errortype  photos
0        RequestError       1
1        TimeoutError      30
2           TypeError      28
3                 NaN    1614
```

After the first `errors_only=True` retry, the timeouts are gone and 1,644 photos have a color. After `schema_rgb.py` and the second retry, 1,672 do. Deleting `bad_image.JPEG` leaves 1,672 photos and 0 failures.

If you stop the chunked insert partway, the timeout count can come out a few lower. The stand-in remembers every photo it timed out, including photos in the chunk you stopped, and it times out each photo only once.

## File Layout

```
rerun-failures/
  README.md
  rerun-failures.ipynb
  schema.py
  schema_rgb.py
  udfs.py
  photo_names.txt
  pyproject.toml
  uv.lock
```

The local Pixeltable catalog is under `~/.pixeltable`. It is not stored in this repo.

## Troubleshooting

### Schema commands cannot find the project

`cd` into `rerun-failures` and run the notebook from there.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from this folder, register the kernel as above, then pick `rerun-failures`.

### The timeouts fail again on retry

The stand-in remembers which photos it timed out only while the notebook kernel is running. Run the retry from the notebook, in the same kernel as the insert. `pxt recompute ... --errors-only` runs in a new process, so each of those photos times out once more there.

### Duplicate primary key on insert

A row with that `name` is already in the table. `insert_remaining` skips names that are already there, so call it instead of `photos.insert`, or run the notebook from the top. The reset cell drops `rerun_demo`.

### A long traceback after stopping a cell

Stopping the chunked insert prints a `KeyboardInterrupt` traceback, and sometimes `Task exception was never retrieved` lines. Both come from the interrupt. Run `photos.count()` to see the rows that were saved.
