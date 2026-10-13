# Virtual try-on

Edit a photo to put a person into a garment, using two reference images, then grade the result. The judge looks at whether the output keeps the same person, matches the reference garment, and preserves body shape.

Virtual try-on is an image-edit row, so it lives in `img_eval/edits` and grades through `img_eval/edit_evals`. You set `eval_ready` on a row to move it into the view. The `workflow` field must be `"virtual_try_on"`.

## Inputs you set on the row

| Column | Required | What it is |
|--------|----------|------------|
| `case_id` | yes | For example `vto_jacket_tryon`. |
| `batch_id` | no | Groups rows. |
| `workflow` | yes | `"virtual_try_on"` |
| `gen_prompt` | yes | The edit instruction for the image model. |
| `prompt` | yes | The instruction shown to the judge. |
| `criteria` | yes | What good means for the judge. |
| `ref_image` | yes | The person photo. See [`assets/person.png`](assets/person.png). |
| `ref_image_2` | for try-on | The garment photo. See [`assets/garment.png`](assets/garment.png). |
| `eval_ready` | yes | `False` until you want scores. |

The edit model is set once in [`schema.py`](../../schema.py) as `EDIT_MODEL`. The demo is a jacket try-on. The full prompts are in [`examples.json`](examples.json). The two reference images should be model-generated with [`scripts/make_tryon_inputs.py`](../../scripts/make_tryon_inputs.py).

## Outputs the harness computes

On `edits`:

| Column | Meaning |
|--------|---------|
| `image` | The try-on edit made from `ref_image` and `ref_image_2` by `gemini.generate_content`. |

On `edit_evals`, when `eval_ready=True`:

| Column | Meaning |
|--------|---------|
| `scores` | The judge JSON: `facial_similarity`, `outfit_fidelity`, `body_shape_preservation`, `verdict`, `reason`. Each metric is 0 to 5. |
| `verdict` | `PASS` if every metric is 3 or higher, otherwise `FAIL`. |
| `reason` | The judge's explanation. |
| `tags` | For example `identity_drift`, `garment_mismatch`, `body_warp`. |

The judge prompt, schema, and gate rules are in [`rubric.py`](rubric.py). The scoring runs through `openai.responses` in [`schema.py`](../../schema.py). The edit uses Gemini with both reference images.

## Actions

Grade the demo try-on, which was generated when you ran `scripts/seed_demo.py`:

```python
import udfs
import pixeltable as pxt
edits = pxt.get_table('img_eval/edits')
edit_evals = pxt.get_table('img_eval/edit_evals')
edits.update({'eval_ready': True}, where=edits.case_id == 'vto_jacket_tryon')
edit_evals.where(edit_evals.case_id == 'vto_jacket_tryon').select(
    edit_evals.image, edit_evals.verdict, edit_evals.scores, edit_evals.tags
).collect()
```

Run a new try-on edit and grade it. Inserting runs the edit model:

```python
edits.insert(
    case_id='vto_jacket_v2',
    batch_id='run_2',
    workflow='virtual_try_on',
    gen_prompt='Put the person in the first image into the jacket...',
    prompt='Put the person in the first image into the jacket...',
    criteria='Same person and background; jacket matches; body preserved.',
    ref_image='use_cases/virtual_try_on/assets/person.png',
    ref_image_2='use_cases/virtual_try_on/assets/garment.png',
    eval_ready=True,
)
edit_evals.where(edit_evals.case_id == 'vto_jacket_v2').select(
    edit_evals.image, edit_evals.verdict, edit_evals.scores, edit_evals.tags
).collect()
```

Re-grade. Recompute the judge column:

```python
edit_evals.recompute_columns(columns=['judge_raw'], where=edit_evals.case_id == 'vto_jacket_tryon')
```

To tune the job, remember that the inputs on a row are mutable. Call `edits.update(...)` to change the `gen_prompt`, `prompt`, `criteria`, or a reference image on an existing row, then recompute. You can also swap the files under `assets/`, or edit [`rubric.py`](rubric.py).
