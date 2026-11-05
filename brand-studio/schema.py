"""A brand studio: brand kits in, brand moments out.

The brand kit lives in tables, not folders:

- `brands`: one row per brand. Palette, type spec, the font files themselves,
  logos, and the style guide. Gemini reads the style guide once into art
  direction, and Pillow draws a brand board from the kit.
- `library`: the brand's own photography, searchable by meaning.
- `products`: one row per SKU, with a studio packshot made from its
  description and the brand's logo, so every shot shows the same product.

The creative library, also rows:

- `directions`: one row per look. The prompt templates for the set designer,
  the set photo, each shot, and the reviewer, plus the house rules.
- `moments`: one row per idea for putting the brand names into the world:
  printed into a doormat, woven into a towel label, appearing in the steam on
  a mirror, set into a tile floor. A new idea is a new row.

The work:

- `campaigns`: one row per brief: a brand, or two, a direction, and the
  moments to shoot. Swap any of them and insert again. Gemini designs one set
  from the brand kits and the moments, and Nano Banana Pro photographs it empty.
- `shots`: one row per campaign and moment. Nano Banana Pro photographs the
  moment in that set with its surface still blank. Then the words go in two
  ways, side by side: Nano Banana Pro edits them into that photo, and code
  sets the exact logo files into the same photo. Gemini reviews both, the
  version that passes ships, Gemini Omni animates it, and Gemini watches the
  clip for glitches.
- `reels`: one row per cut. The approved clips, in the order you list them.

Every model call goes through four helpers below, and MODELS picks the models.
'local' runs everything on this machine for free: Stable Diffusion for images,
and Ollama for text and reviews. 'gemini' calls the Gemini API, which costs money.

Apply with:

    pxt schema update schema.py studio_local -f   # MODELS = 'local'
    pxt schema update schema.py studio -f         # MODELS = 'gemini'
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

import udfs

TableModel = pxt.model_base()

MODELS = 'local'  # 'local' is free, on this machine. 'gemini' calls the Gemini API and costs money.
LOCAL = MODELS == 'local'

LOCAL_TEXT_MODEL = 'llama3.2'  # Ollama
LOCAL_VISION_MODEL = 'llava:7b'  # Ollama

TEXT_MODEL = 'gemini-3.8-flash'
REVIEW_MODEL = 'gemini-3.1-pro-preview'  # reads small letters more reliably
IMAGE_MODEL = 'gemini-3-pro-image'
VIDEO_MODEL = 'gemini-omni-1.1-flash'
EMBED_MODEL = 'gemini-embedding-2'


def _json_config(schema: dict) -> dict:
    return {'response_mime_type': 'application/json', 'response_json_schema': schema}


def ask_json(prompt, schema: dict):
    """A model's answer as JSON that follows the schema."""
    if LOCAL:
        return udfs.local_json(prompt, schema, model=LOCAL_TEXT_MODEL)
    response = pxtf.gemini.generate_content(prompt, model=TEXT_MODEL, config=_json_config(schema))
    return udfs.parse_json(response.candidates[0].content.parts[0].text.astype(pxt.String))


def make_image(parts, short, aspect_ratio, start=None, strength: float = 0.6):
    """An image. Gemini gets the full input with its reference pictures. A local model gets the short prompt,
    and, for an edit, the picture to start from."""
    if LOCAL:
        return udfs.local_image(short, aspect_ratio, start, strength)
    return udfs.first_image(pxtf.gemini.generate_content(parts, model=IMAGE_MODEL, config=udfs.image_config(aspect_ratio)))


def review_image(image, prompt):
    """The brand reviewer's verdict on an image, as JSON. Empty when there is no image."""
    if LOCAL:
        return udfs.local_review(image, prompt, udfs.REVIEW_SCHEMA, model=LOCAL_VISION_MODEL)
    response = pxtf.gemini.generate_content(
        udfs.review_input(image, prompt), model=REVIEW_MODEL, config=_json_config(udfs.REVIEW_SCHEMA)
    )
    return udfs.parse_optional_json(response.candidates[0].content.parts[0].text.astype(pxt.String | None))


def embedding():
    """The embedding behind library search."""
    if LOCAL:
        return pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32')
    return pxtf.gemini.embed_content.using(model=EMBED_MODEL)


# ---------------------------------------------------------------------------
# The brand kit
# ---------------------------------------------------------------------------


class Brands(TableModel, name='brands'):
    brand = pxt.Column(type=pxt.String, primary_key=True)
    name: pxt.String  # spelled and cased exactly as it must appear
    category: pxt.String
    palette: pxt.Json  # a list of {role, name, hex}
    type_spec: pxt.Json  # family names, weights, and letter spacing per role
    headline_font: pxt.Binary  # the font files themselves
    accent_font: pxt.Binary
    body_font: pxt.Binary
    logo_dark: pxt.Image
    logo_light: pxt.Image
    style_guide: pxt.String  # the brand book, in Markdown

    art_direction = ask_json(udfs.art_direction_prompt(style_guide), udfs.ART_DIRECTION_SCHEMA)
    brand_board = udfs.brand_board(name, category, palette, type_spec, headline_font, accent_font, body_font, logo_dark)


class Library(TableModel, name='library'):
    brand: pxt.String
    note: pxt.String
    image: pxt.Image

    __indexes__ = [pxt.EmbeddingIndex(image, embedding=embedding(), name='library_idx')]


@pxt.query
def brand_style(brand: str):
    """The words a model needs about a brand: name, palette, and art direction."""
    return Brands.where(Brands.brand == brand).select(
        name=Brands.name, category=Brands.category, palette=Brands.palette, art_direction=Brands.art_direction
    ).limit(1)


@pxt.query
def brand_visuals(brand: str):
    """The pictures a model needs about a brand: its board and its logo."""
    return Brands.where(Brands.brand == brand).select(name=Brands.name, board=Brands.brand_board, logo=Brands.logo_dark).limit(1)


@pxt.query
def wordmark_style(brand: str):
    """What a brand's wordmark is made of, such as 'geometric caps' or 'script'."""
    return Brands.where(Brands.brand == brand).select(Brands.type_spec.wordmark.style.astype(pxt.String)).limit(1)


@pxt.query
def brand_references(brand: str, brief: str, n: int):
    """The n library photos closest in meaning to the brief."""
    sim = Library.image.similarity(string=brief)
    return Library.where(Library.brand == brand).order_by(sim, asc=False).select(image=Library.image, note=Library.note).limit(n)


class Products(TableModel, name='products'):
    sku = pxt.Column(type=pxt.String, primary_key=True)
    brand: pxt.String
    name: pxt.String
    packaging: pxt.String  # what the product looks like
    photo: pxt.Image | None  # optional: a phone photo of the real product

    style = brand_style(brand)
    packshot = make_image(
        udfs.packshot_input(name, packaging, brand_visuals(brand), style, photo), udfs.short_packshot(packaging, style), '1:1'
    )


@pxt.query
def product_shots(skus: pxt.Json):
    """Name, description, and packshot of each product a campaign features."""
    return Products.where(Products.sku.isin(skus)).select(
        sku=Products.sku, name=Products.name, packaging=Products.packaging, packshot=Products.packshot
    )


# ---------------------------------------------------------------------------
# The creative library: directions and moments are rows, so a marketing team
# changes the look, or adds an idea, without touching code.
# ---------------------------------------------------------------------------


class Directions(TableModel, name='directions'):
    direction = pxt.Column(type=pxt.String, primary_key=True)
    description: pxt.String
    # Prompt templates. {slots} come from the brand kits, the set, and the moment.
    set_prompt: pxt.String  # to the set designer, who returns one set as JSON
    plate_prompt: pxt.String  # the empty set, photographed
    base_prompt: pxt.String  # one moment in that set, its surface still blank
    letter_prompt: pxt.String  # the image model's edit: add the words to that photo
    review_prompt: pxt.String  # the brand reviewer's checklist for a still
    clip_review_prompt: pxt.String  # and for a clip
    house_rules: pxt.Json[list[str]]
    pairing: pxt.String  # {pairing} for two brands: how they share one set
    solo: pxt.String  # {pairing} for one brand
    lockup: pxt.String  # how two wordmarks sit together


class Moments(TableModel, name='moments'):
    moment = pxt.Column(type=pxt.String, primary_key=True)
    subject: pxt.String  # the object that carries the names
    blank: pxt.String  # the surface before any lettering
    treatment: pxt.String  # how the names are made in it; {wordmarks} is the brand wordmarks
    fits: pxt.Json[list[str]]  # the wordmark styles this material can really make
    physics: pxt.String  # how a craftsperson would really make it; the reviewer checks it
    framing: pxt.String
    aspect_ratio: pxt.String
    show_products: pxt.Bool
    motion: pxt.Json  # {prompt, seconds, reverse}
    composite: pxt.String | None  # the code that can lay the words instead, such as 'inlay'; None if only a model can


@pxt.query
def playbook(direction: str):
    """Every template and rule in one direction."""
    return Directions.where(Directions.direction == direction).select(
        set_prompt=Directions.set_prompt,
        plate_prompt=Directions.plate_prompt,
        base_prompt=Directions.base_prompt,
        letter_prompt=Directions.letter_prompt,
        review_prompt=Directions.review_prompt,
        clip_review_prompt=Directions.clip_review_prompt,
        house_rules=Directions.house_rules,
        pairing=Directions.pairing,
        solo=Directions.solo,
        lockup=Directions.lockup,
    ).limit(1)


_MOMENT_FIELDS = dict(
    moment=Moments.moment,
    subject=Moments.subject,
    blank=Moments.blank,
    treatment=Moments.treatment,
    fits=Moments.fits,
    physics=Moments.physics,
    framing=Moments.framing,
    aspect_ratio=Moments.aspect_ratio,
    show_products=Moments.show_products,
    motion=Moments.motion,
    composite=Moments.composite,
)


@pxt.query
def moment_spec(moment: str):
    """Everything about one moment."""
    return Moments.where(Moments.moment == moment).select(**_MOMENT_FIELDS).limit(1)


@pxt.query
def moment_specs(moments: pxt.Json):
    """The moments a campaign uses, so the set designer can build a set that fits all of them."""
    return Moments.where(Moments.moment.isin(moments)).select(**_MOMENT_FIELDS)


# ---------------------------------------------------------------------------
# The work: any brand, or any two, through any direction and any moments
# ---------------------------------------------------------------------------


class Campaigns(TableModel, name='campaigns'):
    campaign = pxt.Column(type=pxt.String, primary_key=True)
    brand: pxt.String
    partner: pxt.String | None  # a second brand, for a collaboration
    direction: pxt.String
    skus: pxt.Json[list[str]]
    brief: pxt.String
    moments: pxt.Json[list[str]]
    clips: pxt.Bool  # False: stills only, no video calls

    style = brand_style(brand)
    partner_style = brand_style(partner)
    products = product_shots(skus)
    rules = playbook(direction)
    wordmark_styles = udfs.styles(brand, wordmark_style(brand), partner, wordmark_style(partner))
    context = udfs.campaign_context(rules, style, partner_style, brief, moment_specs(moments))

    # One set for the whole campaign, designed from the brand kits and photographed empty.
    world_prompt = udfs.fill(rules.set_prompt, context)
    world = ask_json(world_prompt, udfs.WORLD_SCHEMA)
    set_context = udfs.with_world(context, world)
    plate_prompt = udfs.fill(rules.plate_prompt, set_context)
    plate = make_image(
        udfs.plate_input(plate_prompt, brand_references(brand, brief, 2)), udfs.short_prompt('plate', set_context), '9:16'
    )


class Shots(TableModel, name='shots', base=Campaigns, iterator=pxtf.json.list_iterator(moment=Campaigns.moments)):
    spec = moment_spec(moment)
    # Fails here, before any image call, if the moment's material cannot carry a brand's wordmark.
    shot_context = udfs.shot_context(Campaigns.set_context, Campaigns.products, spec, Campaigns.wordmark_styles)

    # 1. The moment with its surface still blank: a plain doormat, a fogged mirror, an empty floor.
    base_prompt = udfs.fill(Campaigns.rules.base_prompt, shot_context)
    base = make_image(
        udfs.shot_input(base_prompt, Campaigns.plate, Campaigns.products, spec),
        udfs.short_prompt('base', shot_context),
        spec.aspect_ratio,
        start=Campaigns.plate,  # a local model starts from the empty room
        strength=0.75,
    )

    # 2a. AI letters: the image model edits the words into that photo.
    letter_prompt = udfs.fill(Campaigns.rules.letter_prompt, shot_context)
    still = make_image(
        udfs.letter_input(letter_prompt, base, brand_visuals(Campaigns.brand), brand_visuals(Campaigns.partner)),
        udfs.short_prompt('letters', shot_context),
        spec.aspect_ratio,
        start=base,
        strength=0.45,
    )

    # 2b. Code letters: the exact logo files set into the same photo. Empty for moments with no compositor.
    composite = udfs.lay_letters(
        base, spec, brand_visuals(Campaigns.brand), brand_visuals(Campaigns.partner), Campaigns.style, Campaigns.partner_style
    )

    # The brand gate, the same for both versions: Gemini reads every word.
    review_prompt = udfs.fill(Campaigns.rules.review_prompt, shot_context)
    review = review_image(still, review_prompt)
    approved = udfs.verdict(review)  # a plain column, so you can filter and rerun on it
    composite_review = review_image(composite, review_prompt)
    composite_approved = udfs.verdict(composite_review)

    # The version that ships, and its clip.
    version = udfs.pick_version(approved, composite_approved)
    final = udfs.pick(version, still, composite)
    clip = udfs.animate(final, spec, False if LOCAL else Campaigns.clips, model=VIDEO_MODEL)  # no local video model

    # The same gate for motion: Gemini watches the clip for glitches and for words that drift.
    clip_review_prompt = udfs.fill(Campaigns.rules.clip_review_prompt, shot_context)
    if LOCAL:
        clip_review = udfs.no_review(clip)
    else:
        clip_review = udfs.parse_optional_json(
            pxtf.gemini.generate_content(
                udfs.clip_review_input(clip, clip_review_prompt), model=REVIEW_MODEL, config=_json_config(udfs.CLIP_REVIEW_SCHEMA)
            )
            .candidates[0]
            .content.parts[0]
            .text.astype(pxt.String | None)
        )
    clip_approved = udfs.verdict(clip_review)


@pxt.query
def campaign_clips(campaign: str):
    """Every clip a campaign has so far, by moment, with its review."""
    return Shots.where(Shots.campaign == campaign).select(moment=Shots.moment, clip=Shots.clip, review=Shots.clip_review)


class Reels(TableModel, name='reels'):
    reel = pxt.Column(type=pxt.String, primary_key=True)
    campaign: pxt.String
    sequence: pxt.Json[list[str]]  # the moments, in cut order

    clips = campaign_clips(campaign)
    video = udfs.stitch(clips, sequence)
