"""Serve the RAG backend: POST /ask with {"raw": "..."} inserts a question and returns the photos and the answer.

Start it with:
    pxt service update serve.py rag_demo --port 8000
"""

import pixeltable as pxt
from pixeltable.serving import FastAPIRouter

queries = pxt.get_table('rag_demo.queries')

rag = FastAPIRouter(name='rag')
rag.add_insert_route(queries, path='/ask', inputs=[queries.raw], outputs=[queries.hits, queries.answer])
