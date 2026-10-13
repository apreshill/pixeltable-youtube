# UI mockups

Generate a mobile UI screen, then grade whether it is usable. The judge looks at the screen type, the layout, the in-image text, and the controls.

UI mockups are text-to-image rows, so they live in `img_eval/generations` and grade through `img_eval/gen_evals`. You set `eval_ready` on a row to move it into the view. The `workflow` field must be `"ui_mockup"`.

## Inputs you set on the row

| Column | Required | What it is |
|--------|----------|------------|
| `case_id` | yes | A stable id, for example `ui_checkout_mockup`. |
| `batch_id` | no | Groups rows, for example `demo_v1` or `run_2`. |
| `workflow` | yes | `"ui_mockup"` |
| `gen_prompt` | yes | The prompt sent to the image model. |
| `prompt` | yes | The instruction shown to the judge. |
| `criteria` | yes | What good means for the judge. |
| `eval_ready` | yes | `False` until you want scores, then `True`. |

The image model and size are set once in [`schema.py`](../../schema.py) as `GEN_MODEL` and `GEN_SIZE`, so you do not set them per row. The demo prompt asks for a checkout screen with the labels Checkout, Place Order, and Edit Cart. The full text is in [`examples.json`](examples.json).

## Outputs the harness computes

On `generations`:

| Column | Meaning |
|--------|---------|
| `image` | The screen generated from `gen_prompt` by `openai.image_generations`. |

On `gen_evals`, only when `eval_ready=True`:

| Column | Meaning |
|--------|---------|
| `scores` | The judge JSON: `instruction_following`, `layout_hierarchy`, `in_image_text_rendering`, `ui_affordance_rendering`, `verdict`, `reason`. |
| `verdict` | `PASS` or `FAIL` after the gate rules. |
| `reason` | The judge's explanation. |
| `tags` | The failure tags, for example `instruction_miss`, `text_garbled`, `weak_hierarchy`, `weak_affordances`. |

### Pass rules

- `instruction_following` must be true.
- `in_image_text_rendering` must be true.
- `layout_hierarchy` must be 3 or higher.
- `ui_affordance_rendering` must be 3 or higher.

The judge prompt, schema, and gate rules are in [`rubric.py`](rubric.py). The scoring runs through `openai.responses` in [`schema.py`](../../schema.py), which then calls this rubric for the verdict and tags.

## Actions

Grade the demo image, which was generated when you ran `scripts/seed_demo.py`:

```python
import udfs
import pixeltable as pxt
generations = pxt.get_table('img_eval/generations')
gen_evals = pxt.get_table('img_eval/gen_evals')
generations.update({'eval_ready': True}, where=generations.case_id == 'ui_checkout_mockup')
gen_evals.where(gen_evals.case_id == 'ui_checkout_mockup').select(
    gen_evals.image, gen_evals.verdict, gen_evals.scores, gen_evals.tags
).collect()
```

Generate a new UI and grade it. Inserting runs the image model:

```python
generations.insert(
    case_id='ui_checkout_v2',
    batch_id='run_2',
    workflow='ui_mockup',
    gen_prompt='...',  # from examples.json or your own
    prompt='...',
    criteria='...',
    eval_ready=True,
)
gen_evals.where(gen_evals.case_id == 'ui_checkout_v2').select(
    gen_evals.image, gen_evals.verdict, gen_evals.scores, gen_evals.tags
).collect()
```

Re-grade without regenerating. Recompute the judge column:

```python
gen_evals.recompute_columns(columns=['judge_raw'], where=gen_evals.case_id == 'ui_checkout_mockup')
```

To tune the job, remember that the inputs on a row are mutable. Call `generations.update(...)` to change the `gen_prompt`, `prompt`, or `criteria` on an existing row, then recompute. You can also edit [`rubric.py`](rubric.py). The schema stays the same.
