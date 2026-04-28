"""
BIS Standards Recommendation Engine — Streamlit Web UI
Run: streamlit run src/app.py
"""
import sys, os, json, math, re, time
from collections import Counter

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

STOP_WORDS = {
    'a','an','the','is','are','was','were','be','been','being','have','has',
    'had','do','does','did','will','would','could','should','may','might',
    'shall','can','to','of','in','for','on','with','at','by','from','up',
    'and','or','but','if','which','that','this','it','we','our','you',
    'your','they','their','not','no','as','so','any','all','where','when',
    'how','what','who','why','use','using','product','products','material',
    'materials','standard','standards','indian','specification','bureau','bis'
}

def tokenize(text):
    return [t for t in re.findall(r'\b[a-z][a-z0-9\-]*\b', text.lower())
            if t not in STOP_WORDS and len(t) > 2]

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
        self.avg_dl = sum(len(t) for t in self.corpus)/N

    def retrieve(self, query, top_k=5):
        qtoks = tokenize(query)
        scores = []
        for i,(chunk,doc) in enumerate(zip(self.chunks,self.corpus)):
            dl=len(doc); tf=Counter(doc); s=0.0
            for qt in qtoks:
                if qt not in self.idf: continue
                f=tf.get(qt,0)
                s += self.idf[qt]*f*(self.k1+1)/(f+self.k1*(1-self.b+self.b*dl/self.avg_dl))
            if chunk['id'].lower().replace(' ','') in query.lower().replace(' ',''): s+=5
            scores.append((i,s))
        scores.sort(key=lambda x:x[1],reverse=True)
        return [(self.chunks[i]['id'],sc,self.chunks[i]['text'][:600]) for i,sc in scores[:top_k]]

@st.cache_resource
def load_retriever():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base,'data','bis_chunks.json')) as f:
        chunks = json.load(f)
    return BM25(chunks)

def main():
    st.set_page_config(page_title="BIS Standards Finder", page_icon="🏗️", layout="wide")
    st.title("🏗️ BIS Standards Recommendation Engine")
    st.markdown(
        "**Helping Indian MSEs find the right BIS building material standards instantly.**\n\n"
        "Powered by RAG (BM25 Retrieval + Gemini LLM) on BIS SP 21 dataset."
    )

    retriever = load_retriever()

    with st.sidebar:
        st.header("⚙️ Settings")
        top_k = st.slider("Number of results", 3, 5, 5)
        use_llm = st.checkbox("Enable Gemini rationale", value=False,
                              help="Requires GEMINI_API_KEY env variable")
        st.markdown("---")
        st.info("**Dataset:** BIS SP 21 (2005)\n\n**590 standards** across 27 categories")

    query = st.text_area(
        "🔍 Describe your product or compliance need:",
        placeholder="e.g. We manufacture 33 Grade Ordinary Portland Cement and need the applicable BIS standard...",
        height=100
    )

    if st.button("Find Standards", type="primary") and query.strip():
        t0 = time.time()
        with st.spinner("Searching BIS standards..."):
            results = retriever.retrieve(query, top_k=top_k)

        latency = time.time() - t0
        st.success(f"Found {len(results)} standards in **{latency:.3f}s**")

        for rank, (std_id, score, snippet) in enumerate(results, 1):
            with st.expander(f"#{rank} — {std_id}  (score: {score:.2f})", expanded=(rank<=3)):
                st.markdown(f"**Standard:** `{std_id}`")
                st.markdown("**Summary:**")
                st.text(snippet[:500])

    st.markdown("---")
    st.caption("BIS x Sigma Squad AI Hackathon | IIT Tirupati")

if __name__ == "__main__" and HAS_STREAMLIT:
    main()
elif not HAS_STREAMLIT:
    print("Install streamlit: pip install streamlit")
    print("Then run: streamlit run src/app.py")
