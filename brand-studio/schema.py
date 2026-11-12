"""Brand collaborations: two brand kits, a campaign theme, and ideas in; campaign visuals out.

- `brands`: one row per brand kit. Your own brand has `house = True`; every other brand is a partner.
- `campaigns`: one row per collab campaign: the partner, the theme, and the creative direction.
- `ideas`: one row per idea for a campaign. Gemini reads both brand kits, the campaign, and the idea,
  and writes two prompts. Nano Banana Pro makes the scene from the first, then edits the logos into
  it from the second. Gemini signs it off. All of it is stored on the idea's own row.

Every prompt is a column, built from other columns with `pxtf.string.format`.

    pxt schema diff schema.py collabs
    pxt schema update schema.py collabs -f
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

import udfs

TableModel = pxt.model_base()

TEXT_MODEL = 'gemini-3.8-flash'
DIRECTOR_MODEL = 'gemini-3.1-pro-preview'  # writes the visual prompts and reviews the images
IMAGE_MODEL = 'gemini-3-pro-image'

IMAGE_CONFIG = {'response_modalities': ['IMAGE'], 'image_config': {'aspect_ratio': '9:16', 'image_size': '2K'}}

# How a brand looks in photographs, read once from its style guide.
ART_DIRECTION = (
    'Read these brand guidelines and describe, in one short paragraph, how this brand looks in photographs: '
    'its light, colors, surfaces, props, mood, and what it never shows.\n\n{style_guide}'
)

# How the logos are made in each material, written as what the camera sees. Each visual is made in two
# steps: the scene with a plain surface, then an edit that makes the logos in that surface.
CRAFT = """How the logos are made, by material. For each, first the plain surface, then the logos in it:
- Steam on a mirror. Plain: thick white condensation covers the whole mirror in one unbroken, even layer, from the center out to all four edges of its frame, the way a mirror fogs after a long hot shower. The fog is dense and milky, a bright, pale white like frosted glass, and the room behind it shows only as faint pale shapes. Logos: the condensation is gone inside the letter shapes, as if the mirror had stayed dry there. Each letter is a clear window in the fog that shows the sharp reflection of the room, in its full, deeper color, much darker than the white fog around it. Its edge is the soft line where the condensation stops. The fog everywhere else stays as it is.
- Tile, stitches, or beads. Plain: the surface in one color, in a regular grid. Logos: the letters are tiles (or stitches, or beads) of a second color, much darker or much lighter than the first, laid in the same grid.
- Thread, ink, or a mold. Plain: the blank label, mat, or bar. Logos: the letters are woven into the label, printed into the fibers, or pressed into the soap, and the material's own texture runs through them.
In every material, the logos are the strongest contrast in the photograph, easy to read at a glance from across a room."""

# The creative director's brief. Gemini turns the inputs into two prompts for Nano Banana Pro: one
# for the scene, and one for the edit that makes the logos in it. The letters themselves are never
# drawn by a model: code places the real logos on the scene as a guide, and the edit gives them the material.
DIRECTOR = (
    """You are the creative director for a brand collaboration between {house} and {partner}. Write the two prompts that Nano Banana Pro will use to make one campaign photograph.

The job of the photograph is to show the two logos together: "{house}" above "{partner}", with a small "×" between them to mark the collaboration. The logos are made from something real in the scene. The idea below says what.

The campaign theme: {theme}
The creative direction: {direction}
This visual: {idea}

How {house} looks: {house_look}
How {partner} looks: {partner_look}
Use the two looks for the palette, surfaces, light, and props. Where they differ, follow the creative direction. The two attached pictures are the brand boards.

"""
    + CRAFT
    + """

The photograph is made in two steps, so write two prompts, in plain, concrete words for what the camera sees.

scene_prompt, 100 to 150 words: the photograph before the logos are made. Open with the surface that will carry them, plain and unmarked, the same from edge to edge, filling most of the frame with its edges visible. Shoot the surface square-on, so it sits flat in the frame like a poster: a mirror or a wall from straight in front, a floor or a mat from directly above. A mirror reflects the room, with no camera in it. Then the room around it, with at most two props, the light, and the camera: lens and aperture. Say that it is a clean, immaculate, photoreal still life for a luxury beauty campaign, with no people. The photograph is vertical, 9:16.

logo_prompt, 50 to 90 words: an instruction to edit that photograph. Nano Banana Pro gets two images: first the photograph, then a guide, which is the same photograph with the logos marked on the surface in flat magenta. Tell it to return the first photograph unchanged, except inside the magenta shapes of the guide, at exactly their position, size, and outline. Say what the surface becomes inside those shapes, physically, as the material guidance above describes it, and that no magenta is left in the result.

surface: the surface that carries the logos, in a few words, as the scene prompt names it, such as "the fogged glass of the mirror"."""
)

DIRECTOR_SCHEMA = {
    'type': 'object',
    'properties': {
        'scene_prompt': {'type': 'string'},
        'logo_prompt': {'type': 'string'},
        'surface': {'type': 'string'},
    },
    'required': ['scene_prompt', 'logo_prompt', 'surface'],
}

# Where the surface is in the scene, so the logos can be placed on it. Gemini's own box convention.
LOCATE = (
    'Find {surface} in this photograph. Return the box around the surface itself, inside any frame or border, '
    'as ymin, xmin, ymax, xmax: whole numbers from 0 to 1000, as fractions of the image height and width.'
)

BOX_SCHEMA = {
    'type': 'object',
    'properties': {k: {'type': 'integer'} for k in ('ymin', 'xmin', 'ymax', 'xmax')},
    'required': ['ymin', 'xmin', 'ymax', 'xmax'],
}

# The sign-off. The house brand's chief marketing officer looks at each shot and decides whether it goes in the
# campaign: true to both brands, true to the campaign, logos right, and restrained.
REVIEW = """You are the founding chief marketing officer of {house}, signing off the creative for your collaboration with {partner}. You know both brands well, and you protect both. Your taste is restraint: a clear point of view, one signature look for the campaign, and nothing in the frame that does not earn its place.

Image 1 is the shot. Image 2 is the {house} logo and Image 3 is the {partner} logo. The letter shapes in the shot were traced from these two logo files, so they are correct: do not judge the typeface or the letter shapes.

The campaign theme: {theme}
The creative direction: {direction}
The idea for this shot: {idea}

How {house} looks: {house_look}
How {partner} looks: {partner_look}
The two brands differ in places. The creative direction is the agreed blend, so judge each brand's look through it.

Look at the shot the way you would in a creative review, and answer each question with yes or no and one short note on what you see:
- house: is the shot true to {house}?
- partner: is the shot true to {partner}?
- campaign: does it deliver the theme and the creative direction?
- logos: can you read "{house}", the small "×", and "{partner}" at a glance, as the first thing you see in the shot, and do they look physically made from the scene as the idea describes, not etched, printed, or laid over the photo?
- restraint: is it clean, uncluttered, and free of people and of any other words?

Then list what you would ask the studio to fix, most important first. Approve the shot only if every answer is yes."""

_ANSWER = {'type': 'object', 'properties': {'yes': {'type': 'boolean'}, 'note': {'type': 'string'}}, 'required': ['yes', 'note']}

REVIEW_SCHEMA = {
    'type': 'object',
    'properties': {
        'house': _ANSWER,
        'partner': _ANSWER,
        'campaign': _ANSWER,
        'logos': _ANSWER,
        'restraint': _ANSWER,
        'fixes': {'type': 'array', 'items': {'type': 'string'}},
        'approved': {'type': 'boolean'},
    },
    'required': ['house', 'partner', 'campaign', 'logos', 'restraint', 'fixes', 'approved'],
}


# ---------------------------------------------------------------------------
# Brand kits
# ---------------------------------------------------------------------------


class Brands(TableModel, name='brands'):
    brand = pxt.Column(type=pxt.String, primary_key=True)
    name: pxt.String  # spelled and cased exactly as it must appear
    house: pxt.Bool  # True for your own brand
    category: pxt.String
    palette: pxt.Json  # a list of {role, name, hex}
    type_spec: pxt.Json  # typefaces per role, and how the wordmark looks
    headline_font: pxt.Binary
    accent_font: pxt.Binary
    body_font: pxt.Binary
    logo: pxt.Image
    style_guide: pxt.String

    board = udfs.brand_board(name, category, palette, type_spec, headline_font, accent_font, body_font, logo)
    art_direction_prompt = pxtf.string.format(ART_DIRECTION, style_guide=style_guide)
    art_direction_response = pxtf.gemini.generate_content(art_direction_prompt, model=TEXT_MODEL)
    art_direction = art_direction_response.candidates[0].content.parts[0].text.astype(pxt.String)


@pxt.query
def house_kit():
    """Your own brand's kit."""
    return Brands.where(Brands.house == True).select(  # noqa: E712
        name=Brands.name,
        logo=Brands.logo,
        board=Brands.board,
        look=Brands.art_direction,
        wordmark=Brands.type_spec.wordmark.look.astype(pxt.String),
    ).limit(1)


@pxt.query
def brand_kit(brand: str):
    """A partner's kit."""
    return Brands.where(Brands.brand == brand).select(
        name=Brands.name,
        logo=Brands.logo,
        board=Brands.board,
        look=Brands.art_direction,
        wordmark=Brands.type_spec.wordmark.look.astype(pxt.String),
    ).limit(1)


# ---------------------------------------------------------------------------
# Campaigns: your brand and one partner, with a theme and a creative direction
# ---------------------------------------------------------------------------


class Campaigns(TableModel, name='campaigns'):
    campaign = pxt.Column(type=pxt.String, primary_key=True)
    partner: pxt.String  # the partner brand's key in `brands`
    theme: pxt.String  # the shared idea behind the collab, in plain words
    direction: pxt.String  # the look: setting, materials, light, and mood, in plain words


@pxt.query
def campaign_brief(campaign: str):
    """A campaign's partner, theme, and creative direction."""
    return Campaigns.where(Campaigns.campaign == campaign).select(
        partner=Campaigns.partner, theme=Campaigns.theme, direction=Campaigns.direction
    ).limit(1)


# ---------------------------------------------------------------------------
# Ideas: one row per campaign visual. Add as many as you like, any time; only new rows run.
# ---------------------------------------------------------------------------


class Ideas(TableModel, name='ideas'):
    id = pxt.Column(value=pxtf.uuid.uuid7(), primary_key=True)
    campaign: pxt.String  # the campaign's key in `campaigns`
    idea: pxt.String  # the visual, in plain words

    brief = campaign_brief(campaign)
    house = house_kit()
    guest = brand_kit(brief['partner'])

    # 1. Gemini, as creative director, writes two prompts from the inputs: the scene, and the logos in it.
    director_prompt = pxtf.string.format(
        DIRECTOR,
        house=house['name'],
        partner=guest['name'],
        house_look=house.look,
        partner_look=guest.look,
        theme=brief.theme,
        direction=brief.direction,
        idea=idea,
    )
    director_response = pxtf.gemini.generate_content(
        [director_prompt, house.board, guest.board],
        model=DIRECTOR_MODEL,
        config={'response_mime_type': 'application/json', 'response_json_schema': DIRECTOR_SCHEMA},
    )
    prompts = udfs.parse_json(director_response.candidates[0].content.parts[0].text.astype(pxt.String))
    scene_prompt = prompts['scene_prompt'].astype(pxt.String)
    logo_prompt = prompts['logo_prompt'].astype(pxt.String)
    surface = prompts['surface'].astype(pxt.String)

    # 2. Nano Banana Pro makes the scene, with a plain surface and no logos yet.
    scene_response = pxtf.gemini.generate_content(scene_prompt, model=IMAGE_MODEL, config=IMAGE_CONFIG)
    scene = udfs.first_image(scene_response)

    # 3. Code places the real logos on the scene. Gemini says where the surface is; Pillow builds the
    #    lockup from both logos and marks it on the surface in flat magenta. No model draws a letter.
    locate_prompt = pxtf.string.format(LOCATE, surface=surface)
    locate_response = pxtf.gemini.generate_content(
        [scene, locate_prompt],
        model=TEXT_MODEL,
        config={'response_mime_type': 'application/json', 'response_json_schema': BOX_SCHEMA},
    )
    surface_box = udfs.parse_json(locate_response.candidates[0].content.parts[0].text.astype(pxt.String))
    house_stencil = udfs.logo_stencil(house.logo)
    guest_stencil = udfs.logo_stencil(guest.logo)
    lockup = udfs.logo_lockup(house_stencil, guest_stencil)
    guide = udfs.logo_guide(scene, lockup, surface_box)

    # 4. Nano Banana Pro edits the scene: inside the marked shapes, the surface becomes the material.
    image_response = pxtf.gemini.generate_content([scene, guide, logo_prompt], model=IMAGE_MODEL, config=IMAGE_CONFIG)
    image = udfs.first_image(image_response)

    # 5. Gemini, as the house brand's CMO, signs off the shot against both brands and the campaign.
    review_prompt = pxtf.string.format(
        REVIEW,
        house=house['name'],
        partner=guest['name'],
        house_look=house.look,
        partner_look=guest.look,
        theme=brief.theme,
        direction=brief.direction,
        idea=idea,
    )
    review_response = pxtf.gemini.generate_content(
        [image, house.logo, guest.logo, review_prompt],
        model=DIRECTOR_MODEL,
        config={'response_mime_type': 'application/json', 'response_json_schema': REVIEW_SCHEMA},
    )
    review = udfs.parse_json(review_response.candidates[0].content.parts[0].text.astype(pxt.String))
    approved = review['approved'].astype(pxt.Bool)
