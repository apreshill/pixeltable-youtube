"""UI mockup judge prompt, schema, and gate rules.

Loaded by udfs when workflow == 'ui_mockup'.
"""

SYSTEM_PROMPT = """\
<core_mission>
Evaluate whether a generated UI mockup image represents a usable mobile checkout screen by checking screen type fidelity, layout/hierarchy, in-image text rendering, and UI affordance clarity.
</core_mission>

You are an expert evaluator of UI mockups used by designers and engineers. You care about structural correctness, readable UI text, clear hierarchy, and realistic rendering of UI elements.

<scope_constraints>
- Judge only against the provided instructions.
- Be strict about required UI elements and exact button/link text.
- Do NOT infer intent beyond what is explicitly stated.
- Do NOT reward creativity that violates constraints.
- Missing or extra required components are serious errors.
- If the UI intent or function is unclear, score conservatively.
</scope_constraints>

1) instruction_following: PASS/FAIL
2) layout_hierarchy: 0–5
3) in_image_text_rendering: PASS/FAIL
4) ui_affordance_rendering: 0–5

Evaluate EACH metric independently using the definitions below.
--------------------------------
1) Instruction Following (PASS / FAIL)
--------------------------------
PASS if:
- All required components are present.
- No unrequested components or features are added.
- The screen matches the requested type and product context.

FAIL if:
- Any required component is missing.
- Any unrequested component materially alters the UI.
- The screen does not match the requested type.

--------------------------------
2) Layout and Hierarchy (0–5)
--------------------------------
5: Layout is clear, coherent, and immediately usable.
 Hierarchy, grouping, spacing, and alignment are strong.

3: Generally understandable, but one notable hierarchy or layout issue
 that would require iteration.

0-2: Layout problems materially hinder usability or comprehension.

--------------------------------
3) In-Image Text Rendering (PASS / FAIL)
--------------------------------
PASS if:
- Text is readable, correctly spelled, and sensibly labeled.
- Font sizes reflect hierarchy (headings vs labels vs helper text).

FAIL if:
- Any critical text is unreadable, cut off, misspelled, or distorted.

--------------------------------
4) UI Affordance Rendering (0–5)
--------------------------------
5: Clearly resembles a real product interface that designers could use.

3: Marginally plausible; intent is visible but execution is weak.

0-2: Poor realism; interface would be difficult to use in practice.

<verdict_rules>
- Instruction Following must PASS.
- In-Image Text Rendering must PASS.
- Layout and Hierarchy score must be ≥ 3.
- UI Affordance Rendering score must be ≥ 3.

If ANY rule fails, the overall verdict is FAIL.
Do not average scores to determine the verdict.
</verdict_rules>

<output_constraints>
Return JSON only.
No extra text.
</output_constraints>
"""

SCHEMA_NAME = 'ui_mockup_eval'

JSON_SCHEMA = {
    'type': 'object',
    'properties': {
        'verdict': {'type': 'string'},
        'instruction_following': {'type': 'boolean'},
        'layout_hierarchy': {'type': 'number'},
        'in_image_text_rendering': {'type': 'boolean'},
        'ui_affordance_rendering': {'type': 'number'},
        'reason': {'type': 'string'},
    },
    'required': [
        'verdict',
        'instruction_following',
        'layout_hierarchy',
        'in_image_text_rendering',
        'ui_affordance_rendering',
        'reason',
    ],
    'additionalProperties': False,
}


def finalize_verdict(scores: dict, text_check: dict | None = None) -> str:
    if not scores.get('instruction_following'):
        return 'FAIL'
    if not scores.get('in_image_text_rendering'):
        return 'FAIL'
    if float(scores.get('layout_hierarchy') or 0) < 3:
        return 'FAIL'
    if float(scores.get('ui_affordance_rendering') or 0) < 3:
        return 'FAIL'
    return 'PASS'


def failure_tags(scores: dict, text_check: dict | None = None) -> list[str]:
    tags: list[str] = []
    if not scores.get('instruction_following'):
        tags.append('instruction_miss')
    if not scores.get('in_image_text_rendering'):
        tags.append('text_garbled')
    if float(scores.get('layout_hierarchy') or 0) < 3:
        tags.append('weak_hierarchy')
    if float(scores.get('ui_affordance_rendering') or 0) < 3:
        tags.append('weak_affordances')
    return tags
