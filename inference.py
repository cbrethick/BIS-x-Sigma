"""
inference.py — Mandatory entry-point for BIS Hackathon judges.

Usage:
    python inference.py --input hidden_private_dataset.json --output team_results.json

Optional: set GEMINI_API_KEY env var to enable LLM rationale.
"""

import argparse, json, os, sys, time, math, re
from collections import Counter

STOP_WORDS = {
    'a','an','the','is','are','was','were','be','been','being','have','has',
    'had','do','does','did','will','would','could','should','may','might',
    'shall','can','need','dare','ought','used','to','of','in','for','on',
    'with','at','by','from','up','about','into','through','during','before',
    'after','above','below','between','each','both','and','or','but','if',
    'while','although','because','since','unless','which','that','this',
    'these','those','it','its','we','our','you','your','they','their','he',
    'his','she','her','not','no','nor','as','so','than','too','very','just',
    'more','most','also','only','any','all','few','other','such','same',
    'own','where','when','how','what','who','whom','why','use','using',
    'product','products','material','materials','standard','standards',
    'indian','specification','specifications','bureau','bis',
    'requirement','requirements','manufacture','manufacturing'
}

def tokenize(text):
    tokens = re.findall(r'\b[a-z][a-z0-9\-]*\b', text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 2]

class BM25:
    def __init__(self, chunks):
        self.chunks = chunks
        self.corpus = [tokenize(c['text']) for c in chunks]
        N = len(chunks)
        df = Counter()
        for toks in self.corpus:
            for t in set(toks): df[t] += 1
        self.idf = {t: math.log((N-df[t]+0.5)/(df[t]+0.5)+1) for t in df}
        self.k1, self.b = 1.5, 0.75
        self.avg_dl = sum(len(t) for t in self.corpus) / N

    def retrieve(self, query, top_k=5):
        qtoks = tokenize(query)
        scores = []
        for i, (chunk, doc) in enumerate(zip(self.chunks, self.corpus)):
            dl = len(doc); tf = Counter(doc); s = 0.0
            for qt in qtoks:
                if qt not in self.idf: continue
                f = tf.get(qt, 0)
                s += self.idf[qt] * f*(self.k1+1) / (f + self.k1*(1-self.b+self.b*dl/self.avg_dl))
            # boost if IS id mentioned in query
            if chunk['id'].lower().replace(' ','') in query.lower().replace(' ',''): s += 5
            scores.append((i, s))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(self.chunks[i]['id'], sc) for i,sc in scores[:top_k]]

def call_gemini(query, std_ids, chunks_map):
    import requests
    key = os.environ.get("GEMINI_API_KEY","")
    if not key: return []
    snippets = "\n\n".join(f"[{sid}]\n{chunks_map.get(sid,'')[:400]}" for sid in std_ids)
    prompt = (f'You are a BIS compliance expert.\nQuery: "{query}"\n\n'
              f'Top BIS standards retrieved:\n{snippets}\n\n'
              'Write a 1-2 sentence rationale for each standard above.\n'
              'Reply ONLY as JSON array: [{"standard_id":"...","rationale":"..."}]')
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    try:
        r = requests.post(url,
            json={"contents":[{"parts":[{"text":prompt}]}],
                  "generationConfig":{"temperature":0.1,"maxOutputTokens":1024}},
            timeout=20)
        r.raise_for_status()
        txt = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        txt = txt.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(txt)
    except Exception as e:
        print(f"[LLM] {e}"); return []

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--no-llm", action="store_true")
    args = p.parse_args()

    with open(args.input) as f: queries = json.load(f)

    base = os.path.dirname(os.path.abspath(__file__))
    chunks_path = os.path.join(base, "data", "bis_chunks.json")
    if not os.path.exists(chunks_path):
        print(f"ERROR: {chunks_path} not found"); sys.exit(1)

    with open(chunks_path) as f: chunks = json.load(f)
    chunks_map = {c['id']: c['text'] for c in chunks}
    retriever = BM25(chunks)

    results = []
    for item in queries:
        qid = item.get("id","")
        query = item.get("query","")
        print(f"[{qid}] {query[:70]}...")
        t0 = time.time()
        retrieved = retriever.retrieve(query, top_k=5)
        std_ids = [r[0] for r in retrieved]
        rationale = [] if args.no_llm else call_gemini(query, std_ids, chunks_map)
        results.append({
            "id": qid,
            "retrieved_standards": std_ids,
            "rationale": rationale,
            "latency_seconds": round(time.time()-t0, 4)
        })

    with open(args.output, "w") as f: json.dump(results, f, indent=2)
    avg_lat = sum(r['latency_seconds'] for r in results)/len(results)
    print(f"\n✅ Saved {len(results)} results → {args.output}  |  Avg latency: {avg_lat:.3f}s")

if __name__ == "__main__":
    main()
