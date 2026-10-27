"""Class-based Pixeltable schema for the image eval harness.

Two base tables, split by operation, each producing its image with a built-in
Pixeltable provider function and a constant model, so the provider and model are
part of the schema:
  - generations.image via pxtf.openai.image_generations  (GEN_MODEL)
  - edits.image        via pxtf.gemini.generate_content   (EDIT_MODEL)

Each base table has a view over its eval_ready rows that runs the vision judge
(pxtf.openai.responses with JUDGE_MODEL). The judge returns a JSON string; one
udfs.parse_json turns it into an object, after which the fields are native
Pixeltable access (scores.verdict, scores.reason).

The provider functions need a constant model for resource-pool resolution, so
the three models are constants here, not per-row columns.

Apply with:
    pxt schema update schema.py img_eval -f
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

import udfs

TableModel = pxt.model_base()

JUDGE_MODEL = 'gpt-5.2'                 # OpenAI vision judge
GEN_MODEL = 'gpt-image-1.5'            # OpenAI text-to-image
GEN_SIZE = '1024x1024'
EDIT_MODEL = 'gemini-2.5-flash-image'  # Gemini image edit
_EDIT_CONFIG = {'response_modalities': ['IMAGE']}


class Generations(TableModel, name='generations'):
    """Text-to-image rows: ui_mockup, marketing_flyer."""

    case_id: pxt.String
    batch_id: pxt.String | None
    workflow: pxt.String  # ui_mockup | marketing_flyer

    gen_prompt: pxt.String  # sent to the image model
    prompt: pxt.String      # shown to the judge
    criteria: pxt.String
    required_text: pxt.Json | None  # marketing only

    eval_ready: pxt.Bool

    image = pxtf.openai.image_generations(
        gen_prompt, model=GEN_MODEL, model_kwargs={'size': GEN_SIZE}
    )['data'][0]


class Edits(TableModel, name='edits'):
    """Image-edit rows: virtual_try_on, logo_edit."""

    case_id: pxt.String
    batch_id: pxt.String | None
    workflow: pxt.String  # virtual_try_on | logo_edit

    gen_prompt: pxt.String  # edit instruction for the model
    prompt: pxt.String      # shown to the judge
    criteria: pxt.String

    ref_image: pxt.Image
    ref_image_2: pxt.Image | None  # optional second reference (try-on)

    eval_ready: pxt.Bool

    image = pxtf.gemini.generate_content(
        udfs.edit_contents(ref_image, ref_image_2, gen_prompt),
        model=EDIT_MODEL,
        config=_EDIT_CONFIG,
    ).candidates[0].content.parts[0].inline_data.data.astype(pxt.Image)


class GenEvals(TableModel, name='gen_evals', base=Generations.where(Generations.eval_ready == True)):  # noqa: E712
    """Judge view for generations, including the marketing exact-text check."""

    judge_raw = pxtf.openai.responses(
        [
            {
                'role': 'user',
                'content': [
                    {'type': 'input_text', 'text': udfs.judge_user_text(Generations.prompt, Generations.criteria)},
                    {'type': 'input_image', 'image_url': Generations.image},
                ],
            }
        ],
        model=JUDGE_MODEL,
        model_kwargs={
            'instructions': udfs.judge_instructions(Generations.workflow),
            'text': udfs.judge_text_format(Generations.workflow),
        },
    )
    scores = udfs.parse_json(judge_raw.output.filter(lambda o: o.type == 'message')[0].content[0].text)
    judge_verdict = scores.verdict
    reason = scores.reason

    extracted_text = udfs.extract_flyer_text(Generations.image, Generations.workflow, JUDGE_MODEL)
    text_check = udfs.compare_required_text(extracted_text, Generations.required_text)
    verdict = udfs.finalize_verdict(Generations.workflow, scores, text_check)
    tags = udfs.failure_tags(Generations.workflow, scores, text_check)


class EditEvals(TableModel, name='edit_evals', base=Edits.where(Edits.eval_ready == True)):  # noqa: E712
    """Judge view for edits. No exact-text check."""

    judge_raw = pxtf.openai.responses(
        [
            {
                'role': 'user',
                'content': udfs.edit_judge_content(
                    Edits.prompt, Edits.criteria, Edits.ref_image, Edits.ref_image_2, Edits.image
                ),
            }
        ],
        model=JUDGE_MODEL,
        model_kwargs={
            'instructions': udfs.judge_instructions(Edits.workflow),
            'text': udfs.judge_text_format(Edits.workflow),
        },
    )
    scores = udfs.parse_json(judge_raw.output.filter(lambda o: o.type == 'message')[0].content[0].text)
    judge_verdict = scores.verdict
    reason = scores.reason

    verdict = udfs.finalize_verdict(Edits.workflow, scores, None)
    tags = udfs.failure_tags(Edits.workflow, scores, None)
