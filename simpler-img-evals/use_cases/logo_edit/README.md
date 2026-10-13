# Logo editing

Edit specific text in a logo while keeping everything else the same, then grade the result with strict thresholds. Near misses fail.

Logo edits are image-edit rows, so they live in `img_eval/edits` and grade through `img_eval/edit_evals`. You set `eval_ready` on a row to move it into the view. The `workflow` field must be `"logo_edit"`.

## Inputs you set on the row

| Column | Required | What it is |
|--------|----------|------------|
| `case_id` | yes | For example `logo_year_edit`. |
| `batch_id` | no | Groups rows. |
| `workflow` | yes | `"logo_edit"` |
| `gen_prompt` | yes | The narrow edit instruction. |
| `prompt` | yes | The instruction shown to the judge. |
| `criteria` | yes | What good means for the judge. |
| `ref_image` | yes | The source logo. See [`assets/logo_input.png`](assets/logo_input.png). |
| `eval_ready` | yes | `False` until you want scores. |

A logo edit uses a single reference image, so leave `ref_image_2` unset. The edit model is set once in [`schema.py`](../../schema.py) as `EDIT_MODEL`. The demo edit changes the text FIELD to BUTTER and changes nothing else. The prompts are in [`examples.json`](examples.json).

## Outputs the harness computes

On `edits`:

| Column | Meaning |
|--------|---------|
| `image` | The edit made from `ref_image` and `gen_prompt` by `gemini.generate_content`. |

On `edit_evals`, when `eval_ready=True`:

| Column | Meaning |
|--------|---------|
| `scores` | The judge JSON: `edit_intent_correctness`, `non_target_invariance`, `character_and_style_integrity`, `verdict`, `reason`. Each metric is 0 to 5. |
| `verdict` | `PASS` only if every metric is 4 or higher, otherwise `FAIL`. |
| `reason` | The judge's explanation. |
| `tags` | For example `edit_miss`, `edit_spill`, `style_drift`. |

The cookbook demo often fails on spill, which is a change to the background or style, even when the text change is correct. That is expected with these thresholds.

The judge prompt, schema, and gate rules are in [`rubric.py`](rubric.py). The scoring runs through `openai.responses` in [`schema.py`](../../schema.py). The edit uses Gemini.

## Actions

Grade the demo edit, which was generated when you ran `scripts/seed_demo.py`:

```python
import udfs
import pixeltable as pxt
edits = pxt.get_table('img_eval/edits')
edit_evals = pxt.get_table('img_eval/edit_evals')
edits.update({'eval_ready': True}, where=edits.case_id == 'logo_year_edit')
edit_evals.where(edit_evals.case_id == 'logo_year_edit').select(
    edit_evals.image, edit_evals.verdict, edit_evals.scores, edit_evals.tags, edit_evals.reason
).collect()
```

Run a new logo edit and grade it. Inserting runs the edit model:

```python
edits.insert(
    case_id='logo_butter_v2',
    batch_id='run_2',
    workflow='logo_edit',
    gen_prompt='Edit the logo by changing the text from FIELD to BUTTER. Do not change any other text, colors, shapes, or layout.',
    prompt='Edit the logo by changing the text from FIELD to BUTTER. Do not change any other text, colors, shapes, or layout.',
    criteria='Exact edit; non-target unchanged; style preserved.',
    ref_image='use_cases/logo_edit/assets/logo_input.png',
    eval_ready=True,
)
edit_evals.where(edit_evals.case_id == 'logo_butter_v2').select(
    edit_evals.image, edit_evals.verdict, edit_evals.scores, edit_evals.tags
).collect()
```

Re-grade. Recompute the judge column:

```python
edit_evals.recompute_columns(columns=['judge_raw'], where=edit_evals.case_id == 'logo_year_edit')
```

To tune the job, remember that the inputs on a row are mutable. Call `edits.update(...)` to change a prompt or the `ref_image` on an existing row, then recompute. You can also replace [`assets/logo_input.png`](assets/logo_input.png), or edit the thresholds in [`rubric.py`](rubric.py).
