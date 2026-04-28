document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('queryInput');
    const searchBtn = document.getElementById('searchBtn');
    const loader = document.getElementById('loader');
    const resultsSection = document.getElementById('resultsSection');
    const latencyBadge = document.getElementById('latencyBadge');
    const standardsGrid = document.getElementById('standardsGrid');
    const rationaleContainer = document.getElementById('rationaleContainer');

    // Execute search
    const performSearch = async () => {
        const query = searchInput.value.trim();
        if (!query) return;

        // UI Reset
        resultsSection.style.display = 'none';
        standardsGrid.innerHTML = '';
        rationaleContainer.innerHTML = '';
        loader.style.display = 'flex';

        try {
            // Check if running on localhost or Vercel
            const apiUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
                ? 'http://127.0.0.1:5000/api/recommend'
                : '/api/recommend';

            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch recommendations');
            }

            renderResults(data);
        } catch (error) {
            console.error('Search error:', error);
            alert(`Error: ${error.message}`);
        } finally {
            loader.style.display = 'none';
        }
    };

    // Render logic
    const renderResults = (data) => {
        // Set latency
        latencyBadge.textContent = `${data.latency_seconds}s`;

        // Render retrieved standard IDs as small cards
        if (data.retrieved_standards && data.retrieved_standards.length > 0) {
            data.retrieved_standards.forEach(stdId => {
                const card = document.createElement('div');
                card.className = 'card';
                card.innerHTML = `
                    <div class="card-title">${stdId}</div>
                    <div class="card-desc">Bureau of Indian Standards Reference Match</div>
                `;
                standardsGrid.appendChild(card);
            });
        } else {
            standardsGrid.innerHTML = '<p style="color: var(--text-muted);">No exact standards found.</p>';
        }

        // Render AI rationale
        if (data.rationale && data.rationale.length > 0) {
            data.rationale.forEach(item => {
                const rationaleCard = document.createElement('div');
                rationaleCard.className = 'rationale-card';
                
                // Format markdown-like bold tags to HTML
                const formattedText = item.rationale.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

                rationaleCard.innerHTML = `
                    <div class="rationale-header">
                        <span class="logo-icon" style="font-size: 1.2rem;">✦</span>
                        <span class="rationale-id">${item.standard_id}</span>
                    </div>
                    <div class="rationale-text">${formattedText}</div>
                `;
                rationaleContainer.appendChild(rationaleCard);
            });
        }

        // Show section
        resultsSection.style.display = 'block';
        
        // Scroll slightly down to show results
        setTimeout(() => {
            resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    };

    // Event Listeners
    searchBtn.addEventListener('click', performSearch);
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            performSearch();
        }
    });
});
