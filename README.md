# BIS Standards Recommendation Engine
**BIS x Sigma Squad AI Hackathon — RAG Track**

An AI-powered Recommendation Engine that converts product descriptions into accurate BIS standard recommendations in seconds, using Retrieval-Augmented Generation (RAG).

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd bis-rag
pip install -r requirements.txt
```

### 2. Set Gemini API Key (optional — for LLM rationale)
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```
> Without this key, the system still retrieves accurate standards via BM25 — only the rationale text is skipped.

### 3. Run Inference (for judges)
```bash
python inference.py --input hidden_private_dataset.json --output team_results.json
```

### 4. Evaluate on Public Test Set
```bash
# First generate results on public test set
python inference.py --input data/public_test_set.json --output data/public_results.json

# Then evaluate
python eval_script.py --results data/public_results.json
```

---

## 📁 Project Structure
```
bis-rag/
├── inference.py          # ← Judge entry-point (self-contained)
├── eval_script.py        # ← Official evaluation script
├── requirements.txt
├── README.md
├── presentation.pdf
├── data/
│   ├── bis_chunks.json       # Parsed BIS SP 21 standard chunks
│   ├── public_test_set.json  # 10 public queries
│   └── public_results.json   # Results on public test set
└── src/
    ├── retriever.py      # BM25 retrieval engine
    ├── llm.py            # Gemini API wrapper
    └── pipeline.py       # End-to-end pipeline
```

---

## 🏗️ System Architecture

```
User Query
    │
    ▼
[Text Preprocessing & Tokenization]
    │  - Lowercasing, stop-word removal
    │  - BIS domain stop-word list
    │
    ▼
[BM25 Retriever]
    │  - Corpus: 590 IS standard chunks from BIS SP 21
    │  - Scoring: BM25 + IS-number exact-match boost
    │  - Returns top-5 standard IDs + snippets
    │
    ▼
[Gemini 1.5 Flash LLM] (optional, requires API key)
    │  - Generates 1-2 sentence rationale per standard
    │  - Falls back gracefully if API unavailable
    │
    ▼
Output JSON: {id, retrieved_standards, rationale, latency_seconds}
```

---

## 📊 Chunking & Retrieval Strategy

### Data Ingestion
- Source: BIS SP 21 (2005) PDF — 929 pages
- Extraction: `pdftotext` for clean text extraction
- Chunking: **Standard-level chunking** — each IS standard becomes one chunk
  - Pattern: `IS XXXX : YYYY <TITLE>` used as chunk boundary
  - Result: **590 chunks**, each containing the full summary of one standard
  - Chunk size: up to 4000 characters per standard

### Retrieval
- Algorithm: **BM25** (Best Match 25) — proven IR baseline
  - Parameters: k1=1.5, b=0.75 (tuned for technical document retrieval)
  - IDF smoothed with +0.5 add-one to avoid division by zero
- **Domain stop-words**: Extended stop-word list for BIS/standards domain
  (e.g., "specification", "bureau", "bis", "standard", "material" suppressed to surface specific terms)
- **IS-number boost**: +5.0 score when query explicitly mentions an IS standard number

### Why BM25?
- No GPU required → runs on any hardware
- Sub-second latency → easily meets <5s target
- Excellent precision on keyword-rich technical queries
- No hallucination risk in retrieval step

---

## 📈 Evaluation Results (Public Test Set)

| Metric | Score | Target |
|--------|-------|--------|
| Hit Rate @3 | **100%** | >80% |
| MRR @5 | **1.0000** | >0.7 |
| Avg Latency | **<0.5s** | <5s |

---

## 💡 Impact on MSEs

Indian Micro and Small Enterprises (MSEs) currently spend **weeks** manually searching through BIS documentation to identify applicable standards. This system:

- Reduces discovery time from **weeks → seconds**
- Works **offline** (no GPU, no cloud required)
- Covers all **590 BIS building material standards** in SP 21
- Returns **top 5 standards** with rationale for human review
- **Zero hallucination** — retrieval is grounded in actual BIS text

---

## ⚙️ Environment

- Python 3.8+
- Standard library only for retrieval (no ML frameworks needed)
- `requests` for Gemini API calls
- Tested on Ubuntu 24 / macOS / Windows

---

## 📝 External APIs & Data Sources

| Resource | Usage |
|----------|-------|
| BIS SP 21 (2005) PDF | Official dataset (provided by organizers) |
| Google Gemini 1.5 Flash | LLM rationale generation (optional) |

---

## 👥 Team
RETHICK CB — [rethickcb2007@gmail.com]
