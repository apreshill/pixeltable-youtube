"""Sample rows for the brand studio: two invented beauty brands, their products, moments, and a campaign.

ORIEL and brume are made up for this tutorial. Their fonts are Google Fonts
under the SIL Open Font License, their wordmarks are drawn by
scripts/make_logos.py, and their library photos were made once by
scripts/make_library.py.
"""

from pathlib import Path

KITS = Path(__file__).parent / 'brand_kits'


def _read(path: Path) -> bytes:
    return path.read_bytes()


def brand_row(slug: str) -> dict:
    """One brands row, read from brand_kits/<slug>/."""
    kit = KITS / slug
    spec = BRANDS[slug]
    return {
        'brand': slug,
        'name': spec['name'],
        'category': spec['category'],
        'palette': spec['palette'],
        'type_spec': spec['type_spec'],
        'headline_font': _read(kit / spec['fonts']['headline']),
        'accent_font': _read(kit / spec['fonts']['accent']),
        'body_font': _read(kit / spec['fonts']['body']),
        'logo_dark': str(kit / 'logo-dark.png'),
        'logo_light': str(kit / 'logo-light.png'),
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
            # What the wordmark is made of, so a moment can say whether its material can carry it.
            'wordmark': {'style': 'geometric caps'},
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
            'wordmark': {'style': 'monospace'},
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
}

# The brand's own photography. Each prompt below made one file in brand_kits/<brand>/library/.
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


def library_rows() -> list[dict]:
    return [{'brand': r['brand'], 'note': r['note'], 'image': str(KITS / r['brand'] / 'library' / r['file'])} for r in LIBRARY]


PRODUCTS = [
    {
        'sku': 'oriel-skin-tint',
        'brand': 'oriel',
        'name': 'Daylight Skin Tint',
        'packaging': (
            'A 30 ml frosted glass dropper bottle with rounded shoulders, a matte Apricot (#E9A47F) rubber dropper '
            'bulb on a slim matte Linen-colored collar (no gold or metal), and a small Espresso ORIEL wordmark printed on the front.'
        ),
    },
    {
        'sku': 'oriel-sun-balm',
        'brand': 'oriel',
        'name': 'Sun Balm',
        'packaging': (
            'A squat, round, matte Linen (#F4EDE3) compact about 5 cm wide, with the ORIEL wordmark debossed on '
            'the lid. The lid rests beside it, showing a soft apricot balm inside.'
        ),
    },
    {
        'sku': 'brume-scalp-oil',
        'brand': 'brume',
        'name': 'Pre-Wash Scalp Oil',
        'packaging': (
            'A 50 ml frosted, softly sage-tinted (#8DA290) glass bottle with a brushed nickel dropper collar and '
            'the lowercase typewriter-style brume wordmark printed in Slate on the front.'
        ),
    },
    {
        'sku': 'brume-hair-mist',
        'brand': 'brume',
        'name': 'Weightless Hair Mist',
        'packaging': (
            'A slim, tall, matte Fog-colored (#E8EAE5) aluminum spray bottle with a brushed nickel cap and the '
            'lowercase typewriter-style brume wordmark printed in Slate on the front.'
        ),
    },
]

# ---------------------------------------------------------------------------
# Directions: the creative playbook, one row per look. Every {slot} is filled
# from the brand kits, the campaign's set, and the moment.
# ---------------------------------------------------------------------------

HOUSE_RULES = [
    'No people: no faces, hands, hair on a head, bodies, silhouettes, or reflections of people.',
    'No words, letters, or logos anywhere except the brand wordmarks where a shot asks for them, '
    'and the printed labels on products.',
    'It must look like a real photograph from a high-end beauty campaign, shot on location in a room that was '
    'designed or carefully restored, then dressed by a prop stylist. Real materials keep their natural character (the '
    'veining of stone, the hand-glazed variation of zellige, the weave of linen), with real light and real lens depth '
    'of field. Never a 3D render.',
    'Vintage or modern, everything is spotless and cared for: no dirt, grime, stains, water marks, rust, mold, chips, '
    'cracks, dark or dirty grout, peeling paint, dust, or clutter.',
    'Every frame is composed like an editorial still life: calm, considered, with generous negative space, '
    'and nothing in it by accident.',
    'The words are made the way a craftsperson would really make them in that material, within its physical limits. '
    'Nothing is painted, printed, or pasted on unless the moment says so.',
]

# The camera, so every image reads as a beauty editorial photograph and not a rendering.
CAMERA = (
    'Photographed for a beauty editorial on a medium-format digital camera with an 80mm lens at f/4, soft and '
    'flattering natural light, clean true-to-life color, and crisp detail.'
)

SET_PROMPT = """You are the set designer for a beauty campaign photographed as still lifes, with no people.
Design one room that every shot of the campaign happens in: a bathroom whose look comes from the brands' own art direction below, their materials, light, colors, and mood. Vintage or modern, the room is immaculate and beautifully kept, the kind of room an interiors magazine would photograph. Then dress it for the brands.

Campaign: {brief}

The brands:
{brands}

{pairing}

The room must have everything these shots need. Describe it as it stands before any lettering is added:
{needs}

House rules:
{house_rules}

Return the palette you used, with each color tied to the surfaces it covers."""

PLATE_PROMPT = """A photograph of the empty room for {lockup}: wide, straight on, at eye level, so the whole room is visible.
{world}

House rules:
{house_rules}
No products, and no words, letters, or logos anywhere: the floor, the mirror, and every surface are blank."""

BASE_PROMPT = """A still-life photograph for {lockup}, taken in the attached room: the same walls, colors, materials, and hardware.
{world}

The subject: {subject}
Before any lettering: {blank}
Framing: {framing}
Styling: {products}

House rules:
{house_rules}
No words, letters, or logos anywhere except the printed labels on products.
Never show: {never}."""

LETTER_PROMPT = """Edit the attached photograph. Keep everything in it exactly as it is: the same camera, framing, light, room, objects, and colors. Change only one thing: add the brand names.
The words: {treatment}
How they are really made: {physics}
Every wordmark is copied exactly from its attached logo: the same letters, case, and typeface. The names are {names}. Never change a letter, add an accent, or swap a typeface.
No other words anywhere.

House rules:
{house_rules}"""

REVIEW_PROMPT = """You are the brand reviewer for {names}. Read every word in this picture, letter by letter, including small labels.
The brand names must appear spelled and cased exactly as {names}, with no added accents or marks.
They should appear like this: {treatment}
They must be physically made like this: {physics}
The subject should be: {subject}
Check realism with these concrete failures: objects pasted in like cutouts or cards, duplicated objects, warped or impossible geometry, text that sits on top of a surface instead of being made from it, letters that are not made the way the description above says, and smooth plastic surfaces that look computer-rendered. If none of these are present, it passes.
Product labels may carry their own printed text, such as the brand name, product name, and volume. No other words are allowed anywhere else.

House rules:
{house_rules}
Never allowed: {never}.

Sort every problem you find into one of two lists.
Look at the room as a luxury brand's creative director would. Vintage or modern, it must look spotless, cared for, and beautifully styled.
Blocking, the shot cannot ship: a brand name misspelled or in the wrong typeface, a person or part of one, words that are not brand names or product labels, brand names that are not made from the material as described, objects pasted in like cutouts, anything that looks dirty, worn, or neglected (grime, stains, water marks, rust, mold, chipped or cracked tiles, dark or dirty grout, peeling paint, dust, clutter), or the brand's never list broken in a way a viewer would notice.
Minor, note it but do not block: small artifacts in background objects, slightly soft small print, light that is a little off.
Approve if and only if the blocking list is empty."""

CLIP_REVIEW_PROMPT = """You are the brand reviewer for {names}. Watch this whole clip, frame by frame.
It should show: {subject}
The motion asked for: {motion}
Whenever the brand names are visible, they must stay sharp and spelled exactly as {names}. They may appear or disappear only if the motion asks for it.
List anything that appears from nowhere, vanishes, warps, melts, or moves in a way a real object would not.

House rules:
{house_rules}

Approve only if the words hold, the motion matches, and nothing glitches."""

LOCKUP = 'stacked on two lines with a small × between them'

DIRECTIONS = [
    {
        'direction': 'monochrome-set',
        'description': 'One bold, tone-on-tone room in a brand color, styled like a quiet luxury still life.',
        'set_prompt': SET_PROMPT,
        'plate_prompt': PLATE_PROMPT + '\nSoft, natural morning light from a window. ' + CAMERA,
        'base_prompt': BASE_PROMPT + '\nSoft, natural morning light from a window. ' + CAMERA,
        'letter_prompt': LETTER_PROMPT,
        'review_prompt': REVIEW_PROMPT,
        'clip_review_prompt': CLIP_REVIEW_PROMPT,
        'house_rules': HOUSE_RULES,
        'pairing': (
            "This is a collaboration. Give the room one bold, saturated main color from the first brand's palette, "
            'used on nearly every surface, tone on tone: walls, paneling, door, vanity, and textiles. Use the second '
            "brand's palette for one strong accent, such as the towels or the vanity stone, so both brands are visible."
        ),
        'solo': (
            "Give the room one bold, saturated main color from the brand's palette, used on nearly every surface, "
            'tone on tone: walls, paneling, door, vanity, and textiles, with one accent from the same palette.'
        ),
        'lockup': LOCKUP,
    },
    {
        'direction': 'macro-detail',
        'description': 'The same moments, shot as tight macro details: the words and their material fill the frame.',
        'set_prompt': SET_PROMPT,
        'plate_prompt': PLATE_PROMPT + '\nSoft, natural morning light from a window. ' + CAMERA,
        'base_prompt': BASE_PROMPT.replace(
            'Framing: {framing}',
            'Framing: a much tighter version of this: {framing} Move in with a 120mm macro lens until the words and '
            'the material they are made from fill most of the frame, and everything else falls into soft blur.',
        )
        + '\nSoft, natural morning light from a window. ' + CAMERA.replace('an 80mm lens at f/4', 'a 120mm macro lens at f/2.8'),
        'letter_prompt': LETTER_PROMPT,
        'review_prompt': REVIEW_PROMPT,
        'clip_review_prompt': CLIP_REVIEW_PROMPT,
        'house_rules': HOUSE_RULES,
        'pairing': (
            "This is a collaboration. Give the room one main color from the first brand's palette on nearly every "
            "surface, and use the second brand's palette for one strong accent, so both brands are visible."
        ),
        'solo': "Give the room one main color from the brand's palette on nearly every surface.",
        'lockup': LOCKUP,
    },
]

# ---------------------------------------------------------------------------
# Moments: one row per idea for putting the brand names into the world.
# {wordmarks} becomes one wordmark or two, so any moment works for any brand or pair.
# ---------------------------------------------------------------------------

MOMENTS = [
    {
        'moment': 'doormat',
        'fits': ['geometric caps', 'monospace', 'serif', 'script'],
        'physics': (
            "Ink printed into the coir: the stiff bristles poke through the ink, the letter edges are slightly fuzzy, and the print follows the mat's uneven surface. The mat is new and clean, and lies flat on the floor."
        ),
        'subject': 'A natural coir doormat on the floor in front of a closed paneled door.',
        'blank': 'The doormat is plain natural coir, with nothing printed on it.',
        'composite': None,
        'treatment': (
            'Printed into the coir in a dark brown and centered: {wordmarks}. The print sits in the coir fibers, '
            'slightly rough at the edges, like a real printed doormat. Nothing else is printed on the mat.'
        ),
        'framing': (
            'Vertical, seen from slightly above. The doormat fills the lower half of the frame, '
            'with the bottom of the door, its handle, and the floor around it.'
        ),
        'aspect_ratio': '9:16',
        'show_products': False,
        'motion': {
            'prompt': (
                'The camera pushes in steadily toward the doormat, ending clearly closer than it started. '
                'The printed words stay sharp and unchanged. Nothing else moves.'
            ),
            'shows': 'A steady push-in toward the doormat. The words stay sharp and unchanged.',
            'seconds': 4,
            'reverse': False,
        },
    },
    {
        'moment': 'towel_label',
        'fits': ['geometric caps', 'monospace', 'serif', 'script'],
        'physics': (
            'A separate fabric label sewn on with visible stitches along its edges. The letters are woven thread, slightly soft at the edges because of the weave, and the label puckers a little where it is stitched.'
        ),
        'subject': 'A waffle-weave bath towel hanging from a hook on the paneled bathroom door.',
        'blank': 'A small plain white fabric label is sewn near the top edge of the towel, with nothing woven into it yet.',
        'composite': None,
        'treatment': (
            'A small white woven label is sewn near the top edge of the towel, with {wordmarks} woven into it in thin '
            'dark thread. The label is the only place with words.'
        ),
        'framing': (
            'Vertical, eye level, close: the towel fills the right half of the frame and the label is large enough '
            'to read, with the door paneling softly behind it.'
        ),
        'aspect_ratio': '9:16',
        'show_products': False,
        'motion': {
            'prompt': (
                'Fixed camera, no camera movement. The towel sways gently on its hook, as if a door just closed '
                'nearby, then settles. The label stays on the front of the towel, facing the camera, sharp and '
                'readable the whole time. Nothing else moves.'
            ),
            'shows': 'The towel sways gently and settles. The label stays visible and readable the whole time.',
            'seconds': 4,
            'reverse': False,
        },
    },
    {
        'moment': 'steam_mirror',
        'fits': ['geometric caps', 'monospace', 'serif', 'script'],
        'physics': (
            'The old soap-stencil trick: before the shower, the letters were stenciled onto the glass with a thin film of soap, so fog cannot form there. Now the whole mirror is covered in thick, grey-white fog, and the letters are the only clear places. Inside each letter you see a sharp reflection of the bright window behind the camera, so the letters read as glowing, lighter shapes in the duller fog, never dark or black. The letter shapes are exact, but their edges feather into the fog, beaded with tiny water drops, and a few drips run down through the fog from the bottoms of the letters. No ink, paint, sticker, or outline.'
        ),
        'subject': 'The vanity mirror above the sink, with the products standing on the vanity below it.',
        'blank': 'The whole mirror is evenly fogged with milky condensation and a few drips, with no marks or letters in the fog.',
        'composite': None,
        'treatment': (
            'The mirror glass is fogged with an even, milky layer of condensation and a few drips. Across the middle of '
            'the mirror, {wordmarks} show through the fog. The letters are not printed or painted: each one is clear '
            'glass where the fog was wiped away, soft at the edges, with the room faintly reflected inside it and a '
            'tiny drip at the bottom of some strokes. The letter shapes still match the logos.'
        ),
        'framing': (
            'Vertical, straight on. The fogged mirror fills the upper two thirds of the frame. '
            'The vanity, the sink, the taps, and the products fill the lower third.'
        ),
        'aspect_ratio': '9:16',
        'show_products': True,
        'motion': {
            'prompt': (
                'Fixed camera, no camera movement. The condensation on the mirror slowly evaporates, from the edges '
                'inward, until the glass is completely clear and the letters are gone. The vanity and the products '
                'stay still.'
            ),
            # The clip plays backwards, so the reviewer is told what the finished clip shows.
            'shows': (
                'The mirror starts clear. Fog slowly forms on it, and the brand names appear as the only clear places '
                'in the fog, ending sharp and readable. The vanity and the products stay still.'
            ),
            'seconds': 5,
            'reverse': True,
        },
    },
    {
        'moment': 'tile_floor',
        # Inlay cuts any letter shape, but the fit guard keeps the tile moment to grid-friendly wordmarks.
        'fits': ['geometric caps', 'monospace'],
        'physics': (
            'The letters are inlaid. Each one was cut from matte tile in its ink color with a waterjet, to the exact logo shape, and set into the floor. The small floor tiles around it were cut to fit, leaving a fine joint around every letter. Inside a letter there is no grid. Nothing is painted, printed, or laid on top.'
        ),
        'subject': (
            'The bathroom floor just inside the door, laid in small, pale, matte square mosaic tiles, '
            'with grout the same pale color as the tiles, so the grid is quiet.'
        ),
        'blank': 'The floor is plain: every tile is the same pale color, with no letters, inlay, border, or pattern.',
        'composite': 'inlay',
        'treatment': (
            'Inlaid into the pale floor: {wordmarks}. The letters are matte tile in {letter_colors}, large, '
            'like the name set into the entrance floor of a grand hotel.'
        ),
        'framing': (
            'Vertical, looking straight down from standing height, so the tile grid runs square to the frame. '
            'The floor fills the frame, with the threshold and the bottom of the door along the top edge.'
        ),
        'aspect_ratio': '9:16',
        'show_products': False,
        'motion': {
            'prompt': 'The camera slowly rises straight up, still looking down at the floor lettering. Nothing else moves.',
            'shows': 'The camera rises slowly over the floor lettering. The letters stay sharp and unchanged.',
            'seconds': 4,
            'reverse': False,
        },
    },
    {
        'moment': 'soap_bar',
        'fits': ['geometric caps', 'monospace', 'serif', 'script'],
        'physics': (
            'Pressed into the soap by a mold: the letters are recessed, with soft rounded edges, and water sits in some of the letters. The soap is new and unused.'
        ),
        'subject': 'A fresh bar of soap resting on a small ceramic dish on the edge of the vanity, beside the tap.',
        'blank': 'The top of the soap is smooth, with nothing pressed into it.',
        'composite': None,
        'treatment': (
            '{wordmarks} pressed into the top of the soap, crisp and shallow, as if stamped by a mold. '
            'A few water droplets sit on the soap.'
        ),
        'framing': 'Vertical, close and slightly above. The soap fills the middle of the frame, with the tap softly behind it.',
        'aspect_ratio': '9:16',
        'show_products': False,
        'motion': {
            'prompt': (
                'Fixed camera, no camera movement. A few water droplets slowly run down the side of the soap, '
                'and a thin wisp of steam drifts past. Nothing else moves.'
            ),
            'shows': 'Droplets run down the soap and a wisp of steam drifts past. The pressed letters stay unchanged.',
            'seconds': 4,
            'reverse': False,
        },
    },
]

# ---------------------------------------------------------------------------
# Campaigns: any brand, or any two, through any direction and any moments.
# ---------------------------------------------------------------------------

ORIEL_SKUS = ['oriel-skin-tint', 'oriel-sun-balm']
BRUME_SKUS = ['brume-scalp-oil', 'brume-hair-mist']

CAMPAIGNS = [
    {
        'campaign': 'morning-edit',
        'brand': 'oriel',
        'partner': 'brume',
        'direction': 'monochrome-set',
        'skus': ORIEL_SKUS + BRUME_SKUS,
        'brief': (
            'ORIEL × brume: The Morning Edit, a limited collection for the first hour of the day. '
            'One shared bathroom at 7am, where skin care and hair care live side by side. It arrives Tuesday.'
        ),
        'moments': ['doormat', 'towel_label', 'steam_mirror', 'tile_floor'],
        'clips': True,
    },
    {
        'campaign': 'oriel-daylight',
        'brand': 'oriel',
        'partner': None,
        'direction': 'monochrome-set',
        'skus': ORIEL_SKUS,
        'brief': 'ORIEL Daylight: the new skin tint and sun balm, for skin that looks like skin in morning light.',
        'moments': ['steam_mirror', 'tile_floor'],
        'clips': False,
    },
    {
        'campaign': 'brume-slow-hair',
        'brand': 'brume',
        'partner': None,
        'direction': 'monochrome-set',
        'skus': BRUME_SKUS,
        'brief': 'brume Slow Hair: a five-minute scalp oil ritual before the shower, and a mist for after.',
        'moments': ['steam_mirror', 'tile_floor'],
        'clips': False,
    },
    {
        'campaign': 'morning-edit-details',
        'brand': 'brume',
        'partner': 'oriel',
        'direction': 'macro-detail',
        'skus': ORIEL_SKUS + BRUME_SKUS,
        'brief': 'brume × ORIEL: The Morning Edit, up close. The same bathroom, in details.',
        'moments': ['steam_mirror', 'soap_bar', 'tile_floor'],
        'clips': False,
    },
]

REELS = [
    {'reel': 'morning-edit-teaser', 'campaign': 'morning-edit', 'sequence': ['doormat', 'towel_label', 'steam_mirror']},
]
