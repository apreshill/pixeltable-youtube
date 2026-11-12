# Brand Studio

Pixeltable keeps your brand kit, every collab campaign, and every campaign visual in one database. Your marketing team writes the inputs in plain words: each brand's kit, each campaign's theme and creative direction, and the ideas for each campaign. Gemini writes the prompts for each idea, Nano Banana Pro makes the scene and then edits both logos into it, and Gemini signs it off. The prompts, the scene, the final image, and the sign-off are stored on the idea's own row, so you can see exactly which prompt made which picture.

The brands here are invented for this tutorial. ORIEL (complexion and skin care) is the house brand. brume (hair care) and wallow (bath soaks and candles) are its partners. Their fonts are Google Fonts under the SIL Open Font License.

## Overview

Three tables, one row per thing your team works with:

| Table | One row per | Your team writes | Pixeltable computes on the row |
|---|---|---|---|
| `brands` | brand | the kit: name, palette, fonts, logo, style guide, and whether it is the house brand | `board`: a brand board drawn from the kit. `art_direction`: Gemini's summary of how the brand looks in photographs, read from its style guide |
| `campaigns` | collab campaign | the partner brand, the `theme` (the shared idea), and the `direction` (the look: setting, materials, light, mood) | nothing |
| `ideas` | campaign visual | the campaign it belongs to, and the `idea` in plain words | the prompts Gemini writes, the scene, the final image, and the sign-off |

A campaign has as many ideas as your team wants. Adding an idea is one insert, and only that new row runs.

## Technical Architecture

1. **Pixeltable database (`collabs`)**
   - `brands`, `campaigns`, and `ideas`, as above.
   - Each `ideas` row looks up its campaign and both brands' kits with `@pxt.query` lookups, so every idea uses its own campaign's theme and direction and both brands' kits.

2. **How one idea becomes a visual (computed columns on the `ideas` row)**
   1. `director_prompt`: the creative director's brief, filled with the idea, the campaign's theme and direction, and and both brands' looks, using `pxtf.string.format`.
   2. `director_response`, `scene_prompt`, and `logo_prompt`: Gemini reads the brief and both brand boards, and writes two prompts: one for the scene, and one for the edit that makes the logos in it.
   3. `scene_response` and `scene`: Nano Banana Pro makes the scene from `scene_prompt`, with a plain surface and no logos yet.
   4. `locate_response` and `surface_box`: Gemini finds the surface in the scene and returns the box around it.
   5. `house_stencil`, `guest_stencil`, `lockup`, and `guide`: code draws the two real logos with a "×" between them, and places them on the scene in flat magenta, centered in the box. No model draws the letters, so their shapes are always the real logos.
   6. `image_response` and `image`: Nano Banana Pro edits the scene from `logo_prompt`, with the scene and the guide attached. The room stays the same, and only the surface inside the magenta shapes changes.
   7. `review_prompt`, `review`, and `approved`: Gemini signs off the shot as the house brand's chief marketing officer. It answers five questions, each with a short note: is the shot true to the house brand, true to the partner, true to the campaign, are the logos easy to read and made from the scene, and is it restrained. `approved` is true only when all five are yes.

3. **Files**
   - `schema.py`: the three tables, the creative director's brief, the lettering guidance, and the sign-off.
   - `udfs.py`: the brand board, the logo lockup and guide, and helpers that read Gemini's responses (`first_image`, `parse_json`). It also still holds functions used by an earlier version of this tutorial.
   - `sample_data.py`: the brand kits, two campaigns, and their ideas.
   - `brand_kits/`: fonts, logos, and style guides for each brand.

4. **Models**

   | Step | Model |
   |---|---|
   | Art direction, and finding the surface | `gemini-3.8-flash` |
   | Visual prompts and reviews | `gemini-3.1-pro-preview` |
   | Images | `gemini-3-pro-image` (Nano Banana Pro) |

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- A Gemini API key in `GEMINI_API_KEY`. Each idea makes five calls: the prompts, the scene, finding the surface, the logo edit, and the sign-off.

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

Each idea makes five calls: Gemini writes the prompts, Nano Banana Pro makes the scene, Gemini finds the surface, Nano Banana Pro edits the logos into it, and Gemini signs it off. Add more ideas to the same campaign any time; only the new rows run.

### See the Results

Each row holds the idea, the prompt that was used, the image it made, and the review:

```bash
uv run pxt rows collabs/ideas --cols idea,scene_prompt,logo_prompt,scene,guide,image,approved
uv run pxt dashboard
```

The dashboard shows each scene and final image next to its prompts.

### Try a Step in a Query Before You Pay for the Next One

Each `ideas` row stores its campaign brief and both brand kits, so you can try any step with `.select()`. Nothing is stored, and only the step you select runs.

See the filled-in brief Gemini would get. This makes no model calls:

```python
import pixeltable.functions as pxtf
import schema

brief = pxtf.string.format(
    schema.DIRECTOR,
    house=ideas.house['name'], partner=ideas.guest['name'],
    house_look=ideas.house.look, partner_look=ideas.guest.look,
    theme=ideas.brief.theme, direction=ideas.brief.direction, idea=ideas.idea,
)
ideas.select(ideas.idea, brief).collect()
```

See the prompts Gemini writes from it. This is one text call per row, and no image:

```python
response = pxtf.gemini.generate_content(
    [brief, ideas.house.board, ideas.guest.board],
    model=schema.DIRECTOR_MODEL,
    config={'response_mime_type': 'application/json', 'response_json_schema': schema.DIRECTOR_SCHEMA},
)
ideas.select(ideas.idea, response.candidates[0].content.parts[0].text).collect()
```

Edit `DIRECTOR` in `schema.py`, run the query again, and compare. When the prompt reads well, apply it with `pxt schema update` and recompute the rows you want.

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
| `ideas` | `id` | `campaign`, `idea` | `brief`, `house`, `guest`, `director_prompt`, `scene_prompt`, `logo_prompt`, `surface`, `scene`, `surface_box`, `house_stencil`, `guest_stencil`, `lockup`, `guide`, `image`, `review_prompt`, `review`, `approved` |

## Project Details

### Dependencies

- `pixeltable`
- `google-genai`, for Gemini
- `pillow` and `scipy`, for the brand board
