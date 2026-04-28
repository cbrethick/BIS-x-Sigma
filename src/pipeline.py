"""
BIS RAG Pipeline — end-to-end: query → retrieve → (optionally) LLM rationale → output
"""

import os
import time
from typing import List, Dict

from src.retriever import BISRetriever
from src.llm import generate_rationale

# Resolve path to chunks relative to this file or project root
_HERE = os.path.dirname(os.path.abspath(__file__))
_CHUNKS_PATH = os.path.join(_HERE, '..', 'data', 'bis_chunks.json')


class BISRAGPipeline:
    def __init__(self, chunks_path: str = None, use_llm: bool = True, top_k: int = 5):
        path = chunks_path or _CHUNKS_PATH
        self.retriever = BISRetriever(path)
        self.use_llm = use_llm
        self.top_k = top_k

    def query(self, question: str) -> dict:
        """
        Run the RAG pipeline for a single query.
        Returns: {
            "retrieved_standards": [...],   # list of IS IDs
            "rationale": [...],             # list of {standard_id, rationale}
            "latency_seconds": float
        }
        """
        t0 = time.time()
        retrieved = self.retriever.retrieve(question, top_k=self.top_k)
        std_ids = [r[0] for r in retrieved]

        rationale = []
        if self.use_llm:
            rationale = generate_rationale(question, retrieved, top_k=self.top_k)

        latency = round(time.time() - t0, 3)
        return {
            "retrieved_standards": std_ids,
            "rationale": rationale,
            "latency_seconds": latency
        }
