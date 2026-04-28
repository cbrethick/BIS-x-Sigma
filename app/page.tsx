'use client';

import React, { useState } from 'react';
import { Search, Sparkles, Loader2 } from 'lucide-react';

interface StandardResult {
  retrieved_standards: string[];
  rationale: { standard_id: string; rationale: string }[];
  latency_seconds: number;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<StandardResult | null>(null);

  const performSearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setResult(null);

    try {
      // Vercel routes /api/* to the python serverless function
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch recommendations');
      }

      const data = await response.json();
      setResult(data);
    } catch (error: any) {
      console.error('Search error:', error);
      alert(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="container mx-auto max-w-4xl px-4 py-16 min-h-screen relative z-10">
      <header className="text-center mb-16">
        <div className="flex items-center justify-center gap-3 mb-4">
          <Sparkles className="w-10 h-10 text-accent-glow" />
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight">
            BIS RAG <span className="highlight-text">Engine</span>
          </h1>
        </div>
        <p className="text-text-muted text-lg md:text-xl font-light">
          AI-powered intelligent retrieval for Indian Standards.
        </p>
      </header>

      <section className="search-section max-w-2xl mx-auto mb-16">
        <div className="search-box glass rounded-full p-2 shadow-2xl flex items-center transition-all focus-within:ring-2 focus-within:ring-accent-glow/50">
          <input
            type="text"
            className="flex-1 bg-transparent border-none px-6 py-3 text-lg outline-none text-text-main placeholder:text-text-muted"
            placeholder="Describe the standards you are looking for..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && performSearch()}
          />
          <button
            onClick={performSearch}
            className="bg-gradient-to-br from-accent-glow to-accent-secondary p-4 rounded-full text-white transition-transform hover:scale-105 active:scale-95 shadow-lg"
          >
            <Search className="w-6 h-6" />
          </button>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center gap-3 mt-8 text-text-muted animate-pulse">
            <Loader2 className="w-5 h-5 animate-spin" />
            <span>Analyzing Indian Standards...</span>
          </div>
        )}
      </section>

      {result && (
        <section className="results-section animate-in fade-in slide-in-from-bottom-5 duration-500">
          <div className="flex justify-between items-center mb-8">
            <h2 className="text-2xl font-semibold">Analysis Results</h2>
            <span className="text-sm font-medium text-success bg-success/10 px-3 py-1 rounded-full border border-success/20">
              {result.latency_seconds}s
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
            {result.retrieved_standards.map((stdId, idx) => (
              <div key={idx} className="glass p-5 rounded-2xl hover:translate-y-[-4px] transition-all">
                <div className="text-lg font-bold text-accent-secondary mb-1">{stdId}</div>
                <div className="text-sm text-text-muted">Standard Reference Match</div>
              </div>
            ))}
          </div>

          <div className="space-y-4">
            {result.rationale.map((item, idx) => (
              <div key={idx} className="glass p-6 rounded-2xl border-l-4 border-l-accent-glow">
                <div className="flex items-center gap-3 mb-3">
                  <div className="bg-white/10 px-2 py-1 rounded text-xs font-bold">{item.standard_id}</div>
                </div>
                <p className="text-text-main/90 leading-relaxed">
                  {item.rationale.split('**').map((part, i) => 
                    i % 2 === 1 ? <strong key={i} className="text-white">{part}</strong> : part
                  )}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
