# Off-label Pixeltable: help my parents pick a front door color

Pixeltable is a multimodal backend for AI apps. This tutorial uses it off label, for a family project.

My parents want to paint their front door navy, and Benjamin Moore has dozens of navies. This notebook puts the whole decision in one Pixeltable table. You insert one door photo and a list of color numbers. For each color, Pixeltable reads the official color data from Benjamin Moore's site, draws a paint chip, and has Gemini repaint just the door in that color. Then you compare the colors in one table, one row per color.

The same pattern works for other personal projects: one photo you care about, a list of options, the official facts for each option, and an AI preview of each option on your photo. Try it with bedroom wall colors, backsplash tiles, or a new hair color.

## Overview

1. `doors` holds one photo of the front door.
2. `paints` holds one row per color. You insert only the color number, such as `HC-154`.
3. Computed columns fill in the rest: the name, hex, LRV, collection, Benjamin Moore's photo of the color, a paint chip, and the repainted door.
4. `on_error='ignore'` keeps the insert going if Gemini returns no image for a color. `recompute_columns('response', where=...)` reruns only those colors.

| Color | Number | Hex | LRV |
|---|---|---|---|
| Van Deusen Blue | HC-156 | #485B6E | 11.97 |
| Newburyport Blue | HC-155 | #465566 | 10.31 |
| Hudson Bay | 1680 | #3F5266 | 9.77 |
| Hale Navy | HC-154 | #434B56 | 8.36 |
| Gentleman's Gray | 2062-20 | #304656 | 7.26 |
| Symphony Blue | 2060-10 | #203B5D | 6.16 |
| Deep Royal | 2061-10 | #2F394B | 5.36 |

LRV is light reflectance value, from 0 (black) to 100 (white).

## Technical Architecture

1. **Pixeltable database (`door_demo`)**
   - `doors`: the door photo and its credit.
   - `paints`: one row per color, with its official data, chip, and repainted door.

2. **Schema and functions**
   - `schema.py` declares both tables and the repaint prompt.
   - `udfs.py` reads a color's data from its Benjamin Moore page, downloads Benjamin Moore's photo of the color, draws the chip, and pulls the image out of Gemini's response.

3. **Notebook (`off-label-doors.ipynb`)**
   - Resets `door_demo`, applies `schema.py`, inserts the door and the colors, reruns any failed doors, and shows the comparison.

The door photo is a free photo by Shaylyn on [Unsplash](https://unsplash.com/photos/-zNNFDR3dPM). Color data and color photos come from each color's page on [benjaminmoore.com](https://www.benjaminmoore.com/en-us/paint-colors). Screen colors are close, not exact: check a real paint sample on the door before you buy.

## Prerequisites

- **Python 3.11 or newer**
- **[uv](https://docs.astral.sh/uv/)**
- **Git**
- **`GEMINI_API_KEY`** in your environment. The repaint uses `gemini-3-pro-image`.

This folder is a Pixeltable project root. `off-label-doors/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

```bash
cd off-label-doors
uv sync
```

### 3. Register the Kernel

```bash
uv run python -m ipykernel install --user --name off-label-doors --display-name off-label-doors
```

### 4. Open the Notebook

Run Jupyter from this folder:

```bash
uv run jupyter lab
```

Open `off-label-doors.ipynb`, pick the `off-label-doors` kernel, and run the cells from the top.

## Expected Output

### When Applying the Schema

```
+ door_demo/doors          create
+ door_demo/paints         create

Plan: 2 create, 0 update, 0 unchanged, 0 extra  |  0 destructive
```

### When Inserting the Colors

```
Inserted 6 rows with 0 errors across 1 column (paints.painted_door)
```

Each Gemini call takes about 25 seconds. If some doors fail, the message counts them, and the rerun cell retries only those.

## Try Your Own Door and Colors

- Your door: put your photo's path or URL in the `doors.insert` cell. The prompt in `schema.py` names the parts of this house to keep (sidelights, brick, porch). Change that list to match your house.
- Other colors: insert any Benjamin Moore color number from the end of its page URL, for example `2061-10` from `.../paint-colors/color/2061-10/deep-royal`. Only the new rows run.

## File Layout

```
off-label-doors/
  README.md
  off-label-doors.ipynb
  schema.py
  udfs.py
  pyproject.toml
  uv.lock
```

## Troubleshooting

### `there is no project root`

The notebook's working directory is not `off-label-doors`. Start Jupyter from this folder.

### `the model returned no image (finish reason: IMAGE_RECITATION)`

Gemini judged its output too close to an image it knows. It varies from call to call. Run the rerun cell to retry only those colors.

### `no color data on the page for ...`

The color number is wrong, or Benjamin Moore changed its page. Check that the number opens a color page on benjaminmoore.com.

### `Duplicate primary key` on insert

The insert cell ran twice. Run the notebook from the top; the reset cell drops `door_demo`.
