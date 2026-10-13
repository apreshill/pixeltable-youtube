"""Recipe 1: The MVP. Full-text search on titles, and an answer from what it finds.

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


class Queries(TableModel, name='queries'):
    """The app's backend: insert a question, read back what was retrieved and the answer."""

    raw: pxt.String

    # Retrieval: title words that match the question.
    hits = (search_titles(raw)).astype(pxt.Json)

    # Generation: answer from whatever `hits` retrieved. This part never changes.
    answer_response = pxtf.openai.chat_completions(messages=answer_messages(raw, hits), model='gpt-4o-mini')
    answer = answer_response.choices[0].message.content.astype(pxt.String)
