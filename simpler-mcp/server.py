"""FastMCP server for the current ``mcp_demo`` schema."""

import argparse
from typing import Any

import pixeltable as pxt
from mcp.server.fastmcp import FastMCP

from resources import describe_table, list_catalog
from tools import (
    ask_about_video,
    get_clip_for_image,
    get_clip_for_text,
    search_photo_content,
    search_photo_text,
)


def _table(name: str) -> pxt.Table | None:
    try:
        return pxt.get_table(f'mcp_demo.{name}')
    except Exception:
        return None


def _supports_similarity(column: Any, *, idx: str) -> bool:
    try:
        column.similarity(string='probe', idx=idx)
        return True
    except Exception:
        return False


def _add_tools(mcp: FastMCP) -> None:
    photos = _table('photos')
    frames = _table('video_frames')
    videos = _table('videos')
    answers = _table('answers')

    if photos is not None:
        mcp.add_tool(search_photo_text)
        if _supports_similarity(photos.image, idx='clip_idx'):
            mcp.add_tool(search_photo_content)

    if frames is not None and _supports_similarity(frames.frame, idx='frame_clip_idx'):
        mcp.add_tool(get_clip_for_text)
        mcp.add_tool(get_clip_for_image)

    if (
        frames is not None
        and videos is not None
        and answers is not None
        and 'transcript' in videos.columns()
        and _supports_similarity(frames.caption, idx='caption_idx')
        and _supports_similarity(videos.transcript, idx='transcript_idx')
    ):
        mcp.add_tool(ask_about_video)


def build_server(*, host: str = '127.0.0.1', port: int = 8000) -> FastMCP:
    """Build a server whose tools match the schema currently applied."""

    mcp = FastMCP('Multimodal Catalog', host=host, port=port)
    mcp.resource(
        'pixeltable://mcp_demo/catalog',
        name='list_catalog',
        description='List the tables and views available through this MCP.',
    )(list_catalog)
    mcp.resource(
        'pixeltable://mcp_demo/tables/{name}',
        name='describe_table',
        description='Describe one table or view in the catalog.',
    )(describe_table)
    _add_tools(mcp)
    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description='Serve the mcp_demo Pixeltable catalog.')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=8000, type=int)
    args = parser.parse_args()
    build_server(host=args.host, port=args.port).run(transport='streamable-http')


if __name__ == '__main__':
    main()
