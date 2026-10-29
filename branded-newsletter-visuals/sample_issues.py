"""Four public issues of Rami Krispin's data newsletter: the issue number and a short scene.

The schema puts `scene` into both prompts and turns the issue number into the
label on the cover.
"""

ISSUES = [
    {
        'issue_number': 111,
        'scene': (
            'A photoreal cinematic wide shot of a lush green mountain valley, '
            'a lone tree in the meadow, rocks in the foreground, and a bright sky '
            'with large white clouds.'
        ),
    },
    {
        'issue_number': 109,
        'scene': (
            "A painting based on Van Gogh's Starry Night: swirling blue and gold night sky, "
            'dark cypress trees, thick visible brushstrokes, a golden wheat field, and a '
            'brown horse standing in the wheat.'
        ),
    },
    {
        'issue_number': 106,
        'scene': (
            'A flat graphic poster of a snow-capped mountain, a red pagoda beside a lake, '
            'autumn trees, cream clouds, and a few red birds in the sky.'
        ),
    },
    {
        'issue_number': 93,
        'scene': (
            'Baby Yoda seated in a golden wheat field under a swirling starry night sky '
            'painted with thick brushstrokes, reaching one hand toward a bright star.'
        ),
    },
]
