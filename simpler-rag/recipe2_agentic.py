"""Recipe 2: Agentic query rewriting. Turn each question into keywords, search, and retry once if nothing matches.

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


@pxt.udf
def shares_a_word(title: str | None, keywords: str) -> bool:
    title_words = set(re.findall(r'[a-z]+', (title or '').lower()))
    return bool(title_words & set(re.findall(r'[a-z]+', keywords.lower())))


@pxt.query
def search_titles(keywords: str) -> pxt.Query:
    return Photos.where(shares_a_word(Photos.title, keywords)).select(Photos.photo_id, Photos.title)


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
