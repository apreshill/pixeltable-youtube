"""Marketing flyer judge prompt, schema, and gate rules.

Loaded by udfs when workflow == 'marketing_flyer'.
"""

SYSTEM_PROMPT = """\
<core_mission>
Evaluate whether a generated marketing flyer is usable for a real coffee shop
promotion by checking instruction adherence, exact text correctness, layout clarity,
style fit, and artifact severity.
</core_mission>

You are an expert evaluator of marketing design deliverables.
You care about correctness, readability, hierarchy, and brand-fit.
You do NOT reward creativity that violates constraints.

<scope_constraints>
- Judge ONLY against the provided prompt and criteria.
- Be strict about required copy: spelling, punctuation, casing, and symbols must match exactly.
- Extra or missing text is a serious error.
- If unsure, score conservatively (lower score).
</scope_constraints>

1) instruction_following: PASS/FAIL
2) text_rendering: PASS/FAIL
3) layout_hierarchy: 0-5
4) style_brand_fit: 0-5
5) visual_quality: 0-5

Use these anchors:
Layout/Hierarchy 5 = instantly readable; clear order; strong spacing/alignment.
3 = understandable but needs iteration (one clear issue).
0-2 = confusing or hard to parse.

Style/Brand Fit 5 = clearly matches requested vibe; consistent; not off-style.
3 = generally matches but with noticeable mismatch.
0-2 = wrong style (e.g. cartoonish when photo-real requested).

Visual Quality 5 = clean; no distracting artifacts; hero image coherent.
3 = minor artifacts but still usable.
0-2 = obvious artifacts or distortions that break usability.

<verdict_rules>
Overall verdict is FAIL if:
- instruction_following is FAIL, OR
- text_rendering is FAIL, OR
- any of layout_hierarchy/style_brand_fit/visual_quality is < 3.
Otherwise PASS.
</verdict_rules>

<output_constraints>
Return JSON only.
No extra text.
</output_constraints>
"""

SCHEMA_NAME = 'marketing_flyer_eval'

JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        'verdict': {'type': 'string'},
        'instruction_following': {'type': 'boolean'},
        'text_rendering': {'type': 'boolean'},
        'layout_hierarchy': {'type': 'number'},
        'style_brand_fit': {'type': 'number'},
        'visual_quality': {'type': 'number'},
        'reason': {'type': 'string'},
    },
    'required': [
        'verdict',
        'instruction_following',
        'text_rendering',
        'layout_hierarchy',
        'style_brand_fit',
        'visual_quality',
        'reason',
    ],
    'additionalProperties': False,
}


def finalize_verdict(scores: dict, text_check: dict | None = None) -> str:
    if not scores.get('instruction_following'):
        return 'FAIL'
    if not scores.get('text_rendering'):
        return 'FAIL'
    for key in ('layout_hierarchy', 'style_brand_fit', 'visual_quality'):
        if float(scores.get(key) or 0) < 3:
            return 'FAIL'
    if text_check is not None and not text_check.get('pass'):
        return 'FAIL'
    return 'PASS'


def failure_tags(scores: dict, text_check: dict | None = None) -> list[str]:
    tags: list[str] = []
    if not scores.get('instruction_following'):
        tags.append('instruction_miss')
    if not scores.get('text_rendering'):
        tags.append('text_garbled')
    if text_check and not text_check.get('pass'):
        tags.append('exact_text_mismatch')
    if float(scores.get('style_brand_fit') or 0) < 3:
        tags.append('brand_mismatch')
    if float(scores.get('visual_quality') or 0) < 3:
        tags.append('artifacts')
    return tags
