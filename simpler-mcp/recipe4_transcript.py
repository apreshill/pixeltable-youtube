"""Recipe 4: search video captions and transcripts, then answer a question.

Apply it with:
    pxt schema diff recipe4_transcript.py mcp_demo
    pxt schema update recipe4_transcript.py mcp_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()

TEXT_EMBEDDING = pxtf.huggingface.sentence_transformer.using(
    model_id='sentence-transformers/all-MiniLM-L6-v2'
)


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
    """Videos with searchable speech."""

    video_id: pxt.Required[pxt.Int]
    video: pxt.Required[pxt.Video]
    title: pxt.Required[pxt.String]

    audio = pxtf.video.extract_audio(video, format='mp3')
    transcript = pxtf.huggingface.automatic_speech_recognition(
        audio,
        model_id='openai/whisper-tiny.en',
        chunk_length_s=30,
    )

    __indexes__ = [
        pxt.EmbeddingIndex(transcript, embedding=TEXT_EMBEDDING, name='transcript_idx'),
    ]


class VideoFrames(
    TableModel,
    name='video_frames',
    base=Videos,
    iterator=pxtf.video.frame_iterator(Videos.video, fps=0.2),
):
    """Sampled video frames with searchable captions and short clips."""

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
        ),
        pxt.EmbeddingIndex(caption, embedding=TEXT_EMBEDDING, name='caption_idx'),
    ]


class Answers(TableModel, name='answers'):
    """Questions, retrieved evidence, and grounded answers."""

    answer_id: pxt.Required[pxt.String]
    question: pxt.Required[pxt.String]
    source_notes: pxt.Required[pxt.String]
    created_at: pxt.Required[pxt.Timestamp]

    response = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Answer only from the supplied video captions and transcript excerpts. '
                'If the evidence is insufficient, say so.',
            },
            {
                'role': 'user',
                'content': 'Question: ' + question + '\n\nEvidence:\n' + source_notes,
            },
        ],
        model='gpt-4o-mini',
    )
    answer = response.choices[0].message.content
