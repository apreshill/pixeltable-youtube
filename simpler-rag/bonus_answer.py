"""Bonus: split a question with more than one request, search each part, and answer from the photos.

Needs OPENAI_API_KEY where the pxt daemon runs.
"""

import re

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id = pxt.Column(type=pxt.Int, primary_key=True)
    image: pxt.Image
    title: pxt.String | None
    hot: pxt.Bool | None

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


@pxt.udf
def shares_a_word(title: str | None, keywords: str) -> bool:
    title_words = set(re.findall(r'[a-z]+', (title or '').lower()))
    return bool(title_words & set(re.findall(r'[a-z]+', keywords.lower())))


@pxt.query
def search_titles(keywords: str) -> pxt.Query:
    return Photos.where(shares_a_word(Photos.title, keywords)).select(Photos.photo_id, Photos.title)


@pxt.query
def search_photos(text: str) -> pxt.Query:
    sim = Photos.image.similarity(string=text, idx='clip_idx_v2')
    return (
        Photos.order_by(sim, asc=False)
        .limit(2)
        .select(Photos.photo_id, Photos.title, Photos.caption, url=Photos.image.fileurl)
    )


@pxt.udf
def source_notes(hits: pxt.Json) -> str:
    return '\n'.join(f'Photo {h["photo_id"]}: {h["title"]}. Caption: {h["caption"]}' for h in hits)


class Queries(TableModel, name='queries'):
    raw: pxt.String

    # First try: turn the question into keywords and search.
    first_try = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Turn the question into 1 to 3 lowercase search keywords. '
                'Reply with only the words, separated by spaces.',
            },
            {'role': 'user', 'content': raw},
        ],
        model='gpt-4o-mini',
    )
    first_keywords = first_try.choices[0].message.content.astype(pxt.String)
    first_hits = search_titles(first_keywords)

    # Second try: the model sees what its keywords found, and broadens them if nothing matched.
    second_try = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'You search photo titles by keyword. If the keywords found photos, reply with the '
                'same keywords. If they found nothing, reply with 3 to 5 different single-word keywords, '
                'including synonyms and more general words. Reply with only the words, separated by spaces.',
            },
            {
                'role': 'user',
                'content': 'Question: ' + raw + '\nKeywords: ' + first_keywords
                + '\nPhotos found: ' + pxtf.json.dumps(first_hits),
            },
        ],
        model='gpt-4o-mini',
    )
    keywords = second_try.choices[0].message.content.astype(pxt.String)
    title_hits = search_titles(keywords)

    # Multi-intent: split the question into two search requests, one per line.
    split = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Split the question into exactly 2 short image-search requests, one per line. '
                'If it asks for only one thing, write it twice. Reply with only the 2 lines.',
            },
            {'role': 'user', 'content': raw},
        ],
        model='gpt-4o-mini',
    )
    parts = split.choices[0].message.content.astype(pxt.String).splitlines()
    photos_1 = search_photos(parts[0])
    photos_2 = search_photos(parts[1])

    # Answer from the retrieved photos, citing photo IDs.
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
                    {
                        'type': 'text',
                        'text': 'Question: ' + raw + '\n\nNotes:\n' + source_notes(photos_1) + '\n'
                        + source_notes(photos_2),
                    },
                    {'type': 'image_url', 'image_url': {'url': photos_1[0].url}},
                    {'type': 'image_url', 'image_url': {'url': photos_1[1].url}},
                    {'type': 'image_url', 'image_url': {'url': photos_2[0].url}},
                    {'type': 'image_url', 'image_url': {'url': photos_2[1].url}},
                ],
            },
        ],
        model='gpt-4o-mini',
    )
    answer = answer_response.choices[0].message.content
