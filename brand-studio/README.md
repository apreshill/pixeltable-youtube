# Brand Studio

Pixeltable keeps your brand kit, every collab campaign, and every campaign visual in one database. Your marketing team writes the inputs in plain words: each brand's kit, each campaign's theme and creative direction, and the ideas for each campaign. Gemini writes the visual prompt for each idea, Nano Banana Pro makes the image, and Gemini reviews it. The prompt, the image, and the review are stored on the idea's own row, so you can see exactly which prompt made which picture.

The brands here are invented for this tutorial. ORIEL (complexion and skin care) is the house brand. brume (hair care) and wallow (bath soaks and candles) are its partners. Their fonts are Google Fonts under the SIL Open Font License.

## Overview

Three tables, one row per thing your team works with:

| Table | One row per | Your team writes | Pixeltable computes on the row |
|---|---|---|---|
| `brands` | brand | the kit: name, palette, fonts, logo, style guide, and whether it is the house brand | `board`: a brand board drawn from the kit. `art_direction`: Gemini's summary of how the brand looks in photographs, read from its style guide |
| `campaigns` | collab campaign | the partner brand, the `theme` (the shared idea), and the `direction` (the look: setting, materials, light, mood) | nothing |
| `ideas` | campaign visual | the campaign it belongs to, and the `idea` in plain words | the prompt Gemini writes, the image, and the review |

A campaign has as many ideas as your team wants. Adding an idea is one insert, and only that new row runs.

## Technical Architecture

1. **Pixeltable database (`collabs`)**
   - `brands`, `campaigns`, and `ideas`, as above.
   - Each `ideas` row looks up its campaign and both brands' kits with `@pxt.query` lookups, so every idea uses its own campaign's theme and direction and both brands' kits.

2. **How one idea becomes a visual (computed columns on the `ideas` row)**
   1. `director_prompt`: the creative director's brief, filled with the idea, the campaign's theme and direction, and both brands' looks and wordmarks, using `pxtf.string.format`.
   2. `director_response` and `visual_prompt`: Gemini reads the brief and both brand boards, and writes the image prompt.
   3. `image_response` and `image`: Nano Banana Pro makes the image from `visual_prompt`, with both logos attached as Image 1 and Image 2.
   4. `review_prompt`, `review`, and `approved`: Gemini checks the image against both brands and says whether it can ship.

3. **Files**
   - `schema.py`: the three tables, the creative director's brief, the craft rules, and the review.
   - `udfs.py`: the brand board, and helpers that read Gemini's responses (`first_image`, `parse_json`). It also still holds functions used by an earlier version of this tutorial.
   - `sample_data.py`: the brand kits, two campaigns, and their ideas.
   - `brand_kits/`: fonts, logos, and style guides for each brand.

4. **Models**

   | Step | Model |
   |---|---|
   | Art direction | `gemini-3.8-flash` |
   | Visual prompts and reviews | `gemini-3.1-pro-preview` |
   | Images | `gemini-3-pro-image` (Nano Banana Pro) |

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- A Gemini API key in `GEMINI_API_KEY`. Each idea makes three calls: one prompt, one image, and one review.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/pixeltable/pixeltable-youtube.git
cd pixeltable-youtube/brand-studio
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Create the Tables

```bash
uv run pxt schema diff schema.py collabs
uv run pxt schema update schema.py collabs
```

## Using It

### Add the Brand Kits

```python
import pixeltable as pxt
import sample_data as data

brands = pxt.get_table('collabs.brands')
brands.insert([data.brand_row('oriel'), data.brand_row('brume')])
```

Each brand makes one Gemini text call, for its art direction.

### Add a Campaign

```python
campaigns = pxt.get_table('collabs.campaigns')
campaigns.insert([{
    'campaign': 'morning-edit',
    'partner': 'brume',
    'theme': 'The Morning Edit, a limited collection for the first hour of the day.',
    'direction': 'One shared, steamy bathroom at 7am: warm terracotta plaster, sage linens, soft window light.',
}])
```

No model calls. Every idea in the campaign reads its theme and direction.

### Add Ideas

```python
ideas = pxt.get_table('collabs.ideas')
ideas.insert([
    {'campaign': 'morning-edit', 'idea': 'Both names woven into the label of a waffle-weave bath towel.'},
    {'campaign': 'morning-edit', 'idea': 'Both names printed into a natural coir doormat at the bathroom door.'},
])
```

Each idea makes three calls: Gemini writes the prompt, Nano Banana Pro makes the image, and Gemini reviews it. Add more ideas to the same campaign any time; only the new rows run.

### See the Results

Each row holds the idea, the prompt that was used, the image it made, and the review:

```bash
uv run pxt rows collabs/ideas --cols idea,visual_prompt,image,approved
uv run pxt dashboard
```

The dashboard shows each image next to its prompt.

### Rerun Only the Ideas That Failed Review

```python
ideas.recompute_columns('director_prompt', where=ideas.approved == False)
```

Gemini writes a new prompt for those rows, and they get a new image and a new review. Approved rows are not touched.

### Add a New Partner

A new partner is one more `brands` row from its own kit, then a campaign that names it:

```python
brands.insert([data.brand_row('wallow')])
campaigns.insert([{'campaign': 'stay-out-late', 'partner': 'wallow', 'theme': '...', 'direction': '...'}])
```

## Expected Output

### Creating the Tables

```
+ collabs/brands     create
+ collabs/campaigns  create
+ collabs/ideas      create

Plan: 3 create, 0 update, 0 unchanged, 0 extra  |  0 destructive
```

## Troubleshooting

### Schema commands cannot find the project

Run them from `brand-studio/`, the folder with `pyproject.toml`.

### A call fails with 402 RESOURCE_EXHAUSTED

Your Gemini prepaid credit is used up. The failed cells keep their error. After you add credit, rerun only them:

```bash
uv run pxt recompute collabs/brands art_direction_response --errors-only -f
```

### Duplicate primary key on insert

The insert ran twice. Each brand, campaign, and idea is inserted once. To change one, update its row.

### A campaign's ideas still use the old theme

Each idea reads its campaign when the idea is made. After you change a campaign, recompute its ideas to use the new theme. That makes new prompts, images, and reviews, so it costs calls.

## Data Structure

| Table | Key | Inputs | Computed |
|---|---|---|---|
| `brands` | `brand` | `name`, `house`, `category`, `palette`, `type_spec`, fonts, `logo`, `style_guide` | `board`, `art_direction_prompt`, `art_direction` |
| `campaigns` | `campaign` | `partner`, `theme`, `direction` | |
| `ideas` | `id` | `campaign`, `idea` | `brief`, `house`, `guest`, `director_prompt`, `visual_prompt`, `image`, `review_prompt`, `review`, `approved` |

## Project Details

### Dependencies

- `pixeltable`
- `google-genai`, for Gemini
- `pillow` and `scipy`, for the brand board
