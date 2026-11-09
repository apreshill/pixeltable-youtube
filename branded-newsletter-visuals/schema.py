"""One issue row becomes a branded cover and a short video.

You insert an issue number, a short scene, and, if you like, an inspiration
picture. The columns below fill in on that insert: the two prompts, the
picture, the brand plate, the cover, and a video made from the cover.

Apply with:

    pxt schema update schema.py visuals -f
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

import udfs

TableModel = pxt.model_base()

IMAGE_MODEL = 'gemini-3.1-flash-image-preview'
VIDEO_MODEL = 'gemini-omni-1.1-flash'
# Omni takes a whole number of seconds from 3 to 10. Rami's covers run about 5.
VIDEO_SECONDS = 5

# Fills {image_note} only when the row has an inspiration image. Without one, {image_note} is empty.
INSPIRATION_NOTE = 'Use the attached image as inspiration. '
# The scene you type goes into both prompts.
ART_TEMPLATE = (
    '{image_note}{scene} The picture fills the whole wide image edge to edge, with no frame, border, margins, '
    'or empty bands. No text, no letters, no numbers, no watermark.'
)
MOTION_TEMPLATE = (
    '<FIRST_FRAME> Animate this picture as one 5-second shot, starting on this exact picture. The picture shows: {scene} '
    'The camera pushes in slowly for the whole shot, with no panning. '
    'What is already in the picture comes alive and keeps moving clearly the whole time, in whatever ways fit it: '
    'grass and leaves sway in a breeze, light and shadows shift slowly, '
    'water flows, stars and moons pulse brighter and dimmer. '
    'Every moving element is subtle and realistic but still noticeable, '
    'and each one moves at its own random pace and timing, never in step with the others. '
    'Keep its style and colors. '
    'Add nothing that is not already in the picture. '
    'Keep the pink {issue_label} and the newsletter name exactly where they are, sharp and unchanged.'
)


class Issues(TableModel, name='issues'):
    issue_number = pxt.Column(type=pxt.Int, primary_key=True)
    scene: pxt.String
    # Optional: a picture for Nano Banana to start from. Leave it out for text only.
    inspiration: pxt.Image | None

    issue_label = pxtf.string.format('ISSUE {issue_number}', issue_number=issue_number)
    image_note = udfs.note_if_image(inspiration, INSPIRATION_NOTE)
    art_prompt = pxtf.string.format(ART_TEMPLATE, image_note=image_note, scene=scene)
    motion_prompt = pxtf.string.format(MOTION_TEMPLATE, scene=scene, issue_label=issue_label)

    # Nano Banana gets the inspiration image, if there is one, and then the prompt.
    art_response = pxtf.gemini.generate_content(
        udfs.art_input(art_prompt, inspiration),
        model=IMAGE_MODEL,
        config={'response_modalities': ['IMAGE'], 'image_config': {'aspect_ratio': '16:9'}},
    )
    art = art_response.candidates[0].content.parts[0].inline_data.data.astype(pxt.Image)

    plate = udfs.make_plate(art, issue_label)
    cover = udfs.composite_cover(art, plate)

    video = pxtf.gemini.generate_video(
        motion_prompt,
        images=[cover],
        model=VIDEO_MODEL,
        config={'aspect_ratio': '16:9', 'duration': f'{VIDEO_SECONDS}s'},
    )
