"""Brand collaborations: two brand kits, a campaign theme, and ideas in; campaign visuals out.

- `brands`: one row per brand kit. Your own brand has `house = True`; every other brand is a partner.
- `campaigns`: one row per collab campaign: the partner, the theme, and the creative direction.
- `ideas`: one row per idea for a campaign. Gemini reads both brand kits, the campaign, and the idea,
  and writes the visual prompt. Nano Banana Pro makes the image from that prompt and both logos.
  Gemini reviews it. All of it is stored on the idea's own row.

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

# How the names are made in a material. The director writes to these rules and the reviewer checks
# them, so both work to the same standard.
CRAFT = """How the names are made, by material:
- Revealed in steam on glass: the letters are clean, exact letterforms in each brand's own typeface, as if the glass had been masked in their shape before the steam rose. Dense, even steam covers the whole glass from edge to edge, and the only clear glass anywhere is inside the letters: each letter is crisp, bare glass holding a sharp, full-color reflection of the room, outlined by the soft, milky steam around it. The letters have no color, ink, or thickness of their own; they are readable only because of the steam around them.
- Built from pieces, such as mosaic tile, cross-stitch, or beads: each letter is made only of whole pieces in a contrasting color, set into the same grid as the rest of the surface, with stepped edges where a curve meets the grid. The letters follow the logos as closely as whole pieces allow.
- Printed, woven, pressed, or stamped, such as ink in coir, thread in a label, or a mold in soap: the letters sit in the material, with its texture showing through them.
- In every case, the letters lie flat on the surface that carries them, in its perspective, and the edges of that surface are in the frame."""

# The creative director's brief. Gemini turns the inputs into one image prompt, following Google's
# Nano Banana prompting guide: a strong verb, a narrative scene, positive framing, camera and light,
# real materials, exact quoted text with its letterforms, and each reference image named.
DIRECTOR = (
    """You are the creative director for a brand collaboration between {house} and {partner}. Write the prompt that Nano Banana Pro will use to make one campaign visual.

The campaign theme: {theme}
The creative direction: {direction}
This visual: {idea}

How {house} looks: {house_look}
How {partner} looks: {partner_look}
The two attached pictures are the brand boards of {house} and {partner}: their logos, type, and palettes.

"""
    + CRAFT
    + """

Write one image prompt of 120 to 180 words that follows Google's guidance for Nano Banana Pro:
- Start with a strong verb. In the first three sentences, name the surface that carries the names, how the names are made in it, and both names in quotes, spelled exactly "{house}" and "{partner}": "{house}" in {house_wordmark}, and "{partner}" in {partner_wordmark}.
- Then describe the setting, the composition, and the style as a story, in positive terms.
- Direct the camera and the light: the lens, the aperture, the angle, and the quality of the light. Photograph a mirror or any glass from about 30 degrees to one side, so its frame shows and its reflection holds the room, never the camera.
- Name real materials and textures. Keep the frame to the surface with the names and at most two props from the brands' own prop lists.
- Nano Banana Pro will receive two reference images. Say that Image 1 is the {house} logo and Image 2 is the {partner} logo, and that they give only the shapes of the letters: in the scene, the letters take the color and texture of the material.
- This is a luxury campaign photograph: clean, immaculate, beautifully styled, photoreal, a still life with no people. Vertical, 9:16.

Return only the prompt."""
)

# The brand review: Gemini checks each image against both brands, the same craft rules, and the prompt it was made from.
REVIEW = (
    """You are the brand reviewer for a collaboration between {house} and {partner}. Image 1 is the shot to review.
It was made for this visual: {idea}
The image model was given this prompt: {visual_prompt}

"""
    + CRAFT
    + """

Read every word in the shot. The names must be spelled and cased exactly "{house}" and "{partner}", with letterforms that match the logos (for letters built from pieces, as closely as the pieces allow).
Blocking, the shot cannot ship: a misspelled or misshapen name; letters that look printed, painted, or inked on when the rules above say they are revealed in the material or built from it; letters floating in their own plane instead of lying on the surface that carries them; anything dirty, worn, or cluttered; a person or part of one; any other words.
Minor, note it but do not block: small artifacts in background objects, slightly soft edges, light that is a little off.
Approve only if nothing is blocking."""
)

REVIEW_SCHEMA = {
    'type': 'object',
    'properties': {
        'text_seen': {'type': 'string'},
        'blocking': {'type': 'array', 'items': {'type': 'string'}},
        'minor': {'type': 'array', 'items': {'type': 'string'}},
        'approved': {'type': 'boolean'},
    },
    'required': ['text_seen', 'blocking', 'minor', 'approved'],
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

    # 1. Gemini, as creative director, writes the visual prompt from the inputs.
    director_prompt = pxtf.string.format(
        DIRECTOR,
        house=house['name'],
        partner=guest['name'],
        house_look=house.look,
        partner_look=guest.look,
        house_wordmark=house.wordmark,
        partner_wordmark=guest.wordmark,
        theme=brief.theme,
        direction=brief.direction,
        idea=idea,
    )
    director_response = pxtf.gemini.generate_content([director_prompt, house.board, guest.board], model=DIRECTOR_MODEL)
    visual_prompt = director_response.candidates[0].content.parts[0].text.astype(pxt.String)

    # 2. Nano Banana Pro makes the image from Gemini's prompt, with both logos attached.
    image_response = pxtf.gemini.generate_content([house.logo, guest.logo, visual_prompt], model=IMAGE_MODEL, config=IMAGE_CONFIG)
    image = udfs.first_image(image_response)

    # 3. Gemini reviews the image against both brands.
    review_prompt = pxtf.string.format(REVIEW, house=house['name'], partner=guest['name'], idea=idea, visual_prompt=visual_prompt)
    review_response = pxtf.gemini.generate_content(
        [image, review_prompt],
        model=DIRECTOR_MODEL,
        config={'response_mime_type': 'application/json', 'response_json_schema': REVIEW_SCHEMA},
    )
    review = udfs.parse_json(review_response.candidates[0].content.parts[0].text.astype(pxt.String))
    approved = review['approved'].astype(pxt.Bool)
