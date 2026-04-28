"""
BIS Standards Retriever — TF-IDF + BM25-style hybrid retrieval
Works offline without any external ML dependencies.
"""

import json
import math
import re
import os
from collections import Counter
from typing import List, Tuple


# ── Stop words ──────────────────────────────────────────────────────────────
STOP_WORDS = {
    'a','an','the','is','are','was','were','be','been','being',
    'have','has','had','do','does','did','will','would','could','should',
    'may','might','shall','can','need','dare','ought','used','to','of',
    'in','for','on','with','at','by','from','up','about','into','through',
    'during','before','after','above','below','between','each','both',
    'and','or','but','if','while','although','because','since','unless',
    'which','that','this','these','those','it','its','we','our','you',
    'your','they','their','he','his','she','her','not','no','nor',
    'as','so','than','too','very','just','more','most','also','only',
    'any','all','both','few','other','such','same','own','where','when',
    'how','what','who','whom','why','use','used','using','product',
    'products','material','materials','standard','standards','indian',
    'specification','specifications','bureau','bis','requirement','requirements'
}


def tokenize(text: str) -> List[str]:
    text = text.lower()
    tokens = re.findall(r'\b[a-z][a-z0-9\-]*\b', text)
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]


class BISRetriever:
    def __init__(self, chunks_path: str):
        with open(chunks_path, 'r') as f:
            self.chunks = json.load(f)

        self.corpus_tokens = [tokenize(c['text']) for c in self.chunks]
        self.N = len(self.chunks)

        # Build IDF
        df = Counter()
        for tokens in self.corpus_tokens:
            for t in set(tokens):
                df[t] += 1
        self.idf = {t: math.log((self.N - df[t] + 0.5) / (df[t] + 0.5) + 1)
                    for t in df}

        # BM25 params
        self.k1 = 1.5
        self.b = 0.75
        avg_dl = sum(len(t) for t in self.corpus_tokens) / self.N
        self.avg_dl = avg_dl

    def bm25_score(self, query_tokens: List[str], doc_idx: int) -> float:
        doc_tokens = self.corpus_tokens[doc_idx]
        dl = len(doc_tokens)
        tf_map = Counter(doc_tokens)
        score = 0.0
        for qt in query_tokens:
            if qt not in self.idf:
                continue
            tf = tf_map.get(qt, 0)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl)
            score += self.idf[qt] * (numerator / denominator)
        return score

    def keyword_boost(self, query: str, chunk: dict) -> float:
        """Boost score when IS number or exact phrase appears in query."""
        boost = 0.0
        chunk_id = chunk['id'].lower().replace(' ', '')
        query_lower = query.lower().replace(' ', '')
        if chunk_id in query_lower:
            boost += 5.0
        return boost

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float, str]]:
        query_tokens = tokenize(query)
        scores = []
        for i, chunk in enumerate(self.chunks):
            score = self.bm25_score(query_tokens, i)
            score += self.keyword_boost(query, chunk)
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scores[:top_k]:
            chunk = self.chunks[idx]
            results.append((chunk['id'], score, chunk['text'][:800]))
        return results
