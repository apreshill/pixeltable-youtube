"""Virtual try-on judge prompt, schema, and gate rules.

Loaded by udfs when workflow == 'virtual_try_on'.
"""

SYSTEM_PROMPT = """\
<core_mission>
Evaluate whether a virtual try-on edit preserves the person while accurately applying the reference garment.
</core_mission>

You are an expert evaluator of virtual try-on outputs.
You focus on identity preservation, garment fidelity, and body-shape preservation.

1) facial_similarity: 0-5
2) outfit_fidelity: 0-5
3) body_shape_preservation: 0-5

<verdict_rules>
FAIL if any metric <= 2.
PASS if all metrics >= 3.
</verdict_rules>

<output_constraints>
Return JSON only with the fields specified in the schema.
</output_constraints>
"""

SCHEMA_NAME = 'vto_eval'

JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        'verdict': {'type': 'string'},
        'facial_similarity': {'type': 'number'},
        'outfit_fidelity': {'type': 'number'},
        'body_shape_preservation': {'type': 'number'},
        'reason': {'type': 'string'},
    },
    'required': [
        'verdict',
        'facial_similarity',
        'outfit_fidelity',
        'body_shape_preservation',
        'reason',
    ],
    'additionalProperties': False,
}


def finalize_verdict(scores: dict, text_check: dict | None = None) -> str:
    for key in ('facial_similarity', 'outfit_fidelity', 'body_shape_preservation'):
        if float(scores.get(key) or 0) <= 2:
            return 'FAIL'
    return 'PASS'


def failure_tags(scores: dict, text_check: dict | None = None) -> list[str]:
    tags: list[str] = []
    if float(scores.get('facial_similarity') or 0) <= 2:
        tags.append('identity_drift')
    if float(scores.get('outfit_fidelity') or 0) <= 2:
        tags.append('garment_mismatch')
    if float(scores.get('body_shape_preservation') or 0) <= 2:
        tags.append('body_warp')
    return tags
