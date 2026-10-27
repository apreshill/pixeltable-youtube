"""UDFs for the image-eval schema.

The provider calls live in schema.py as computed columns that use the built-in
Pixeltable functions, so the provider and model are part of the schema:
  - generations.image via pxtf.openai.image_generations (constant model)
  - edits.image via pxtf.gemini.generate_content (constant model)

These UDFs are the judge logic and one small data-prep helper:
  - edit_contents assembles the Gemini edit input (reference images then the
    instruction) and drops a missing second reference.
  - the judge helpers parse the judge JSON and apply each rubric's gates and tags.
  - extract_flyer_text reads the flyer copy for the marketing exact-text check.
    It calls the built-in openai.responses, and it runs only for marketing rows.

Editing uses Gemini because generate_content takes several reference images in
one call, which virtual try-on needs (person plus garment). The stock OpenAI
image-edit function takes a single image. See the README for the plan to move
editing to OpenAI once the multi-image edit path is confirmed against the live API.

Per-job gates/tags: use_cases/<name>/rubric.py
"""

import json

import pixeltable as pxt
import pixeltable.functions as pxtf
from PIL import Image

from use_cases.logo_edit import rubric as logo_rubric
from use_cases.marketing_flyer import rubric as marketing_rubric
from use_cases.marketing_flyer import text as marketing_text
from use_cases.ui_mockup import rubric as ui_rubric
from use_cases.virtual_try_on import rubric as vto_rubric

_RUBRICS = {
    'ui_mockup': ui_rubric,
    'marketing_flyer': marketing_rubric,
    'virtual_try_on': vto_rubric,
    'logo_edit': logo_rubric,
}

_OCR_INSTRUCTIONS = (
    'List every piece of text visible in this flyer image. '
    'Return one line per text item and preserve capitalization, punctuation, and spacing exactly.'
)


def _rubric(workflow: str):
    rubric = _RUBRICS.get(workflow)
    if rubric is None:
        raise ValueError(f'unsupported workflow: {workflow}')
    return rubric


@pxt.udf
def edit_contents(
    ref_image: Image.Image, ref_image_2: Image.Image | None, prompt: str | None
) -> list:
    """Build the Gemini edit input: reference images, then the instruction."""
    contents: list = [ref_image]
    if ref_image_2 is not None:
        contents.append(ref_image_2)
    contents.append(prompt or '')
    return contents


@pxt.udf
def edit_judge_content(
    prompt: str,
    criteria: str,
    ref_image: Image.Image,
    ref_image_2: Image.Image | None,
    image: Image.Image,
) -> list:
    """The edit judge's message: the instruction, the input images, then the edited result.

    An edit can only be graded against what it started from, so the judge sees the
    reference images too. The second reference is optional (try-on uses two, a logo edit one).
    """
    content: list = [{'type': 'input_text', 'text': f'Prompt:\n{prompt}\n\nCriteria:\n{criteria}'}]
    refs = [ref_image] if ref_image_2 is None else [ref_image, ref_image_2]
    labels = ['Input image, before the edit:'] if len(refs) == 1 else ['First input image:', 'Second input image:']
    for label, ref in zip(labels, refs):
        content += [{'type': 'input_text', 'text': label}, {'type': 'input_image', 'image_url': ref}]
    content += [
        {'type': 'input_text', 'text': 'Edited result to score:'},
        {'type': 'input_image', 'image_url': image},
    ]
    return content


@pxt.udf
def judge_instructions(workflow: str) -> str:
    return _rubric(workflow).SYSTEM_PROMPT


@pxt.udf
def judge_text_format(workflow: str) -> dict:
    rubric = _rubric(workflow)
    return {
        'format': {
            'type': 'json_schema',
            'name': rubric.SCHEMA_NAME,
            'schema': rubric.JSON_SCHEMA,
            'strict': True,
        }
    }


@pxt.udf
def judge_user_text(prompt: str, criteria: str) -> str:
    return f'Prompt:\n{prompt}\n\nCriteria:\n{criteria}\n\nScore the image.'


@pxt.udf
def parse_json(text: str | None) -> dict:
    """Turn the judge's JSON string into an object. After this, fields are native
    Pixeltable access, e.g. scores.verdict. Pixeltable has no native string-to-JSON
    parser, so this one json.loads is the only parse step."""
    if not text:
        return {}
    return json.loads(text)


@pxt.udf(is_deterministic=False)
async def extract_flyer_text(image: Image.Image, workflow: str, judge_model: str) -> list[str] | None:
    """Marketing only. Read the flyer copy with the built-in openai.responses."""
    if workflow != 'marketing_flyer':
        return None

    raw = await pxtf.openai.responses.aexec(
        [
            {
                'role': 'user',
                'content': [{'type': 'input_image', 'image_url': image}],
            }
        ],
        model=judge_model,
        model_kwargs={'instructions': _OCR_INSTRUCTIONS},
    )
    # output_text is an SDK convenience property, not a field of the stored response:
    # the text is in the message item's content.
    messages = [o for o in (raw or {}).get('output') or [] if o.get('type') == 'message']
    text = messages[0]['content'][0].get('text') if messages and messages[0].get('content') else None
    if not text:
        return []
    return [line.strip() for line in text.splitlines() if line.strip()]


@pxt.udf
def compare_required_text(extracted: list[str] | None, required_text: list | None) -> dict | None:
    if extracted is None or required_text is None:
        return None
    return marketing_text.compare_required(extracted, required_text)


@pxt.udf
def finalize_verdict(workflow: str, scores: dict | None, text_check: dict | None) -> str | None:
    if not scores:
        return None
    return _rubric(workflow).finalize_verdict(scores, text_check)


@pxt.udf
def failure_tags(workflow: str, scores: dict | None, text_check: dict | None) -> list[str]:
    if not scores:
        return []
    return _rubric(workflow).failure_tags(scores, text_check)
