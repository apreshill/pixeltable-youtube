"""Sample rows: three invented beauty brands and two collaboration campaigns.

ORIEL, brume, and wallow are made up for this tutorial. Their fonts are Google Fonts under the
SIL Open Font License, and their wordmarks are drawn by scripts/make_logos.py.
"""

from pathlib import Path

KITS = Path(__file__).parent / 'brand_kits'

# Your own brand. Every other brand is a partner.
HOUSE = 'oriel'


def brand_row(slug: str) -> dict:
    """One brands row, read from brand_kits/<slug>/."""
    kit = KITS / slug
    spec = BRANDS[slug]
    return {
        'brand': slug,
        'name': spec['name'],
        'house': slug == HOUSE,
        'category': spec['category'],
        'palette': spec['palette'],
        'type_spec': spec['type_spec'],
        'headline_font': (kit / spec['fonts']['headline']).read_bytes(),
        'accent_font': (kit / spec['fonts']['accent']).read_bytes(),
        'body_font': (kit / spec['fonts']['body']).read_bytes(),
        'logo': str(kit / 'logo-dark.png'),
        'style_guide': (kit / 'style_guide.md').read_text(),
    }


BRANDS = {
    'oriel': {
        'name': 'ORIEL',
        'category': 'Complexion and skin care',
        'palette': [
            {'role': 'background', 'name': 'Linen', 'hex': '#F4EDE3'},
            {'role': 'ink', 'name': 'Espresso', 'hex': '#33241D'},
            {'role': 'accent', 'name': 'Apricot', 'hex': '#E9A47F'},
            {'role': 'cta', 'name': 'Terracotta', 'hex': '#A9553A'},
            {'role': 'soft', 'name': 'Honey', 'hex': '#F3D7AE'},
        ],
        'type_spec': {
            # What the wordmark is made of, and how it looks in words, for prompts that describe the letters.
            'wordmark': {'style': 'geometric caps', 'look': 'thin, geometric sans-serif capitals with very wide letter spacing'},
            'headline': {'family': 'Jost Medium', 'weight': 500, 'leading': 1.02},
            'accent': {'family': 'Cormorant Garamond Medium Italic', 'weight': 500, 'scale': 1.18},
            'body': {'family': 'Jost Regular', 'weight': 400},
            'cta': {'weight': 500, 'case': 'upper', 'tracking': 0.2},
        },
        'fonts': {
            'headline': 'fonts/Jost-Variable.ttf',
            'accent': 'fonts/CormorantGaramond-Italic-Variable.ttf',
            'body': 'fonts/Jost-Variable.ttf',
        },
    },
    'brume': {
        'name': 'brume',
        'category': 'Hair rituals',
        'palette': [
            {'role': 'background', 'name': 'Fog', 'hex': '#E8EAE5'},
            {'role': 'ink', 'name': 'Slate', 'hex': '#1E2A2F'},
            {'role': 'accent', 'name': 'Sage', 'hex': '#8DA290'},
            {'role': 'cta', 'name': 'Moss', 'hex': '#4E5F50'},
            {'role': 'soft', 'name': 'Butter', 'hex': '#F0E5B5'},
        ],
        'type_spec': {
            'wordmark': {'style': 'monospace', 'look': 'lowercase monospaced letters, typewriter-like, spaced a little open'},
            'headline': {'family': 'Instrument Serif', 'leading': 0.98},
            'accent': {'family': 'Instrument Serif Italic', 'scale': 1.0},
            'body': {'family': 'DM Mono'},
            'cta': {'case': 'upper', 'tracking': 0.14},
        },
        'fonts': {
            'headline': 'fonts/InstrumentSerif-Regular.ttf',
            'accent': 'fonts/InstrumentSerif-Italic.ttf',
            'body': 'fonts/DMMono-Regular.ttf',
        },
    },
    'wallow': {
        'name': 'wallow',
        'category': 'Bath soaks and candles',
        'palette': [
            {'role': 'background', 'name': 'Tallow', 'hex': '#F2E8D5'},
            {'role': 'ink', 'name': 'Tobacco', 'hex': '#4A2E1F'},
            {'role': 'accent', 'name': 'Oxblood', 'hex': '#6E1F24'},
            {'role': 'cta', 'name': 'Amber', 'hex': '#C98A3B'},
            {'role': 'soft', 'name': 'Smoke', 'hex': '#CFC6BA'},
        ],
        'type_spec': {
            'wordmark': {'style': 'soft serif', 'look': 'plump, soft-cornered lowercase serif letters, set close together'},
            'headline': {'family': 'Fraunces', 'weight': 600, 'leading': 1.0},
            'accent': {'family': 'Fraunces Soft', 'weight': 400, 'scale': 1.0},
            'body': {'family': 'Work Sans', 'weight': 400},
            'cta': {'weight': 500, 'case': 'lower', 'tracking': 0.04},
        },
        'fonts': {
            'headline': 'fonts/Fraunces-Variable.ttf',
            'accent': 'fonts/Fraunces-Variable.ttf',
            'body': 'fonts/WorkSans-Variable.ttf',
        },
    },
}

# Campaigns: one row per collab, with its partner, theme, and creative direction, in plain words.
CAMPAIGNS = [
    {
        'campaign': 'morning-edit',
        'partner': 'brume',
        'theme': (
            'The Morning Edit, a limited collection for the first hour of the day, where ORIEL skin care and '
            'brume hair care live side by side.'
        ),
        'direction': (
            'One shared, steamy bathroom at 7am: warm terracotta plaster, white zellige, travertine, sage linens, '
            'and soft window light through the steam from the shower.'
        ),
    },
    {
        'campaign': 'stay-out-late',
        'partner': 'wallow',
        'theme': 'Stay Out Late, a limited collection for long summer evenings, from the last of the daylight to the first candle.',
        'direction': (
            'A clean vintage clawfoot bathtub outdoors in an English garden, with fresh-cut flowers, fine gingham, '
            'linen, and warm, low evening light.'
        ),
    },
]

# Ideas: one row per campaign visual. Gemini writes the prompt for each.
IDEAS = [
    {'campaign': 'morning-edit', 'idea': 'The steam on the bathroom mirror reveals both names as clean letters of clear glass, outlined by steam.'},
    {'campaign': 'morning-edit', 'idea': 'Both names woven into the label of a waffle-weave bath towel.'},
    {'campaign': 'morning-edit', 'idea': 'Both names printed into a natural coir doormat at the bathroom door.'},
    {'campaign': 'morning-edit', 'idea': 'Both names set into the bathroom floor in classic hexagon mosaic tile.'},
    {'campaign': 'stay-out-late', 'idea': 'Steam from the bath covers a vintage mirror propped in the garden, and both names show through the steam as clean letters of clear glass.'},
    {'campaign': 'stay-out-late', 'idea': 'Both names cross-stitched into a folded gingham cloth on a stool beside the tub.'},
    {'campaign': 'stay-out-late', 'idea': 'Both names woven into the label of a towel draped over the rim of the tub.'},
    {'campaign': 'stay-out-late', 'idea': 'Both names pressed into a bar of soap on a wooden bath rack across the tub.'},
]

# The brand's own photography: each prompt below made one file in brand_kits/<brand>/library/.
LIBRARY = [
    {
        'brand': 'oriel',
        'file': 'tint-swatch.jpg',
        'note': 'A sheer swatch of skin tint on warm limestone',
        'prompt': (
            'Macro beauty texture shot: a single sheer, dewy swatch of apricot-beige skin tint swept across warm '
            'limestone, with a few glossy droplets at its edge. Warm late-morning window light, with soft shadows of '
            'window panes crossing the stone. Colors of linen, honey, apricot, and terracotta. Photoreal, shallow '
            'depth of field. No people, no hands, no packaging, no text.'
        ),
    },
    {
        'brand': 'oriel',
        'file': 'travertine-still-life.jpg',
        'note': 'Travertine ledge with linen and dried grass in window light',
        'prompt': (
            'Still life on a travertine ledge against a warm plaster wall: a folded raw linen napkin and a sprig '
            'of dried grass in a small unglazed ceramic dish. Warm late-morning window light with soft shadows of '
            'window panes. Lots of calm negative space. Photoreal editorial. No products, no text.'
        ),
    },
    {
        'brand': 'oriel',
        'file': 'bay-window.jpg',
        'note': 'An empty bay window seat, sunlit through sheer curtains',
        'prompt': (
            'An empty cushioned seat in a large bay window, light pouring in from three sides through sheer linen '
            'curtains, a folded linen throw and a small ceramic cup on the cushion, warm plaster walls, warm honey '
            'and apricot tones, soft and calm, editorial interior photograph. No people, no text.'
        ),
    },
    {
        'brand': 'brume',
        'file': 'steam-mirror.jpg',
        'note': 'Steam and droplets on a bathroom mirror',
        'prompt': (
            'A steamy bathroom mirror covered in condensation and droplets above a white zellige tile wall and a '
            'brushed nickel faucet. Soft, cool morning light filtered through steam. Fog, sage, and slate tones. '
            'Photoreal, intimate, shallow depth of field. No people, no text.'
        ),
    },
    {
        'brand': 'brume',
        'file': 'scrunchie-basin.jpg',
        'note': 'A sage silk scrunchie on the edge of a wet porcelain basin',
        'prompt': (
            'Close editorial still life: a sage silk scrunchie resting on the wet rim of a white porcelain basin, '
            'water droplets beaded on the porcelain, a brushed nickel tap softly out of focus, steam hanging in the '
            'air. Soft, diffused, slightly cool morning light. Fog, sage, and slate palette with a small touch of '
            'butter yellow. Shallow depth of field. No people, no hands, no text.'
        ),
    },
    {
        'brand': 'brume',
        'file': 'nickel-and-stone.jpg',
        'note': 'Comb, eucalyptus, and a waffle towel on damp stone',
        'prompt': (
            'Still life on damp grey-green stone: a wide-tooth comb and a single eucalyptus stem beside a folded '
            'white waffle towel. Frosted glass and brushed nickel in the background, haze in the air, cool soft '
            'morning light. Photoreal editorial. No products, no text.'
        ),
    },
]
