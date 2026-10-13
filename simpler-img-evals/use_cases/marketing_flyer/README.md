# Marketing flyers

Generate a print flyer, then grade the copy, layout, brand fit, and visual quality. This job also runs an exact-copy check that compares the text in the image against a list of required strings.

Marketing flyers are text-to-image rows, so they live in `img_eval/generations` and grade through `img_eval/gen_evals`. You set `eval_ready` on a row to move it into the view. The `workflow` field must be `"marketing_flyer"`.

## Inputs you set on the row

| Column | Required | What it is |
|--------|----------|------------|
| `case_id` | yes | For example `coffee_flyer_generation`. |
| `batch_id` | no | Groups rows. |
| `workflow` | yes | `"marketing_flyer"` |
| `gen_prompt` | yes | The prompt for the image model. Include the exact copy. |
| `prompt` | yes | The instruction shown to the judge. |
| `criteria` | yes | What good means for the judge. |
| `required_text` | yes for this job | A JSON list of exact strings that must appear. See [`required_text.json`](required_text.json). |
| `eval_ready` | yes | `False` until you want scores. |

The image model and size are set once in [`schema.py`](../../schema.py). The demo is a flyer for a coffee shop called Sunrise Coffee. The prompts are in [`examples.json`](examples.json), and the required copy is in [`required_text.json`](required_text.json).

## Outputs the harness computes

On `generations`:

| Column | Meaning |
|--------|---------|
| `image` | The flyer generated from `gen_prompt` by `openai.image_generations`. |

On `gen_evals`, when `eval_ready=True`:

| Column | Meaning |
|--------|---------|
| `scores` | The judge JSON: `instruction_following`, `text_rendering`, `layout_hierarchy`, `style_brand_fit`, `visual_quality`, `verdict`, `reason`. |
| `extracted_text` | The list of text lines that a vision pass read from the image. |
| `text_check` | `{pass, missing, extra}` from the compare against `required_text`. |
| `verdict` | `PASS` or `FAIL`. It fails if the judge gates fail or the exact-text check fails. |
| `reason` | The judge's explanation. |
| `tags` | For example `instruction_miss`, `text_garbled`, `exact_text_mismatch`, `brand_mismatch`, `artifacts`. |

### Pass rules

- `instruction_following` and `text_rendering` must be true.
- `layout_hierarchy`, `style_brand_fit`, and `visual_quality` must each be 3 or higher.
- `text_check.pass` must be true.

The exact-copy check asks one question. Did every required string appear in the flyer, spelled and cased the same way? Any text the flyer adds on top of the required copy, such as the shop name, is reported under `extra` but does not fail the check. Whether extra text is a problem is the judge's instruction-following gate, not this check.

The judge prompt, schema, and gate rules are in [`rubric.py`](rubric.py). The exact-text compare is in [`text.py`](text.py). The scoring runs through `openai.responses` in [`schema.py`](../../schema.py), and the same API reads the flyer text for this job.

## Actions

Grade the demo flyer, which was generated when you ran `scripts/seed_demo.py`:

```python
import udfs
import pixeltable as pxt
generations = pxt.get_table('img_eval/generations')
gen_evals = pxt.get_table('img_eval/gen_evals')
generations.update({'eval_ready': True}, where=generations.case_id == 'coffee_flyer_generation')
gen_evals.where(gen_evals.case_id == 'coffee_flyer_generation').select(
    gen_evals.image, gen_evals.verdict, gen_evals.text_check, gen_evals.extracted_text, gen_evals.tags
).collect()
```

Generate a new flyer and grade it. Inserting runs the image model:

```python
import json
from pathlib import Path

required = json.loads(Path('use_cases/marketing_flyer/required_text.json').read_text())
generations.insert(
    case_id='coffee_flyer_v2',
    batch_id='run_2',
    workflow='marketing_flyer',
    gen_prompt='...',
    prompt='...',
    criteria='...',
    required_text=required,
    eval_ready=True,
)
gen_evals.where(gen_evals.case_id == 'coffee_flyer_v2').select(
    gen_evals.image, gen_evals.verdict, gen_evals.text_check, gen_evals.tags
).collect()
```

Re-grade. Recompute the judge column:

```python
gen_evals.recompute_columns(columns=['judge_raw'], where=gen_evals.case_id == 'coffee_flyer_generation')
```

To tune the job, remember that the inputs on a row are mutable. Call `generations.update(...)` to change the `gen_prompt`, `prompt`, or `criteria` on an existing row, then recompute. You can also edit [`required_text.json`](required_text.json) and [`rubric.py`](rubric.py).
