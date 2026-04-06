// Jaimineeya Samavedam Website JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                // Update URL without jumping
                history.pushState(null, null, this.getAttribute('href'));
            }
        });
    });

    // Highlight current section in jump links
    const observerOptions = {
        root: null,
        rootMargin: '-20% 0px -70% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            const id = entry.target.getAttribute('id');
            const jumpLink = document.querySelector(`.jump-links a[href="#${id}"]`);
            if (jumpLink) {
                if (entry.isIntersecting) {
                    document.querySelectorAll('.jump-links a').forEach(a => a.classList.remove('active'));
                    jumpLink.classList.add('active');
                }
            }
        });
    }, observerOptions);

    document.querySelectorAll('.sama-entry').forEach(entry => {
        observer.observe(entry);
    });

    // Sidebar Jump Logic
    const jumpInput = document.getElementById('sidebar-jump');
    const searchBtn = document.querySelector('.search-btn');
    
    // Build a dynamic map from Parva links: displayed parva number → actual supersection ID
    const parvaMap = {};
    document.querySelectorAll('.parva-link').forEach(link => {
        const href = link.getAttribute('href') || '';
        const ssMatch = href.match(/kandah[/]([^/]+)[/]/);
        if (ssMatch) {
            const displayNum = parseInt(link.textContent.trim());
            if (!isNaN(displayNum)) {
                parvaMap[displayNum] = ssMatch[1];
            }
        }
    });

    const handleJump = () => {
        const val = jumpInput ? jumpInput.value.trim() : '';
        if (!val) return;
        
        const path = window.location.pathname;
        let depth = 0;
        if (path.includes('/kandah/')) depth = 2;
        else if (path.includes('/classification/') || path.includes('/vargeekaran/')) depth = 1;
        
        const prefix = '../'.repeat(depth);
        const parts = val.split('.');
        
        if (parts.length >= 2) {
            const parvaNum = parseInt(parts[0]);
            const parvaId = parvaMap[parvaNum] || `supersection_${parts[0]}`;
            const kandahId = parts[1];
            let url = `${prefix}kandah/${parvaId}/${kandahId}.html`;
            
            if (parts.length === 3) {
                const targetNum = parseInt(parts[2]);
                const samaLinks = document.querySelectorAll('.sama-link');
                let matchedAnchor = null;
                
                samaLinks.forEach(link => {
                    const text = link.textContent.trim();
                    const rangeMatch = text.match(/^([0-9]+)[ ]*[–—-][ ]*([0-9]+)$/);
                    if (rangeMatch) {
                        const start = parseInt(rangeMatch[1]);
                        const end = parseInt(rangeMatch[2]);
                        if (targetNum >= start && targetNum <= end) {
                            matchedAnchor = link.getAttribute('href');
                        }
                    } else {
                        const exactMatch = text.match(/^([0-9]+)$/);
                        if (exactMatch && parseInt(exactMatch[1]) === targetNum) {
                            matchedAnchor = link.getAttribute('href');
                        }
                    }
                });
                
                if (matchedAnchor) {
                    url += matchedAnchor;
                } else {
                    url += `#sama-${parts[2]}`;
                }
            }
            window.location.assign(url);
        }
    };

    if (jumpInput) {
        jumpInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                handleJump();
            }
        });
    }
    
    // Search Modal
    const searchModal = document.getElementById('search-modal');
    const searchOverlay = document.getElementById('search-overlay');
    const searchInput = document.getElementById('search-input');
    const searchClose = document.getElementById('search-close');
    const searchResults = document.getElementById('search-results');
    let searchIndex = null;
    
    const loadSearchIndex = () => {
        if (typeof SEARCH_INDEX !== 'undefined') {
            searchIndex = SEARCH_INDEX;
            if (searchResults) searchResults.innerHTML = '';
        } else {
            if (searchResults) searchResults.innerHTML = '<div class="search-no-results"><div class="icon">⚠️</div>Could not load search index.</div>';
        }
    };
    
    const openSearchModal = () => {
        if (searchModal) {
            searchModal.classList.add('active');
            searchOverlay.classList.add('active');
            if (searchInput) searchInput.focus();
            if (!searchIndex) loadSearchIndex();
        }
    };
    
    const closeSearchModal = () => {
        if (searchModal) searchModal.classList.remove('active');
        if (searchOverlay) searchOverlay.classList.remove('active');
    };
    
    if (searchClose) searchClose.addEventListener('click', closeSearchModal);
    if (searchOverlay) searchOverlay.addEventListener('click', closeSearchModal);
    
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') closeSearchModal();
        if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            openSearchModal();
        }
    });
    
    if (searchBtn) {
        searchBtn.addEventListener('click', function(e) {
            e.preventDefault();
            openSearchModal();
        });
    }
    
    document.querySelectorAll('.top-nav a').forEach(link => {
        if (link.textContent.includes('Search') || link.textContent.includes('अन्वेषणम्')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                openSearchModal();
            });
        }
    });
    
    // Detect current page depth for relative path resolution
    const currentPath = window.location.pathname;
    const isKandahPage = currentPath.includes('/kandah/');
    const depthPrefix = isKandahPage ? '../../' : '';
    
    const highlightText = (text, query) => {
        if (!query || !text) return text;
        const idx = text.toLowerCase().indexOf(query.toLowerCase());
        if (idx === -1) return text;
        return text.substring(0, idx) + '<mark>' + text.substring(idx, idx + query.length) + '</mark>' + text.substring(idx + query.length);
    };
    
    const performSearch = (query) => {
        if (!query || query.length < 2 || !searchIndex) return [];
        const q = query.toLowerCase().trim();
        const results = [];
        for (const entry of searchIndex) {
            let score = 0;
            let bestMatchField = '';
            let bestMatchScore = 0;
            let bestMatchText = '';
            
            const checkField = (text, fieldScore, fieldName) => {
                if (text.toLowerCase().includes(q)) {
                    score += fieldScore;
                    if (fieldScore > bestMatchScore) {
                        bestMatchScore = fieldScore;
                        bestMatchField = fieldName;
                        bestMatchText = text;
                    }
                }
            };
            
            checkField(entry.mantra_clean, 10, 'Mantra');
            checkField(entry.rik_clean, 8, 'Rik');
            
            for (const c of entry.classifications) {
                checkField(c.rishi, 7, 'Rishi');
                checkField(c.devata, 6, 'Devata');
                checkField(c.chandas, 4, 'Chandas');
            }
            
            checkField(entry.title_clean, 5, 'Title');
            checkField(entry.metadata_clean, 3, 'Metadata');
            
            if (score > 0) {
                results.push({ ...entry, score, matchField: bestMatchField, matchText: bestMatchText });
            }
        }
        results.sort((a, b) => b.score - a.score);
        return results.slice(0, 50);
    };
    
    if (searchInput) {
        let debounceTimer;
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                const query = this.value.trim();
                if (!query) {
                    if (searchResults) searchResults.innerHTML = '';
                    return;
                }
                if (!searchIndex) {
                    if (searchResults) searchResults.innerHTML = '<div class="search-loading">Loading search index...</div>';
                    return;
                }
                const results = performSearch(query);
                if (results.length === 0) {
                    searchResults.innerHTML = '<div class="search-no-results"><div class="icon">🔍</div>No results found for "' + query + '"</div>';
                    return;
                }
                let html = '';
                for (const r of results) {
                    let displayText;
                    if (r.matchField === 'Mantra') {
                        displayText = r.mantra_html || r.matchText;
                    } else if (r.matchField === 'Rik') {
                        displayText = r.rik_html || r.matchText;
                    } else if (r.matchField === 'Title') {
                        displayText = r.title_html || r.matchText;
                    } else if (r.matchField === 'Metadata') {
                        displayText = r.metadata_html || r.matchText;
                    } else {
                        displayText = r.matchText;
                    }
                    const highlighted = highlightText(displayText, query);
                    const classInfo = r.classifications.length > 0 
                        ? r.classifications.map(c => [c.rishi, c.devata, c.chandas].filter(Boolean).join(' | ')).join('; ')
                        : '';
                    html += `<a href="${depthPrefix}${r.link}" class="search-result-item">
                        <div class="search-result-ref">${r.ref} — ${r.parva_title}, Kandah ${r.kandah_num}</div>
                        <div class="search-result-meta">${r.matchField}${classInfo ? ' · ' + classInfo : ''}</div>
                        <div class="search-result-text">${highlighted}</div>
                    </a>`;
                }
                searchResults.innerHTML = html;
            }, 250);
        });
    }
    
    // Audio error handling
    document.querySelectorAll('audio').forEach(audio => {
        audio.addEventListener('error', function() {
            const container = this.closest('.audio-section');
            if (container) {
                container.innerHTML = `
                    <div class="audio-pending">
                        <span>🎵</span>
                        <span>Audio coming soon</span>
                    </div>
                `;
            }
        });
    });
});
