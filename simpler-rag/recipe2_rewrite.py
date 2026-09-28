"""Recipe 2: rewrite each question into a search word, then search the titles.

Needs OPENAI_API_KEY where the pxt daemon runs.
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Photos(TableModel, name='photos'):
    photo_id: pxt.Int
    image: pxt.Image
    title: pxt.String | None


@pxt.query
def search_titles(word: str) -> pxt.Query:
    return Photos.where(Photos.title.contains(word, case=False)).select(Photos.photo_id, Photos.title)


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

    # A query as a column: every new question is searched on insert.
    title_hits = search_titles(search_query)
