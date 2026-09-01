"""Recipe 5: rewrite messy questions into short search queries.

A model turns a vague request into a short description before we search. This is
one rewrite before one search. It does not inspect the results and try again.

This model calls OpenAI, so it needs OPENAI_API_KEY set where the daemon runs.

Apply it with:
    pxt schema update recipe5_rewrite.py rag_demo
"""

import pixeltable as pxt
import pixeltable.functions as pxtf

TableModel = pxt.model_base()


class Queries(TableModel, name='queries'):
    """Raw user questions and the search query the database rewrites them into."""

    raw: pxt.Required[pxt.String]

    # The database calls OpenAI on each question and keeps the response as a column.
    response = pxtf.openai.chat_completions(
        messages=[
            {
                'role': 'system',
                'content': 'Rewrite the user request as a short, literal image-search query. '
                'Reply with only the query, no punctuation.',
            },
            {'role': 'user', 'content': raw},
        ],
        model='gpt-4o-mini',
    )
    search_query = response.choices[0].message.content
