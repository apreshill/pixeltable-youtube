"""Plain Python helpers the recipe files share."""

import io
import re
import urllib.request

import PIL.Image
import pixeltable as pxt


# Words too common to count as a match, like a full-text search engine would skip.
STOPWORDS = {
    'a', 'an', 'the', 'of', 'on', 'in', 'at', 'to', 'for', 'and', 'or', 'with', 'is', 'are', 'any', 'anything',
    'do', 'does', 'you', 'have', 'me', 'show', 'some', 'what', 'which', 'photo', 'photos', 'picture', 'pictures',
}


def _words(text: str | None) -> set[str]:
    """The words in the text, without stopwords, with a plural "s" removed so "dogs" matches "dog"."""
    words = set(re.findall(r'[a-z]+', (text or '').lower())) - STOPWORDS
    return {w[:-1] if len(w) > 3 and w.endswith('s') and not w.endswith('ss') else w for w in words}


@pxt.udf
def shares_a_word(text: str | None, keywords: str) -> bool:
    """True if the text and the keywords have a word in common."""
    return bool(_words(text) & _words(keywords))


def _load_image(hit: dict) -> PIL.Image.Image:
    """The photo at the hit's URL, from image.fileurl (an https or file URL)."""
    with urllib.request.urlopen(hit['url']) as f:
        return PIL.Image.open(io.BytesIO(f.read()))


@pxt.udf
def answer_messages(question: str, hits: pxt.Json) -> pxt.Json:
    """The chat messages for answering a question from the retrieved photos."""
    notes = '\n'.join(
        f'Photo {h["photo_id"]}: {h.get("title") or "untitled"}. {h.get("caption") or ""}' for h in hits
    )
    content = [{'type': 'text', 'text': f'Question: {question}\n\nPhotos:\n{notes or "No photos found."}'}]
    # Send the images themselves. pxtf.openai.chat_completions in 0.7.14 rejects image URLs.
    content += [{'type': 'image_url', 'image_url': _load_image(h)} for h in hits[:4]]
    return [
        {
            'role': 'system',
            'content': 'Answer using only these photos. If they do not answer the question, say so. '
            'Cite the photo IDs you used, e.g., (photo 6). Answer in plain text, with no links or images.',
        },
        {'role': 'user', 'content': content},
    ]


@pxt.udf
def merge_hits(first: pxt.Json, second: pxt.Json) -> pxt.Json:
    """Both lists of photos, without repeats."""
    seen, merged = set(), []
    for h in first + second:
        if h['photo_id'] not in seen:
            seen.add(h['photo_id'])
            merged.append(h)
    return merged
