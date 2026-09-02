"""Read-only MCP tools over the ``mcp_demo`` Pixeltable catalog."""

from datetime import datetime, timezone
import base64
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pixeltable as pxt
from mcp.types import BlobResourceContents, EmbeddedResource, TextContent

CATALOG = 'mcp_demo'


def _table(name: str) -> pxt.Table:
    return pxt.get_table(f'{CATALOG}.{name}')


def _records(query: Any) -> list[dict[str, Any]]:
    """Collect a Pixeltable query as JSON-safe dictionaries."""

    frame = query.collect().to_pandas()
    return json.loads(frame.to_json(orient='records'))


def _log(tool: str, *, text: str | None = None, image: str | None = None) -> None:
    queries = _table('queries')
    queries.insert(
        [
            {
                'query_id': str(uuid4()),
                'tool': tool,
                'text': text,
                'image': image,
                'created_at': datetime.now(timezone.utc),
            }
        ]
    )


def search_photo_text(query: str, limit: int = 5) -> str:
    """Search photo titles and generated captions for words in the query."""

    _log('search_photo_text', text=query)
    photos = _table('photos')
    needle = query.lower()
    matches = photos.search_title.contains(needle) | photos.caption.lower().contains(needle)
    return json.dumps(
        _records(
            photos.where(matches)
            .select(photo_id=photos.photo_id, title=photos.title, caption=photos.caption)
            .limit(limit)
        )
    )


def search_photo_content(query: str, limit: int = 5) -> str:
    """Search what photos show, even when their titles use different words."""

    _log('search_photo_content', text=query)
    photos = _table('photos')
    score = photos.image.similarity(string=query, idx='clip_idx')
    return json.dumps(
        _records(
            photos.order_by(score, asc=False)
            .select(photo_id=photos.photo_id, title=photos.title, caption=photos.caption, score=score)
            .limit(limit)
        )
    )


def _clip_result(query: Any) -> list[TextContent | EmbeddedResource]:
    rows = query.collect().to_pandas()
    if len(rows) == 0:
        return []
    row = rows.iloc[0]
    clip_path = Path(str(row['clip']))
    details: dict[str, Any] = {
        'video_id': int(row['video_id']),
        'title': str(row['title']),
        'time_seconds': float(row['time_seconds']),
        'caption': str(row['caption']),
        'score': float(row['score']),
    }
    return [
        TextContent(type='text', text=json.dumps(details)),
        EmbeddedResource(
            type='resource',
            resource=BlobResourceContents(
                uri=clip_path.as_uri(),
                mimeType='video/mp4',
                blob=base64.b64encode(clip_path.read_bytes()).decode('ascii'),
            ),
        ),
    ]


def get_clip_for_text(query: str) -> list[Any]:
    """Return an eight-second video clip whose frames match a text query."""

    _log('get_clip_for_text', text=query)
    frames = _table('video_frames')
    score = frames.frame.similarity(string=query, idx='frame_clip_idx')
    return _clip_result(
        frames.order_by(score, asc=False)
        .select(
            video_id=frames.video_id,
            title=frames.title,
            time_seconds=frames.frame_attrs.time,
            caption=frames.caption,
            clip=frames.clip,
            score=score,
        )
        .limit(1)
    )


def get_clip_for_image(image: str) -> list[Any]:
    """Return an eight-second video clip whose frames match an image URL or path."""

    _log('get_clip_for_image', image=image)
    frames = _table('video_frames')
    score = frames.frame.similarity(image=image, idx='frame_clip_idx')
    return _clip_result(
        frames.order_by(score, asc=False)
        .select(
            video_id=frames.video_id,
            title=frames.title,
            time_seconds=frames.frame_attrs.time,
            caption=frames.caption,
            clip=frames.clip,
            score=score,
        )
        .limit(1)
    )


def ask_about_video(question: str, limit: int = 3) -> str:
    """Answer from the nearest video-frame captions and video transcripts."""

    _log('ask_about_video', text=question)
    frames = _table('video_frames')
    videos = _table('videos')
    answers = _table('answers')

    caption_score = frames.caption.similarity(string=question, idx='caption_idx')
    caption_hits = _records(
        frames.order_by(caption_score, asc=False)
        .select(
            video_id=frames.video_id,
            title=frames.title,
            time_seconds=frames.frame_attrs.time,
            caption=frames.caption,
            score=caption_score,
        )
        .limit(limit)
    )

    transcript_score = videos.transcript.similarity(string=question, idx='transcript_idx')
    transcript_hits = _records(
        videos.order_by(transcript_score, asc=False)
        .select(
            video_id=videos.video_id,
            title=videos.title,
            transcript=videos.transcript,
            score=transcript_score,
        )
        .limit(limit)
    )

    source_notes = json.dumps({'captions': caption_hits, 'transcripts': transcript_hits}, indent=2)
    status = answers.insert(
        [
            {
                'answer_id': str(uuid4()),
                'question': question,
                'source_notes': source_notes,
                'created_at': datetime.now(timezone.utc),
            }
        ],
        return_rows=True,
    )
    row = status.rows[0]
    return json.dumps(
        {
            'answer_id': row['answer_id'],
            'answer': row['answer'],
            'sources': {'captions': caption_hits, 'transcripts': transcript_hits},
        }
    )
