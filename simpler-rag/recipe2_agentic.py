"""Recipe 2: Agentic query rewriting. Keywords, a search, and one retry.

Needs an OpenAI key. See Prerequisites in the README.
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

from rag_udfs import answer_messages, shares_a_word

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id = pxt.Column(type=pxt.Int, primary_key=True)
    image: pxt.Image
    title: pxt.String | None


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

    # Retrieval: titles that match the final keywords.
    hits = (search_titles(keywords)).astype(pxt.Json)

    # Generation: answer from whatever `hits` retrieved. This part never changes.
    answer_response = pxtf.openai.chat_completions(messages=answer_messages(raw, hits), model='gpt-4o-mini')
    answer = answer_response.choices[0].message.content.astype(pxt.String)
