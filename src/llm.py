"""
Gemini API wrapper for generating rationale for retrieved BIS standards.
Uses google-generativeai REST API via requests.
Set GEMINI_API_KEY environment variable before running.
"""

import os
import json
import requests
from typing import List, Tuple


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AIzaSyCE04Yl01Nfnsv7W8b0Wco_XEksZctkumg")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)


def generate_rationale(
    query: str,
    retrieved: List[Tuple[str, float, str]],
    top_k: int = 5
) -> List[dict]:
    """
    Given a query and retrieved chunks, use Gemini to generate a short rationale
    for each top standard. Falls back to snippet if API key not set.
    """
    standards_info = "\n\n".join(
        f"[{std_id}]\n{snippet[:500]}"
        for std_id, score, snippet in retrieved[:top_k]
    )

    prompt = f"""You are a BIS (Bureau of Indian Standards) compliance expert helping Indian MSEs.

A business asked: "{query}"

Here are the top matching BIS standards from SP 21:
{standards_info}

For each standard listed above, provide:
1. The standard ID (exactly as given in brackets above)
2. A 1-2 sentence rationale explaining why it is relevant to the query.

Respond in JSON array format ONLY, like:
[
  {{"standard_id": "IS XXX : YYYY", "rationale": "..."}},
  ...
]
Return ONLY the JSON array, no other text."""

    if not GEMINI_API_KEY:
        # Fallback: return snippets as rationale
        return [
            {"standard_id": std_id, "rationale": snippet[:200]}
            for std_id, score, snippet in retrieved[:top_k]
        ]

    try:
        url = GEMINI_URL.format(key=GEMINI_API_KEY)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            }
        }
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        # Strip markdown fences if any
        text = text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(text)
    except Exception as e:
        print(f"[LLM Warning] Gemini call failed: {e}. Using fallback.")
        return [
            {"standard_id": std_id, "rationale": snippet[:200]}
            for std_id, score, snippet in retrieved[:top_k]
        ]
