# Image Evals Are Simpler Than You Think

If your product generates or edits images, OpenAI's [image evals cookbook](https://developers.openai.com/cookbook/examples/multimodal/image_evals) shows a sound way to grade them. Check the hard requirements first, then score quality from 0 to 5, then tag how each image failed. To run it, OpenAI built a custom harness of three packages that call the image model, save the images, and run the judge. Using the method yourself usually means building something like that next to your app: an eval script that pulls the images out, grades them, stores the scores somewhere else, and has to change every time the app does.

You do need the grades, because image models fail quietly. A flyer with a misspelled line or a try-on that changed the person's face looks like any other image until someone reads it.

In this tutorial, the grade is one more step on the table the images already live in. Mark an image ready, and the judge grades it and saves the grade next to the image. A new image gets graded the same way, and so does every image that was already there. When you change the rubric and re-grade, only the grade runs again: judge calls, no image calls. There is no separate eval script to keep in step with the app. Teams building on Pixeltable already grade their outputs this way.

## How an image is graded

The grading runs three checks in order, following the OpenAI cookbook.

1. Gates first. Check the hard requirements, for example required text or an edit that must stay in one place. A gate failure fails the image even if it looks good.
2. Graded scores next. For the images that clear the gates, score quality from 0 to 5 so you can rank them.
3. Failure tags last. Label how an image failed, for example `text_garbled` or `identity_drift`, so the next fix has a target.

The demo grades four kinds of images. Two are made from a prompt, and two are edits of reference images. The last column says which recipe in [`demo.ipynb`](demo.ipynb) shows each one.

| Job | Folder | Table | Produced by | Notebook recipe |
|-----|--------|-------|-------------|-----------------|
| Mobile UI mockup | [`use_cases/ui_mockup/`](use_cases/ui_mockup/) | generations | `openai.image_generations` | 1 |
| Marketing flyer | [`use_cases/marketing_flyer/`](use_cases/marketing_flyer/) | generations | `openai.image_generations` | 1 and 2 |
| Virtual try-on | [`use_cases/virtual_try_on/`](use_cases/virtual_try_on/) | edits | `gemini.generate_content`, two images | 4 |
| Logo edit | [`use_cases/logo_edit/`](use_cases/logo_edit/) | edits | `gemini.generate_content`, one image | 3 |

Recipe 5 re-grades the images from Recipe 1. Open a job folder's README for that job's inputs, pass rules, and sample commands. You can ignore the other three if you only care about one.

## Technical Architecture

Pixeltable is the database. It stores the inputs, the images, and the grades, and it makes the model calls. The catalog directory is `img_eval`.

1. **Base tables**
   - `generations` holds text-to-image rows for UI mockups and marketing flyers. The `image` column is produced by `openai.image_generations`.
   - `edits` holds image-edit rows for virtual try-on and logo edits. The `image` column is produced by `gemini.generate_content`.

2. **Judge views**
   - `gen_evals` and `edit_evals` are views over the rows where `eval_ready` is true.
   - Each view calls `openai.responses`, parses the JSON, and fills in the scores, verdict, and tags.

3. **Schema and judge code**
   - [`schema.py`](schema.py) declares both tables and both views. The three models are constants in that file: `GEN_MODEL`, `EDIT_MODEL`, and `JUDGE_MODEL`. Changing a constant does not keep the old results to compare against. To compare two models, keep both results, for example a second image column for the new model with its own grade.
   - [`udfs.py`](udfs.py) holds the judge helpers. Import it before you touch the tables. That import registers the functions the tables use.
   - Each job folder under `use_cases/` is a Python package. `udfs.py` imports that job's `rubric.py`. The `workflow` field on a row picks which rubric to use.

```text
img_eval/generations                          img_eval/edits
  gen_prompt → openai.image_generations         refs + prompt → gemini.generate_content
       │  image                                        │  image
       │  set eval_ready = True                        │  set eval_ready = True
       ▼                                               ▼
img_eval/gen_evals                             img_eval/edit_evals
  openai.responses → scores → verdict, tags      openai.responses → scores → verdict, tags
```

Inserting a row runs the image model and stores the result in the `image` column. The views include only the rows where `eval_ready` is true. So you can look at the images first, and the judge runs, and you pay for it, only on the ones you mark ready.

The inputs you insert are mutable. You can call `update(...)` to change a prompt or reference image on an existing row. Only that row's image is made again, and its grade too if the row is marked ready.

Each row has two prompt fields. `gen_prompt` is sent to the image model. `prompt` is the instruction shown to the judge. They often hold the same text. You can set them apart when you want the judge to grade against different wording than the model saw.

The judge output is stored with each row. To re-grade after you change a rubric, recompute the `judge_raw` column on the view, as shown in [`demo.ipynb`](demo.ipynb). A re-grade makes judge calls only. The images are not made again, so it makes no image calls.

Editing uses Gemini. `generate_content` accepts several reference images in one call, which virtual try-on needs, because it passes both the person and the garment. The built-in Pixeltable function for OpenAI image edits takes a single image.

`simpler-img-evals` is the Pixeltable project root. Pixeltable finds `pyproject.toml` in this folder and adds this folder to the Python path. That is why `schema.py` can import `udfs` and `use_cases` even though the folder name has a hyphen and is not a Python module. The job folders stay packages inside this project. They do not get their own `pyproject.toml`.

## Prerequisites

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/)
- Git
- `OPENAI_API_KEY` for image generation and the judge
- `GEMINI_API_KEY` for the edit jobs

This folder is a Pixeltable project root. `simpler-img-evals/pyproject.toml` already contains a `[[tool.pixeltable.database]]` section, so you do not need to run `pxt init` after cloning.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/apreshill/pixeltable-youtube.git
cd pixeltable-youtube
```

### 2. Install Dependencies

Each tutorial in this repo is its own uv project. Install this one from its folder.

```bash
cd simpler-img-evals
uv sync
```

Set both keys in your shell, then restart the `pxt` daemon so it picks them up.

```bash
export OPENAI_API_KEY=...
export GEMINI_API_KEY=...
uv run pxt daemon restart
```

Pixeltable reads provider keys from your environment or from `~/.pixeltable/config.toml`. It does not read a `.env` file. To keep the keys across shells, add the two `export` lines to your shell profile, or put the keys in `config.toml` (see the [configuration docs](https://docs.pixeltable.com/platform/configuration)). The `pxt` daemon makes the model calls and reads the keys once, when it starts, so restart it after you set or change a key.

### 3. Register the Kernel

Register this folder's `.venv` as a Jupyter kernel named `simpler-img-evals`. The notebook is set to use it.

```bash
uv run python -m ipykernel install --user --name simpler-img-evals --display-name simpler-img-evals
```

### 4. Open the Notebook

Run Jupyter from this folder so `pxt schema` can find `schema.py` and Python can import `use_cases`.

```bash
uv run jupyter lab
```

Open `demo.ipynb`. In Jupyter, Cursor, or VS Code, pick the `simpler-img-evals` kernel. The first code cell is:

```python
!uv sync
```

## Expected Output

### When Installing Dependencies

`uv sync` creates `simpler-img-evals/.venv` and installs Pixeltable 0.7.11 or newer, plus OpenAI, Google GenAI, Pillow, and Jupyter.

### When Applying the Schema

The notebook prints a plan before it changes the catalog. The first apply looks like this:

```text
+ img_eval/generations create
+ img_eval/edits create
+ img_eval/gen_evals create
+ img_eval/edit_evals create

Plan: 4 create, 0 update, 0 unchanged, 0 extra  |  0 destructive
```

`uv run pxt ls img_eval` then lists `generations` and `edits` as tables, and `gen_evals` and `edit_evals` as views.

### When the Demo Batch Is Graded

The seed cell inserts four rows and generates four images. Grading calls the judge, so the wording of each reason varies. Check the verdict and the tags.

- UI mockup. Instruction following and in-image text are gates. Layout and affordances are graded from 0 to 5.
- Marketing flyer. A missing required string fails the flyer even if the design looks good. Extra text, such as the shop name, is reported and does not by itself fail the exact-text check.
- Virtual try-on. The same person, the reference garment, and body shape are each scored from 0 to 5. The verdict passes when every score is 3 or higher.
- Logo edit. Every score must be 4 or higher. A correct text change can still fail when the edit spills into the background or the style.

## Run the Demo

Run `demo.ipynb` from top to bottom.

1. `!uv sync`
2. `pxt schema diff schema.py img_eval`
3. `pxt schema update schema.py img_eval -f`
4. `python scripts/seed_demo.py`, which generates the four demo images and leaves `eval_ready` false
5. Set `eval_ready` to true. The views run the judge.
6. Read the verdict, scores, and tags next to each image

Later cells generate a new UI mockup, run a logo edit, run a try-on, re-grade without regenerating, and delete the demo batch.

To browse the rows and images in a browser, run `uv run pxt dashboard` from this folder.

## Data Structure

```text
simpler-img-evals/
  README.md
  demo.ipynb
  pyproject.toml
  uv.lock
  schema.py
  udfs.py
  scripts/
    seed_demo.py
    make_tryon_inputs.py
  use_cases/
    ui_mockup/
    marketing_flyer/
    virtual_try_on/
    logo_edit/
```

Each job folder holds:

| File | Role |
|------|------|
| `README.md` | The inputs, outputs, and actions for that job. |
| `rubric.py` | The judge prompt, JSON schema, and gate and tag rules. |
| `examples.json` | The sample row fields. |
| `assets/` | The edit reference images, for try-on and the logo. |
| `required_text.json` | Marketing only. The list of exact copy. |
| `text.py` | Marketing only. The exact-text compare. |

`scripts/make_tryon_inputs.py` generates `use_cases/virtual_try_on/assets/person.png` and `garment.png` with `openai.image_generations`. The files already in `assets/` are those generated images. Run the script again only when you want new references.

The local Pixeltable catalog is under `~/.pixeltable`. It is not in this repo.

## Troubleshooting

### Schema commands cannot find the project

`cd` into `simpler-img-evals` and run the command again. This folder is the project root. The folder name has a hyphen, so it is not a Python module. Pixeltable loads `udfs` and `use_cases` from this folder.

### `import udfs` or `use_cases` fails

Run Python with this folder as the working directory, after `uv sync`. `udfs.py` imports `use_cases.ui_mockup`, `use_cases.marketing_flyer`, `use_cases.virtual_try_on`, and `use_cases.logo_edit`. Those imports work because each job folder has an `__init__.py` and this folder is on the Python path. A `pyproject.toml` inside `use_cases` would make that subfolder the project root and those imports would break.

### The notebook kernel cannot import Pixeltable

Run `uv sync` from `simpler-img-evals/`, register the kernel (Setup step 3), then pick the `simpler-img-evals` kernel.

### The schema diff says unsupported

`img_eval` is already in the local catalog, and the stored tables do not match `schema.py`. Pixeltable cannot change those columns in place. Run `pxt.drop_dir('img_eval', force=True)` yourself, for example with `uv run python -c "import pixeltable as pxt; pxt.drop_dir('img_eval', force=True)"` from this folder, then run the schema cells again. That deletes the old `img_eval` tables and every image and grade in them.

### The seed script says the batch is already loaded

`scripts/seed_demo.py` skips the insert when `demo_v1` is already in the tables. Delete that batch with the notebook's last cell, "Delete the sample rows". Or run `pxt.drop_dir('img_eval', force=True)` yourself, as in the section above, and run the notebook again from the schema cells. That deletes the old `img_eval` tables and every image and grade in them.

### Images or verdicts are empty

Set `OPENAI_API_KEY` and `GEMINI_API_KEY` where the `pxt` daemon runs. Restart the daemon if you set the keys after it started. From this folder:

```bash
uv run pxt daemon restart
```

### `uv sync` warns that `VIRTUAL_ENV` does not match

Another virtual environment is active in the shell that started Jupyter or your editor. uv ignores it and uses `simpler-img-evals/.venv`, so the sync still works. To clear the warning, run `deactivate` or open a new terminal, then start Jupyter again from `simpler-img-evals/`.

## Project Details

### Dependencies

- Pixeltable 0.7.11 or newer. Tables, computed columns, views, and `pxt schema`.
- OpenAI. Text-to-image generation and the vision judge.
- Google GenAI. Image edits.
- Pillow. Image values in the edit helper.
- JupyterLab and ipykernel. Running the notebook.

### Resources

- [OpenAI image evals cookbook](https://developers.openai.com/cookbook/examples/multimodal/image_evals)
- [Pixeltable documentation](https://docs.pixeltable.com/)
- [Pixeltable on YouTube](https://www.youtube.com/@PixeltableHQ)
