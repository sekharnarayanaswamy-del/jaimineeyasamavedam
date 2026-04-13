// Jaimineeya Samavedam Website JavaScript
// Deterministic Navigation System v2.1

document.addEventListener('DOMContentLoaded', function() {
    console.log("[JS] Jaimineeya Website Loaded");

    // Centralized Scroll Handler
    const scrollToTarget = (targetId, smooth = true) => {
        if (!targetId) return;
        
        // Clean hash (strip #)
        const id = targetId.startsWith('#') ? targetId.substring(1) : targetId;
        const element = document.getElementById(id);
        
        if (element) {
            console.log("[Scroll] Navigating to:", id);
            
            // Fixed header offset (adjust based on CSS)
            const headerOffset = 100;
            const elementPosition = element.getBoundingClientRect().top;
            const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

            window.scrollTo({
                top: offsetPosition,
                behavior: smooth ? 'smooth' : 'auto'
            });
            
            return true;
        }
        console.warn("[Scroll] Target not found:", id);
        return false;
    };

    // 1. Handle Initial Load Scroll (Deterministic Wait)
    window.addEventListener('load', () => {
        if (window.location.hash) {
            console.log("[Load] Initial hash detected:", window.location.hash);
            // Wait for Sanskrit web fonts and layout to finish settling
            setTimeout(() => {
                scrollToTarget(window.location.hash, false);
            }, 200);
        }
    });

    // 2. Handle Hash Changes (Link clicks, History)
    window.addEventListener('hashchange', () => {
        console.log("[HashChange] New hash:", window.location.hash);
        scrollToTarget(window.location.hash, true);
    });

    // 3. Smooth scroll for ALL internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const hash = this.getAttribute('href');
            if (hash === '#') return;
            
            e.preventDefault();
            // Update hash which triggers hashchange listener
            if (window.location.hash === hash) {
                // Manually trigger if hash is identical
                scrollToTarget(hash, true);
            } else {
                window.location.hash = hash;
            }
        });
    });

    // 4. Parva Map for Jump resolution
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

    // 5. Jump Logic (Deterministic Two-Step)
    const jumpInput = document.getElementById('sidebar-jump');
    const handleJump = () => {
        const val = jumpInput ? jumpInput.value.trim() : '';
        if (!val) return;
        
        console.log("[Jump] Input received:", val);
        const parts = val.split('.');
        
        // Resolve prefix based on depth
        const path = window.location.pathname;
        let depth = 0;
        if (path.includes('/kandah/')) depth = 2;
        else if (path.includes('/classification/') || path.includes('/vargeekaran/')) depth = 1;
        const prefix = '../'.repeat(depth);

        if (parts.length >= 2) {
            const parvaNum = parseInt(parts[0]);
            const parvaId = parvaMap[parvaNum] || `supersection_${parts[0]}`;
            const kandahId = parts[1];
            
            const targetPage = `kandah/${parvaId}/${kandahId}.html`;
            const absoluteTargetPage = new URL(prefix + targetPage, window.location.href).pathname;
            const currentPage = window.location.pathname;
            
            let targetHash = "";
            if (parts.length === 3) {
                const targetNum = parseInt(parts[2]);
                const samaLinks = document.querySelectorAll('.sama-link');
                let matchedAnchor = null;
                
                samaLinks.forEach(link => {
                    const text = link.textContent.trim();
                    const rangeMatch = text.match(/^([0-9]+)[ ]*[–—\-][ ]*([0-9]+)$/);
                    if (rangeMatch) {
                        const start = parseInt(rangeMatch[1]);
                        const end = parseInt(rangeMatch[2]);
                        if (targetNum >= start && targetNum <= end) matchedAnchor = link.getAttribute('href');
                    } else {
                        const exactMatch = text.match(/^([0-9]+)$/);
                        if (exactMatch && parseInt(exactMatch[1]) === targetNum) matchedAnchor = link.getAttribute('href');
                    }
                });
                
                targetHash = matchedAnchor || `#v-${parts[2]}`;
            }

            console.log("[Jump] Resolving:", {targetPage, targetHash});

            // STEP 1: Determine if we need to change files
            if (currentPage.endsWith(targetPage) || currentPage.includes('/' + targetPage)) {
                // Same file: Just scroll (Step 2)
                console.log("[Jump] Same page identified, scrolling...");
                if (window.location.hash === targetHash) scrollToTarget(targetHash, true);
                else window.location.hash = targetHash;
            } else {
                // Different file: Redirect (Step 1)
                console.log("[Jump] Different page, navigating to:", prefix + targetPage + targetHash);
                window.location.assign(prefix + targetPage + targetHash);
            }
        }
    };

    if (jumpInput) {
        jumpInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') handleJump();
        });
    }

    // Search Interactivity (Standard)
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
        
        // Convert IAST/Latin input to Devanagari for matching
        const latinToDevanagari = (text) => {
            const mapping = {
                'aa': 'आ', 'ee': 'ई', 'oo': 'ऊ', 'ai': 'ऐ', 'au': 'औ', 'ri': 'ऋ', 'rii': 'ॠ',
                'kh': 'ख', 'gh': 'घ', 'ch': 'च', 'chh': 'छ', 'jh': 'झ', 'th': 'थ', 'dh': 'ध',
                'ph': 'फ', 'bh': 'भ', 'sh': 'श', 'ng': 'ङ', 'nj': 'ञ', 'nn': 'ण',
                'a': 'अ', 'i': 'इ', 'u': 'उ', 'e': 'ए', 'o': 'ओ',
                'k': 'क', 'g': 'ग', 'c': 'च', 'j': 'ज', 't': 'त', 'd': 'द', 'n': 'न',
                'p': 'प', 'b': 'ब', 'm': 'म', 'y': 'य', 'r': 'र', 'l': 'ल', 'v': 'व', 'w': 'व', 's': 'स', 'h': 'ह',
                '.': '।', '|': '॥'
            };
            let result = text.toLowerCase();
            // Process long vowels first
            for (const [k, v] of Object.entries(mapping).sort((a, b) => b[0].length - a[0].length)) {
                result = result.replaceAll(k, v);
            }
            return result;
        };
        
        // Check if query looks like Latin (contains a-z, not Devanagari)
        const isLatin = /[a-z]/.test(q) && !/[\u0900-\u097F]/.test(q);
        const devanagariQuery = isLatin ? latinToDevanagari(q) : null;
        
        for (const entry of searchIndex) {
            let score = 0;
            let matchedFields = [];
            
            const checkField = (text, fieldScore, fieldName, displayHtml) => {
                if (!text) return;
                // Remove spaces for comparison
                const wsRegex = new RegExp('\\\\s+', 'g');
                const textNoSpaces = text.replace(wsRegex, '');
                const qNoSpaces = q.replace(wsRegex, '');
                
                // Check exact match
                if (textNoSpaces.toLowerCase().includes(qNoSpaces)) {
                    score += fieldScore;
                    matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                    return;
                }
                
                // Check permissive (diacritic-stripped) match
                const textPermissive = textNoSpaces.replace(/[\u093E-\u094D\u0951-\u0954]/g, '');
                const qPermissive = qNoSpaces.replace(/[\u093E-\u094D\u0951-\u0954]/g, '');
                if (textPermissive.toLowerCase().includes(qPermissive)) {
                    score += fieldScore * 0.8;
                    matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                    return;
                }
                
                // Check Latin transliteration match
                if (isLatin && devanagariQuery) {
                    const textLatin = textNoSpaces.replace(/[\u093E-\u094D\u0951-\u0954]/g, '');
                    const dqNoSpaces = devanagariQuery.replace(wsRegex, '');
                    if (textLatin.toLowerCase().includes(dqNoSpaces.toLowerCase())) {
                        score += fieldScore * 0.7;
                        matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                    }
                }
            };
            
            checkField(entry.mantra_clean, 10, 'Mantra', entry.mantra_html);
            checkField(entry.rik_clean, 8, 'Rik', entry.rik_html);
            
            for (const c of entry.classifications) {
                checkField(c.rishi_clean, 7, 'Rishi', c.rishi);
                checkField(c.devata_clean, 6, 'Devata', c.devata);
                checkField(c.chandas_clean, 4, 'Chandas', c.chandas);
            }
            
            checkField(entry.title_clean, 5, 'Title', entry.title_html);
            checkField(entry.metadata_clean, 3, 'Metadata', entry.metadata_html);
            
            if (score > 0) {
                results.push({ ...entry, score, matchedFields });
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
                    const classInfo = r.classifications.length > 0 
                        ? r.classifications.map(c => [c.rishi, c.devata, c.chandas].filter(Boolean).join(' | ')).join('; ')
                        : '';
                    const fieldLabels = { 'Mantra': 'मन्त्र', 'Rik': 'ऋक्', 'Rishi': 'ऋषि', 'Devata': 'देवता', 'Chandas': 'छन्दस्', 'Title': 'शीर्षक', 'Metadata': 'विवरण' };
                    let fieldsHtml = '';
                    for (const mf of r.matchedFields) {
                        const highlighted = highlightText(mf.html || mf.text, query);
                        const label = fieldLabels[mf.name] || mf.name;
                        fieldsHtml += `<div class="search-result-field"><span class="search-result-field-label">${label}</span><div class="search-result-text">${highlighted}</div></div>`;
                    }
                    html += `<div class="search-result-item">
                        <div class="search-result-ref"><a href="${depthPrefix}${r.link}">${r.ref} — ${r.parva_title}, Kandah ${r.kandah_num}</a></div>
                        <div class="search-result-meta">${classInfo || ''}</div>
                        ${fieldsHtml}
                    </div>`;
                }
                searchResults.innerHTML = html;
                
                // Add click handlers to result items for navigation
                document.querySelectorAll('.search-result-item').forEach(item => {
                    let startX, startY;
                    item.addEventListener('mousedown', function(e) {
                        if (e.button !== 0) return;
                        startX = e.clientX;
                        startY = e.clientY;
                    });
                    item.addEventListener('mouseup', function(e) {
                        if (e.button !== 0) return;
                        const dx = Math.abs(e.clientX - startX);
                        const dy = Math.abs(e.clientY - startY);
                        if (dx > 5 || dy > 5) return;
                        const selection = window.getSelection();
                        if (selection && selection.toString().trim().length > 0) {
                            return;
                        }
                        const link = this.querySelector('.search-result-ref a');
                        if (link) {
                            window.location.href = link.href;
                        }
                    });
                    // Double-click always navigates
                    item.addEventListener('dblclick', function(e) {
                        const link = this.querySelector('.search-result-ref a');
                        if (link) {
                            window.location.href = link.href;
                        }
                    });
                });
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
