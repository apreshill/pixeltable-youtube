"""One front door, many paint colors.

- `doors`: the one photo of the front door.
- `paints`: one row per Benjamin Moore color. You insert only the color number. Pixeltable reads the
  official data from the color's page (name, hex, LRV, and more), downloads Benjamin Moore's photo
  of the color, draws a paint chip, and has Gemini repaint just the door in that color.

    pxt schema diff schema.py door_demo
    pxt schema update schema.py door_demo -f
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

import udfs

TableModel = pxt.model_base()

IMAGE_MODEL = 'gemini-3-pro-image'
IMAGE_CONFIG = {'response_modalities': ['IMAGE'], 'image_config': {'aspect_ratio': '3:4', 'image_size': '2K'}}

REPAINT = """Image 1 is a photo of a front door. Image 2 is the paint chip for Benjamin Moore {name} ({number}), hex {hex}.

Edit Image 1: repaint only the front door itself, its panels, moldings, and edges, in exactly the color of the chip, in a satin exterior finish. Keep the photo's light and shadows on the door, so the new color looks the way this paint would look in this light.

Keep everything else exactly as it is: the door's glass and what shows through it, the hardware, the white sidelights, transom, and trim around the door, the brick, the porch, the columns, the steps, and the plants. Keep the same framing. Return only the edited photo."""


class Doors(TableModel, name='doors'):
    door = pxt.Column(type=pxt.String, primary_key=True)
    photo: pxt.Image
    credit: pxt.String


@pxt.query
def front_door():
    """The front door photo."""
    return Doors.select(photo=Doors.photo).limit(1)


class Paints(TableModel, name='paints'):
    number = pxt.Column(type=pxt.String, primary_key=True)  # for example 'HC-154'

    # 1. The official color data, from the color's Benjamin Moore page.
    info = udfs.bm_color(number)
    name = info['name'].astype(pxt.String)
    hex = info['hex'].astype(pxt.String)
    lrv = info['lrv'].astype(pxt.Float)  # light reflectance value: 0 is black, 100 is white
    collection = info['collection'].astype(pxt.String)
    best_selling = info['best_selling'].astype(pxt.Bool)

    # 2. Benjamin Moore's photo of the color, and a paint chip drawn from the official hex.
    bm_photo = udfs.fetch_image(info['photo_url'].astype(pxt.String))
    chip = udfs.paint_chip(name, number, hex, lrv)

    # 3. Gemini repaints just the door in this color.
    door = front_door()
    repaint_prompt = pxtf.string.format(REPAINT, name=name, number=number, hex=hex)
    response = pxtf.gemini.generate_content([door.photo, chip, repaint_prompt], model=IMAGE_MODEL, config=IMAGE_CONFIG)
    painted_door = udfs.first_image(response)
