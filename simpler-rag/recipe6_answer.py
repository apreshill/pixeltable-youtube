"""Recipe 6: retrieve three photos for each question and answer from them.

Needs OPENAI_API_KEY where the pxt daemon runs.
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id: pxt.Int
    image: pxt.Image
    title: pxt.String | None

    caption = pxtf.huggingface.image_captioning(
        image,
        model_id='Salesforce/blip-image-captioning-base',
        model_kwargs={'max_length': 30},
    )

    __indexes__ = [
        pxt.EmbeddingIndex(
            image,
            embedding=pxtf.huggingface.clip.using(model_id='openai/clip-vit-base-patch16'),
            name='clip_idx_v2',
        ),
    ]


@pxt.query
def search_titles(word: str) -> pxt.Query:
    return Photos.where(Photos.title.contains(word, case=False)).select(Photos.photo_id, Photos.title)


@pxt.query
def search_photos(text: str) -> pxt.Query:
    sim = Photos.image.similarity(string=text, idx='clip_idx_v2')
    return (
        Photos.order_by(sim, asc=False)
        .limit(3)
        .select(Photos.photo_id, Photos.title, Photos.caption, url=Photos.image.fileurl)
    )


@pxt.udf
def source_notes(hits: pxt.Json) -> str:
    return '\n'.join(f'Photo {h["photo_id"]}: {h["title"]}. Caption: {h["caption"]}' for h in hits)


class Queries(TableModel, name='queries'):
    raw: pxt.String

    response = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Rewrite the question as one singular, lowercase noun that would appear in a photo title. '
                'Reply with only that word.',
            },
            {'role': 'user', 'content': raw},
        ],
        model='gpt-4o-mini',
    )
    search_query = response.choices[0].message.content
    title_hits = search_titles(search_query)

    # Retrieve, then answer. Both run on every question at insert.
    photo_hits = search_photos(search_query)
    answer_response = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Answer using only the photos and notes. If they are not enough, say so. '
                'Cite the photo IDs you used.',
            },
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': 'Question: ' + raw + '\n\nNotes:\n' + source_notes(photo_hits)},
                    {'type': 'image_url', 'image_url': {'url': photo_hits[0].url}},
                    {'type': 'image_url', 'image_url': {'url': photo_hits[1].url}},
                    {'type': 'image_url', 'image_url': {'url': photo_hits[2].url}},
                ],
            },
        ],
        model='gpt-4o-mini',
    )
    answer = answer_response.choices[0].message.content
