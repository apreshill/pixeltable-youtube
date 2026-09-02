"""Recipe 3: search video frames and return short clips.

Apply it with:
    pxt schema diff recipe3_video.py mcp_demo
    pxt schema update recipe3_video.py mcp_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    """Photos with text search and image similarity search."""

    photo_id: pxt.Required[pxt.Int]
    image: pxt.Required[pxt.Image]
    title: pxt.String | None

    search_title = title.lower()
    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )

    __indexes__ = [
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32'),
            name='clip_idx',
        )
    ]


class Queries(TableModel, name='queries'):
    """Questions and images sent to the MCP search tools."""

    query_id: pxt.Required[pxt.String]
    tool: pxt.Required[pxt.String]
    text: pxt.String | None
    image: pxt.Image | None
    created_at: pxt.Required[pxt.Timestamp]


class Videos(TableModel, name='videos'):
    """Source videos available to the MCP."""

    video_id: pxt.Required[pxt.Int]
    video: pxt.Required[pxt.Video]
    title: pxt.Required[pxt.String]


class VideoFrames(
    TableModel,
    name='video_frames',
    base=Videos,
    iterator=pxtf.video.frame_iterator(Videos.video, fps=0.2),
):
    """Sampled frames, captions, and clips from each source video."""

    caption = pxtf.huggingface.image_captioning(
        frame,  # type: ignore[name-defined]  # noqa: F821
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )
    clip = pxtf.video.clip(
        Videos.video,
        mode='fast',
        duration=8.0,
        start_time=frame_attrs.time,  # type: ignore[name-defined]  # noqa: F821
    )

    __indexes__ = [
        pxt.EmbeddingIndex(
            frame,  # type: ignore[name-defined]  # noqa: F821
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch32'),
            name='frame_clip_idx',
        )
    ]
