"""Bonus: split a question with two requests into two searches. Also declares the app's API route.

Needs an OpenAI key. See Prerequisites in the README.
"""

import pixeltable as pxt
import pixeltable.functions as pxtf
from pixeltable.serving import FastAPIRouter

from rag_udfs import answer_messages, merge_hits, shares_a_word

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id = pxt.Column(type=pxt.Int, primary_key=True)
    image: pxt.Image
    title: pxt.String | None
    hot: pxt.Bool | None  # the photos people look at most

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
def search_titles(text: str) -> pxt.Query:
    """Photos whose title shares a word with the text."""
    return Photos.where(shares_a_word(Photos.title, text)).select(
        Photos.photo_id, Photos.title, url=Photos.image.fileurl
    )


@pxt.query
def all_titles() -> pxt.Query:
    """Every photo title. The model picks search words from these."""
    return Photos.select(Photos.title)


@pxt.query
def full_search(question: str) -> pxt.Query:
    """Every photo, ranked by the newer model."""
    sim = Photos.image.similarity(string=question, idx='clip_idx_v2')
    return (
        Photos.order_by(sim, asc=False)
        .limit(2)
        .select(Photos.photo_id, Photos.title, Photos.caption, url=Photos.image.fileurl)
    )


class Queries(TableModel, name='queries'):
    """The app's backend: insert a question, read back what was retrieved and the answer."""

    raw: pxt.String

    # Retrieval, step 1: an LLM turns the question into keywords, and we search the titles.
    first_try = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Turn the question into 1 to 3 lowercase English search keywords. '
                'Reply with only the words, separated by spaces.',
            },
            {'role': 'user', 'content': raw},
        ],
        model='gpt-4o-mini',
    )
    first_keywords = first_try.choices[0].message.content.astype(pxt.String)
    first_hits = search_titles(first_keywords)

    # Retrieval, step 2: the LLM sees what it found and every photo title, and adds title words that fit.
    second_try = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'You search photo titles by keyword. If the keywords found photos, reply with the '
                'same keywords. If they found nothing, reply with the one or two words from the photo titles '
                'that best match what the question asks for. If no title fits, reply with nothing. '
                'Reply with only the words, separated by spaces.',
            },
            {
                'role': 'user',
                'content': 'Question: ' + raw + '\nKeywords: ' + first_keywords
                + '\nPhotos found: ' + pxtf.json.dumps(search_titles(first_keywords))
                + '\nPhoto titles: ' + pxtf.json.dumps(all_titles()),
            },
        ],
        model='gpt-4o-mini',
    )
    # Keep the first words, and add the words from the second try.
    keywords = first_keywords + ' ' + second_try.choices[0].message.content.astype(pxt.String)

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

    # Retrieval: search each part of the question, and combine the photos.
    hits = (merge_hits(full_search(parts[0]), full_search(parts[1]))).astype(pxt.Json)

    # Generation: answer from whatever `hits` retrieved. This part never changes.
    answer_response = pxtf.openai.chat_completions(messages=answer_messages(raw, hits), model='gpt-4o-mini')
    answer = answer_response.choices[0].message.content.astype(pxt.String)


# The API: POST /ask inserts a question and returns the photos and the answer.
api = FastAPIRouter(name='rag')
api.add_insert_route(Queries, path='/ask', inputs=[Queries.raw], outputs=[Queries.hits, Queries.answer])
