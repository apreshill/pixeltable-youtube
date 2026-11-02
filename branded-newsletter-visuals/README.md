# Branded newsletter visuals

Insert one newsletter issue. You get a branded cover and a 5-second video.

You type an issue number and a short scene, and you can add an inspiration picture for the image model to start from. The scene becomes the prompt for the picture and for the video, and the issue number becomes the words on the cover. On that insert, Pixeltable fills both prompts, generates the picture, prints the issue number and the newsletter name on it, and animates that cover. The cover is the first frame of the video.

The sample scenes are four public issues of [Rami Krispin's newsletter](https://ramikrispin.substack.com/archive). The notebook inserts issues 111 and 109. Issues 106 and 93 are also in `sample_issues.py`.

## Overview

`schema.py` declares one table, `visuals.issues`. You insert a row. These columns fill in for that row:

1. `issue_label`, `art_prompt`, and `motion_prompt`, from the issue number and the scene
2. `art_response` and `art`: a 16:9 still from Gemini's Nano Banana model (`gemini-3.1-flash-image-preview`), with no text in the picture
3. `plate` and `cover`: `ISSUE N` in pink neon at the upper left, and `RAMI'S DATA NEWSLETTER` as white neon outline letters with a red glow along the bottom
4. `video`, 5 seconds, 16:9, from Gemini Omni Flash, with the cover as the first frame

A second insert computes only the new row.

## Technical Architecture

1. **Pixeltable database (`visuals`)**
   - `issues`: one row per issue
   - You insert `issue_number` (primary key) and `scene`, and optionally `inspiration`, a picture
   - Computed columns: `issue_label`, `art_prompt`, `motion_prompt`, `art_response`, `art`, `plate`, `cover`, `video`

2. **Files**
   - `schema.py`: the table and its two prompt templates, `ART_TEMPLATE` and `MOTION_TEMPLATE`
   - `udfs.py`: the Pillow plate and the video call
   - `sample_issues.py`: issues 111, 109, 106, and 93

3. **Notebook (`branded-newsletter-visuals.ipynb`)**
   - Creates the empty table with one `pxt schema update`
   - Inserts issues 111 and 109 and shows their covers and videos

4. **Sample issues**
   - 111: a photoreal green valley
   - 109: Van Gogh's *Starry Night*, with a wheat field and a horse
   - 106: a flat poster of a mountain, a red pagoda, a lake, autumn trees, and a few birds
   - 93: Baby Yoda in a wheat field, painted in that swirling night-sky style, reaching toward a star

`pxtf.string.format(template, scene=scene)` fills the template per row. Calling `template.format(scene=scene)` formats the column expression once in Python, so every row would get the same string.

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)** for installing this folder's dependencies
- **Git** for cloning the repository
- **A Gemini API key**, for the still and the video

Both the notebook and the `pxt` daemon call the Gemini API. The simplest way to give both of them the key is to put it in `~/.pixeltable/config.toml`:

```toml
[gemini]
api_key = '...'
```

Then restart the daemon once from `branded-newsletter-visuals/` with `uv run pxt daemon restart`.

This folder is a Pixeltable project root. `branded-newsletter-visuals/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

Each tutorial in this repo is its own uv project. `branded-newsletter-visuals/pyproject.toml` lists the packages and `branded-newsletter-visuals/uv.lock` pins their versions.

```bash
cd branded-newsletter-visuals
uv sync
```

That creates `branded-newsletter-visuals/.venv` and installs Pixeltable 0.7.14 or newer, plus Pillow, the Gemini SDK, and Jupyter.

### 3. Register the Kernel

Register this folder's `.venv` as a Jupyter kernel named `branded-newsletter-visuals`. The notebook is set to use it:

```bash
uv run python -m ipykernel install --user --name branded-newsletter-visuals --display-name branded-newsletter-visuals
```

### 4. Open the Notebook

Run the notebook with this folder as the working directory. The `pxt schema` cell looks for `schema.py` next to the notebook.

```bash
uv run jupyter lab
```

Open `branded-newsletter-visuals.ipynb`. In Jupyter, Cursor, or VS Code, pick the `branded-newsletter-visuals` kernel.

### 5. Insert an Issue

Run the notebook from top to bottom.

1. Preview the table with `pxt schema diff schema.py visuals`
2. Create it with `pxt schema update schema.py visuals -f`
3. Insert issue 111, then issue 109

Each insert runs one image call and one video call, and takes about a minute. The second insert computes only issue 109. The last cell shows both covers and both videos.

### 6. Start Over

The cell after `uv sync` drops the `visuals` directory, so running the notebook from the top starts with an empty table. Each run pays for the image and video calls again.

## Expected Output

Issue 111's cover is a generated green valley with `ISSUE 111` in pink neon at the upper left and `RAMI'S DATA NEWSLETTER` in white neon outline letters with a red glow along the bottom. The still changes from run to run. The video is 5 seconds and 16:9, and the cover is its first frame.

## Troubleshooting

### Schema commands cannot find the project

You ran the command from the wrong directory. `cd` into `branded-newsletter-visuals` and run it again. Do not run `pxt init` at the repo root. `branded-newsletter-visuals` is not a valid Python module name because of the hyphen.

### The insert fails or the cover and video are empty

The notebook or the `pxt` daemon cannot find `GEMINI_API_KEY`. Put the key in `~/.pixeltable/config.toml` as shown in Prerequisites, then run `uv run pxt daemon restart` from `branded-newsletter-visuals/` and restart the kernel.

### A video cell holds an error

Omni allows only a few requests a minute and a small number a day, so a video call can fail on a rate limit (429). Because the notebook inserts with `on_error='ignore'`, the row keeps its picture and cover with the error in `video`. Rerun only the failed videos:

```python
issues.recompute_columns('video', errors_only=True)
```

### Duplicate rows

`issue_number` is a primary key, so inserting the same issue twice fails with `Duplicate primary key` instead of adding a copy. Use a new issue number, or run the notebook from the top, which drops the table first.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from `branded-newsletter-visuals/`, register the kernel (Setup step 3), then pick the `branded-newsletter-visuals` kernel.

### `uv sync` warns that `VIRTUAL_ENV` does not match

Another virtual environment is active in the shell that started Jupyter or your editor. uv ignores it and uses `branded-newsletter-visuals/.venv`, so the sync still works. To clear the warning, run `deactivate` or open a new terminal, then start Jupyter again from `branded-newsletter-visuals/`.

### `!pxt` says command not found

The notebook's shell cannot see `branded-newsletter-visuals/.venv/bin`. Start Jupyter with `uv run jupyter lab` from `branded-newsletter-visuals/`. Selecting `.venv` as the kernel in an editor does not always put `.venv/bin` on the shell path.

## Data Structure

```
branded-newsletter-visuals/
  branded-newsletter-visuals.ipynb   # create the table, insert two issues, show the covers and videos
  pyproject.toml           # dependencies and Pixeltable project config
  uv.lock                  # pinned versions for this tutorial
  schema.py                # the issues table and its two prompt templates
  udfs.py                  # the Pillow plate and the video call
  sample_issues.py         # issues 111, 109, 106, and 93
  images/                  # issue 111's cover and video, shown at the top of the notebook
  fonts/                   # Barlow Condensed Medium and Montserrat, under the SIL Open Font License
```

The local Pixeltable database is under `~/.pixeltable`.

## Extending the Database

### Adding an Issue

Insert a row with a new `issue_number` and a short `scene`. Pixeltable fills the prompts, the still, the plate, the cover, and the video for that row. Rows already stored stay as they are.

```python
issues.insert([{
    'issue_number': 112,
    'scene': 'A short description of the picture.',
}], on_error='ignore')
```

To start from a picture of your own, add `inspiration`, a file path or URL. `INSPIRATION_NOTE` in `schema.py` ("Use the attached image as inspiration.") then fills the `{image_note}` slot at the start of `ART_TEMPLATE`, and the model gets the image followed by that prompt. In rows without one, the slot is empty and the prompt goes alone.

```python
issues.insert([{
    'issue_number': 113,
    'scene': 'A short description of the picture.',
    'inspiration': 'my-photo.jpg',
}], on_error='ignore')
```

Issues 106 and 93 are already in `sample_issues.py`. Insert one by changing `109` in the notebook's second insert cell to that number.

### Changing the Table

1. Edit `schema.py`
2. Run `pxt schema diff schema.py visuals` and read the plan
3. Run `pxt schema update schema.py visuals -f` if the plan is what you want
4. Reload the table in Python with `pxt.get_table('visuals.issues')`

## Project Details

### Dependencies

- Pixeltable 0.7.14 or newer: tables, computed columns, `pxt schema`
- google-genai: the still, through Nano Banana (`gemini-3.1-flash-image-preview`), and the video, through Gemini Omni Flash (`gemini-omni-1.1-flash`)
- Pillow: the brand plate
- JupyterLab and ipykernel: running the notebook

### Resources

- [Rami Krispin's newsletter](https://ramikrispin.substack.com/archive)
- [Issue 111 on Substack](https://ramikrispin.substack.com/p/data-engineering-for-multimodal-ai)
- [Pixeltable documentation](https://docs.pixeltable.com/)
- [Barlow Condensed](https://fonts.google.com/specimen/Barlow+Condensed), [SIL Open Font License](fonts/OFL.txt)
- [Montserrat](https://fonts.google.com/specimen/Montserrat), [SIL Open Font License](fonts/OFL-Montserrat.txt)
- [uv projects](https://docs.astral.sh/uv/concepts/projects/)
