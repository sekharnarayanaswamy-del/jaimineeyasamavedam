"""
Static Assets Generator for Jaimineeya Samaveda Website
Generates CSS stylesheets (including palette, layout, and swara modifier typography)
and deterministic client-side JavaScript.
"""

from pathlib import Path


def generate_main_js() -> str:
    """Return client-side JavaScript for navigation and search."""
    return r"""// Jaimineeya Samavedam Website JavaScript
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

    // 5. Consolidated Navigation Logic (Deterministic P.K.S Resolution)
    window.resolveJump = (val, smooth = true) => {
        if (!val) return;
        
        console.log("[Navigation] Resolving reference:", val);
        const parts = val.split('.');
        
        // Resolve prefix based on current depth
        const path = window.location.pathname;
        let depth = 0;
        if (path.includes('/kandah/')) depth = 2;
        else if (path.includes('/classification/') || path.includes('/vargeekaran/')) depth = 1;
        const prefix = '../'.repeat(depth);

        if (parts.length >= 2) {
            const parvaNum = parseInt(parts[0]);
            
            // Site-aware prefix resolution (Handles Samhita vs Aaranam cross-links)
            let sitePrefix = "";
            const currentPath = window.location.pathname;
            
            // Only switch sites if the parvaNum is NOT in our local parvaMap
            if (!parvaMap[parvaNum]) {
                if (parvaNum <= 6 && currentPath.includes('/aaranam/')) {
                    sitePrefix = "../samhita/";
                } else if (parvaNum > 6 && currentPath.includes('/samhita/')) {
                    sitePrefix = "../aaranam/";
                }
            }

            const parvaId = parvaMap[parvaNum] || `supersection_${parts[0]}`;
            const kandahId = parts[1];
            
            // Deterministic hash: point to specific Samam Sequence ID (#sama-N)
            const targetHash = parts.length === 3 ? `#sama-${parts[2]}` : "";
            const targetPage = `kandah/${parvaId}/${kandahId}.html`;
            const currentPage = window.location.pathname;
            
            console.log("[Navigation] Target determined:", prefix + sitePrefix + targetPage + targetHash);

            if (currentPage.endsWith(targetPage) || currentPage.includes('/' + targetPage)) {
                // Same file: Just scroll
                if (window.location.hash === targetHash) scrollToTarget(targetHash, true);
                else window.location.hash = targetHash;
            } else {
                // Different file: Redirect
                window.location.assign(prefix + sitePrefix + targetPage + targetHash);
            }
            return true;
        }
        return false;
    };

    // Link Jump Box to Consolidated Logic
    const jumpInput = document.getElementById('sidebar-jump');
    const handleJump = () => {
        const val = jumpInput ? jumpInput.value.trim() : '';
        window.resolveJump(val, true);
    };

    // 6. Sidebar Highlighting (Intersection Observer)
    const observerOptions = {
        root: null,
        rootMargin: '-100px 0px -70% 0px',
        threshold: 0
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const samaStart = entry.target.getAttribute('data-sama-start');
                if (samaStart) {
                    document.querySelectorAll('.nav-links a.active, .jump-links a.active').forEach(l => {
                        l.classList.remove('active');
                    });
                    
                    const links = document.querySelectorAll(`.nav-links a[href="#sama-${samaStart}"], .jump-links a[href="#sama-${samaStart}"]`);
                    links.forEach(l => {
                        l.classList.add('active');
                    });
                }
            }
        });
    }, observerOptions);

    document.querySelectorAll('.sama-entry').forEach(el => observer.observe(el));

    if (jumpInput) {
        jumpInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') handleJump();
        });
    }

    // Search Interactivity (Standard)
    const searchModal = document.getElementById('search-modal');
    const searchOverlay = document.getElementById('search-overlay');
    const searchInput = document.getElementById('search-input');
    const searchClose = document.getElementById('search-close');
    const searchResults = document.getElementById('search-results');
    const searchBtn = document.querySelector('.search-btn');
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
    const path = window.location.pathname;
    let depth = 0;
    if (path.includes('/kandah/')) depth = 2;
    else if (path.includes('/classification/') || path.includes('/vargeekaran/')) depth = 1;
    const depthPrefix = '../'.repeat(depth);
    
const highlightText = (text, query, devanagariQuery) => {
        if (!text) return text;
        if (!query && !devanagariQuery) return text;

        let searchQ = query;
        if (devanagariQuery && devanagariQuery.length > 0) {
            searchQ = devanagariQuery;
        }

        if (text.toLowerCase().indexOf(searchQ.toLowerCase()) !== -1) {
            const re = new RegExp(searchQ.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
            return text.replace(re, '<mark>$&</mark>');
        }

        return text;
    };

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
        for (const [k, v] of Object.entries(mapping).sort((a, b) => b[0].length - a[0].length)) {
            result = result.replaceAll(k, v);
        }
        return result;
    };

    const performSearch = (query, callIsLatin, callDevanagariQuery) => {
        if (!query || query.length < 2 || !searchIndex) return [];
        const q = query.toLowerCase().trim();
        const results = [];

        const isLatin = callIsLatin !== undefined ? callIsLatin : (/[a-z]/.test(q) && !/[\u0900-\u097F]/.test(q));

        const normalizeLatin = (text) => {
            if (!text) return "";
            const map = {
                'aa': 'a', 'ee': 'i', 'oo': 'u', 'ii': 'i', 'uu': 'u',
                'kh': 'k', 'gh': 'g', 'ch': 'c', 'jh': 'j', 'th': 't', 'dh': 'd', 'ph': 'p', 'bh': 'b',
                'sh': 's', 'z': 's', 'w': 'v', 'ñ': 'n', 'ṅ': 'n', 'ṇ': 'n', 'ś': 's', 'ṣ': 's',
                'ā': 'a', 'ī': 'i', 'ū': 'u', 'ṛ': 'r', 'ṭ': 't', 'ḍ': 'd', 'ḥ': 'h', 'ṃ': 'n', 'ṁ': 'n'
            };
            let result = text.toLowerCase().replace(/[^a-z]/g, '');
            for (const [k, v] of Object.entries(map)) {
                result = result.replaceAll(k, v);
            }
            return result;
        };

        // Use the passed devanagariQuery if provided, otherwise compute it
        const devanagariQuery = callDevanagariQuery !== undefined ? callDevanagariQuery : (isLatin ? latinToDevanagari(q) : null);

        for (const entry of searchIndex) {
            let score = 0;
            let matchedFields = [];
            
            const checkField = (text, fieldScore, fieldName, displayHtml) => {
                if (!text) return;
                // Remove spaces for comparison
                const wsRegex = /\s+/g;
                const textNoSpaces = text.replace(wsRegex, '');
                const qNoSpaces = q.replace(wsRegex, '');
                
                // Check exact match
                if (textNoSpaces.toLowerCase().includes(qNoSpaces)) {
                    score += fieldScore;
                    matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                    return;
                }
                
                // Check permissive (diacritic-stripped) match
                // We must strip parentheses content for Samam swara ignoring
                const stripAll = (t) => t.replace(/\([^)]*\)/g, '').replace(/[\u093E-\u094D\u0951-\u0957\u1CD0-\u1CFF\u0964\u0965\u0966-\u096F0-9]/g, '');
                const textPermissive = stripAll(textNoSpaces);
                const qPermissive = stripAll(qNoSpaces);
                if (textPermissive.toLowerCase().includes(qPermissive)) {
                    score += fieldScore * 0.8;
                    matchedFields.push({ name: fieldName, text: text, html: displayHtml, matchedInDevanagari: true });
                    return;
                }
                
                // Check Latin match if input is Latin
                if (isLatin) {
                    const qLatin = normalizeLatin(qNoSpaces);
                    // Match against various latin fields found in entries
                    if (fieldName === 'Mantra' && entry.mantra_latin && entry.mantra_latin.includes(qLatin)) {
                        score += fieldScore * 0.75;
                        matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                    } else if (fieldName === 'Rik' && entry.rik_latin && entry.rik_latin.includes(qLatin)) {
                        score += fieldScore * 0.75;
                        matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                    } else if (fieldName === 'Title' && entry.title_latin && entry.title_latin.includes(qLatin)) {
                        score += fieldScore * 0.75;
                        matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                    } else if (devanagariQuery) {
                        // Fallback: check Devanagari conversion match
                        const textLatin = textNoSpaces.replace(/[\u093E-\u094D\u0951-\u0954]/g, '');
                        const dqNoSpaces = devanagariQuery.replace(wsRegex, '');
                        if (textLatin.toLowerCase().includes(dqNoSpaces.toLowerCase())) {
                            score += fieldScore * 0.65;
                            matchedFields.push({ name: fieldName, text: text, html: displayHtml });
                        }
                    }
                }
            };
            
            checkField(entry.mantra_clean, 10, 'Mantra', entry.mantra_html);
            checkField(entry.rik_clean, 8, 'Rik', entry.rik_html);
            
            for (const c of entry.classifications) {
                checkField(c.rishi_clean, 7, 'Rishi', c.rishi);
                // Latin match for Rishi
                if (isLatin && c.rishi_latin && c.rishi_latin.includes(normalizeLatin(q))) {
                    score += 5; matchedFields.push({ name: 'Rishi', text: c.rishi_clean, html: c.rishi });
                }
                
                checkField(c.devata_clean, 6, 'Devata', c.devata);
                // Latin match for Devata
                if (isLatin && c.devata_latin && c.devata_latin.includes(normalizeLatin(q))) {
                    score += 4; matchedFields.push({ name: 'Devata', text: c.devata_clean, html: c.devata });
                }
                
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
                const q = query.toLowerCase().trim();
                const isLatin = /[a-z]/.test(q) && !/[\u0900-\u097F]/.test(q);
                const devanagariQuery = isLatin ? latinToDevanagari(q) : null;
                const results = performSearch(query, isLatin, devanagariQuery);
                if (results.length === 0) {
                    searchResults.innerHTML = '<div class="search-no-results"><div class="icon">🔍</div>No results found for "' + query + '"</div>';
                    return;
                }
                let html = '';
                for (const r of results) {
                    const classInfo = r.classifications.length > 0 
                        ? r.classifications.map(c => [c.rishi, c.devata, c.chandas].filter(Boolean).join(' | ')).filter(Boolean).join('; ')
                        : '';
                    const fieldLabels = { 'Mantra': 'मन्त्र', 'Rik': 'ऋक्', 'Rishi': 'ऋषि', 'Devata': 'देवता', 'Chandas': 'छन्दस्', 'Title': 'शीर्षक', 'Metadata': 'विवरण' };
                    let fieldsHtml = '';
                    for (const mf of r.matchedFields) {
                        const highlighted = highlightText(mf.html || mf.text, query, devanagariQuery);
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
                            // Extract reference from text (e.g. "1.1.1 — ...")
                            const refPart = link.textContent.split('—')[0].trim();
                            if (refPart && window.resolveJump) {
                                e.preventDefault();
                                window.resolveJump(refPart, true);
                                closeSearchModal();
                            } else {
                                window.location.href = link.href;
                            }
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
"""


def generate_styles_css(font: str = 'AdishilaVedic', font_sans: str = 'AdishilaSanVedic', is_malayalam: bool = False, kpully: bool = False) -> str:
    """Generate complete CSS stylesheet matching standalone HTML viewer swara modifier typography."""
    if 'notosans' in font.lower():
        sw_off = '0.15em'
        ka_off = '0.1em'
        tr_off = '0.1em'
        an_off = '0.1em'
    else:
        sw_off = '0.15em'
        ka_off = '0.1em'
        tr_off = '0.1em'
        an_off = '0.1em'

    css = """/* Jaimineeya Samavedam Website Styles */
/* User Defined Palette */

:root {
/* Core Palette */
--color-bg-main: #F9F4E8;   /* Eggshell */
--color-bg-card: #EFE6D5;   /* Antique White */
--color-text: #2C2C2C;      /* Charcoal */
--color-accent: #FF6B35;    /* Saffron (Restored) */
--color-primary: var(--color-accent);
--color-secondary: var(--color-text);

/* Theme Semantic Mapping */
--primary-maroon: var(--color-accent); /* Headings/Links = Saffron */
--primary-gold: #8B5A2B;    /* High-contrast Dark Earthy Gold */
--accent-orange: #D2691E;   /* Chocolate */

/* Backgrounds */
--bg-main: var(--color-bg-main);
--bg-sidebar: #FCF9F0;
--bg-hover: #E8DCC0;
--bg-card: var(--color-bg-card);
--bg-verse: var(--bg-card);

/* Text */
--text-primary: var(--color-text);
--text-secondary: #4A4A4A;
--text-muted: #6B6B6B;
--text-link: #D35400;      /* Darker Saffron for contrast */
--text-link-hover: var(--color-accent); /* Saffron on hover/active */

--border-color: #D8CCB8;
--border-light: #E8DCC0;

/* Swara & Mantra System Variables */
--font-doc: {font_doc};
--font-swara: 'JaimineeyaSwara', 'Noto Serif Grantha', serif;
--font-size: 1.3rem;
--mantra-size: calc(var(--font-size) * 1.25);
--swara-size: {swara_size_val};
--primary-color: #000000;
--swara-red: #c62828;
--modifier-color: #0284c7;

/* Typography */
--font-heading: '{self.font}', '{self.font_sans}', 'Noto Serif Devanagari', 'Noto Sans Devanagari', serif;
--font-body: '{self.font}', '{self.font_sans}', 'Noto Sans Devanagari', 'Inter', sans-serif;
--font-sanskrit: '{self.font}', '{self.font_sans}', 'Noto Serif Devanagari', 'Siddhanta', serif;

/* Spacing */
--spacing-xs: 0.25rem;
--spacing-sm: 0.5rem;
--spacing-md: 1rem;
--spacing-lg: 1.5rem;
--spacing-xl: 2rem;
--spacing-2xl: 3rem;

/* Layout */
--sidebar-width: 280px;
}

/* Reset & Base */
*, *::before, *::after {
box-sizing: border-box;
margin: 0;
padding: 0;
}

html {
scroll-behavior: smooth;
font-size: 16px;
}

body {
font-family: var(--font-body);
background: var(--bg-main);
color: var(--text-primary);
line-height: 1.8;
min-height: 100vh;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
font-family: var(--font-heading);
font-weight: 600;
line-height: 1.4;
margin-bottom: var(--spacing-md);
color: var(--color-secondary); /* Headings in Dark Gray */
padding-bottom: 0.1rem;
display: inline-block;
}

h1 { font-size: 2.4rem; }
h2 { font-size: 1.8rem; }
h3 { font-size: 1.4rem; }
h4 { font-size: 1.2rem; }

/* Numerals and Counts in Adishila San Vedic (Sans Look) */
.stat-value, .rishi-rank, .number, .nav-links a, .toc-list li a, .jump-links a, .footnote-ref, .stats-summary, .stats-summary strong, .count, .rishi-count, .stats, .alpha-count, .item-count, .item-refs a, .item-count-badge, .sama-id, .sama-id a, .jump-input {{
    font-family: '{self.font_sans}', 'Noto Sans Devanagari', 'Inter', sans-serif !important;
}}

.stat-label, .rik-metadata, .mantra-number, .sama-header-text, .sama-metadata-text, .classification-table th, .classification-table td, .class-value, .class-label, .page-subtitle, .sama-count, .nav-section h3, .sidebar-right h3 {{
    font-family: '{self.font}', 'Noto Serif Devanagari', serif !important;
}}

.sanskrit-text {
font-family: var(--font-sanskrit);
font-size: 1.2rem;
line-height: 2;
letter-spacing: 0.02em;
}

.sanskrit-large {
font-size: 1.4rem;
line-height: 2.2;
}

/* Links */
a {
color: var(--text-link);
text-decoration: none;
transition: all 0.2s ease;
}

a:hover {
color: var(--text-link-hover);
text-decoration: none;
}

/* Main Layout - 3 Column */
.page-container {
display: flex;
min-height: 100vh;
}

/* Left Sidebar */
.sidebar-left {
width: var(--sidebar-width);
background: var(--bg-sidebar);
border-right: 1px solid var(--border-color);
padding: var(--spacing-lg);
position: fixed;
height: 100vh;
overflow-y: auto;
box-shadow: 2px 0 10px rgba(0,0,0,0.02);
}

.sidebar-left::-webkit-scrollbar {
width: 6px;
}

.sidebar-left::-webkit-scrollbar-thumb {
background: var(--color-primary);
border-radius: 3px;
}

.logo {
margin-bottom: var(--spacing-xl);
padding-bottom: var(--spacing-lg);
border-bottom: 1px solid var(--border-color);
text-align: center;
}

.logo-text {
font-family: var(--font-heading);
font-size: 1.8rem;
color: var(--color-primary);
font-weight: 700;
}

.logo-subtitle {
font-size: 1rem;
color: var(--text-muted);
margin-top: 4px;
text-transform: capitalize !important;
letter-spacing: 0.02em;
}

.nav-section {
margin-bottom: var(--spacing-xl);
}

.nav-section h3 {
font-size: 1.15rem;
color: var(--color-secondary);
text-transform: none;
letter-spacing: normal;
margin-bottom: var(--spacing-sm);
font-weight: normal; 
border-bottom: none;
}

.nav-section h3 .number, .sidebar-right h3 .number {
    font-size: 0.85rem;
    font-weight: 500;
}

.nav-links {
display: flex;
flex-wrap: wrap;
gap: var(--spacing-xs);
}

.nav-links a {
display: inline-block;
padding: 4px 10px;
background: var(--bg-card);
border: 1px solid var(--border-color);
border-radius: 4px;
font-size: 0.7rem;
transition: all 0.2s ease;
color: var(--text-secondary);
font-weight: 500;
}

.nav-links a:hover,
.nav-links a.active {
background: var(--color-accent);
color: white;
border-color: var(--color-accent);
box-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);
}

.nav-list {
list-style: none;
}

.jump-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    font-family: 'AdishilaSanVedic', 'Adishila San Vedic', 'Noto Sans Devanagari', 'Inter', sans-serif !important;
    font-size: 0.9rem;
    margin-top: 4px;
    background: white;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
}

.jump-input:focus {
    outline: none;
    border-color: var(--color-accent);
    box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.1);
}

.search-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
    padding: 12px;
    background: #FFFDF8;
    border: 1px solid #C08535;
    border-radius: 10px;
    color: #8B4513;
    font-weight: 600;
    text-decoration: none !important;
    transition: all 0.2s ease;
    width: 100%;
    margin-top: 10px;
    font-family: var(--font-sanskrit);
}

.search-btn:hover {
    background: white;
    box-shadow: 0 4px 12px rgba(192, 133, 53, 0.15);
    transform: translateY(-1px);
}

.sidebar-footer {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-color);
}

.footer-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem 0.8rem;
    background: #F4F1EA;
    border-radius: 6px;
    font-size: 1rem;
    color: var(--text-secondary);
    text-decoration: none !important;
    transition: all 0.2s ease;
    font-family: var(--font-sanskrit);
    min-width: 70px;
    flex: 1 1 calc(33.33% - 0.5rem);
}

.footer-btn:hover {
    background: #E8DCC0;
    color: var(--primary-maroon);
}

.nav-list li {
margin-bottom: var(--spacing-xs);
}

.nav-list a {
display: block;
padding: 8px 12px;
border-radius: 6px;
transition: background 0.2s ease;
font-family: var(--font-sanskrit);
font-size: 1.15rem;
color: var(--text-primary);
border: 1px solid transparent;
}

.nav-list a:hover {
background: var(--color-primary);
color: white;
box-shadow: 0 2px 6px rgba(255, 107, 53, 0.3);
transform: translateX(4px);
border-color: var(--color-primary);
}

/* Main Content */
.main-content {
flex: 1;
margin-left: var(--sidebar-width);
padding: var(--spacing-md) var(--spacing-2xl);
max-width: 900px;
}

/* Right Sidebar (Jump Navigation) */
.sidebar-right {
width: 220px;
padding: var(--spacing-lg);
position: fixed;
right: 0;
height: 100vh;
overflow-y: auto;
border-left: 1px solid var(--border-color);
background: var(--bg-sidebar);
}

.sidebar-right h3 {
    font-size: 0.85rem;
    color: var(--text-muted);
    text-transform: none;
    letter-spacing: normal;
    margin-bottom: var(--spacing-md);
    font-weight: normal; /* Explicitly regular */
    border-bottom: none;
}

.jump-links {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
}

.jump-links a {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.7rem;
    transition: all 0.2s ease;
    color: var(--text-secondary);
    font-weight: 500;
}

.jump-links a:hover {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
    text-decoration: none;
    box-shadow: 0 2px 4px rgba(255, 107, 53, 0.3);
}

/* Page Header */
.page-header {
    margin-bottom: var(--spacing-lg);
    padding-bottom: 0;
    border-bottom: none;
}

.page-header h1 {
    margin-top: 0;
    margin-bottom: var(--spacing-xs);
}

.page-subtitle {
    color: var(--text-secondary);
    font-size: 1.1rem;
    font-family: var(--font-sanskrit);
}

.page-meta {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-top: var(--spacing-sm);
}

.page-meta .page-subtitle {
    margin: 0;
}

.sama-count {
    display: inline-block;
    font-size: 1.1rem;
    color: var(--text-secondary);
}

.page-meta .number {
    font-size: 0.8rem;
    font-weight: 400;
}

/* Top Nav Links (Mukhyaprshtam / Anveshanam) */
.top-nav {
    display: flex;
    justify-content: flex-end;
    gap: 1.5rem;
    margin-bottom: var(--spacing-md);
    font-family: var(--font-heading);
}

.top-nav a {
    color: var(--text-secondary);
    font-size: 1rem;
    font-weight: 500;
    transition: all 0.2s ease;
    padding: 2px 4px;
}

.top-nav a:hover {
    color: var(--color-accent);
    transform: translateY(-1px);
}

.top-nav .nav-icon {
    margin-right: 4px;
    font-style: normal;
}

/* Breadcrumb */
.breadcrumb {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-lg);
    font-size: 1.25rem;
    font-family: var(--font-sanskrit);
}

.breadcrumb a {
    color: var(--text-link);
}

.breadcrumb-separator {
    color: var(--text-muted);
}

/* Table of Contents */
.toc {
    background: var(--bg-sidebar);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-2xl);
}

.toc h4 {
    margin-bottom: var(--spacing-md);
    font-size: 1.2rem;
}

.toc-list {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-xs);
    list-style: none;
}

.toc-list li a {
    display: inline-block;
    padding: 4px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 4px;
    font-size: 0.9rem;
}

.toc-list li a:hover {
    background: var(--primary-maroon);
    color: white;
    border-color: var(--primary-maroon);
    text-decoration: none;
}

/* Sama Entry (Verse) - Rig Veda Style */
.sama-anchor, .rik-anchor {
    scroll-margin-top: 100px;
    display: block;
    height: 0;
    overflow: hidden;
    visibility: hidden;
    pointer-events: none;
}

.sama-entry {
    scroll-margin-top: 100px;
    margin-bottom: var(--spacing-2xl);
    padding-bottom: var(--spacing-xl);
    border-bottom: 1px solid var(--border-light);
}

.sama-entry:last-child {
    border-bottom: none;
}

.sama-header {
    display: flex;
    align-items: baseline;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-md);
}

.sama-id {
    font-family: var(--font-heading);
    font-size: 0.9rem;
    color: var(--primary-maroon);
    font-weight: 600;
    background: var(--bg-sidebar);
    padding: 2px 10px;
    border-radius: 4px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 22px;
    line-height: normal;
    transform: translateY(5px);
}

.sama-id a {
    color: var(--primary-maroon);
}

.sama-id a:hover {
    text-decoration: none;
}

.sama-id-row {
    margin-bottom: 0rem;
    margin-top: 0.5rem;
}

/* Metadata Links (Rishi, Devata, Chandas) */
.metadata-links {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-md);
}

.metadata-link {
    display: inline-block;
    padding: 4px 12px;
    background: var(--bg-sidebar);
    border-radius: 4px;
    font-size: 0.9rem;
    color: var(--text-secondary);
    transition: all 0.2s ease;
}

.metadata-link:hover {
    background: var(--primary-gold);
    color: var(--text-primary);
    text-decoration: none;
}

.metadata-link.rishi {
    border-left: 3px solid #8B4513;
}

.metadata-link.devata {
    border-left: 3px solid #B22222;
}

.metadata-link.chandas {
    border-left: 3px solid #DAA520;
}

/* Sama Title */
.sama-title {
    font-family: var(--font-sanskrit);
    font-size: 1.1rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-md);
    font-style: italic;
}

/* Rik Metadata - displayed above Rik text in purple */
.rik-metadata {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    color: #7b1fa2;
    text-align: center;
    margin-bottom: var(--spacing-sm);
}

/* Sama Header Container - Flex row for Title + Metadata */
.sama-header-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: var(--spacing-md);
    flex-wrap: wrap;
    margin-bottom: var(--spacing-sm);
}

/* Sama Header Text - displayed above Sama/Mantra text in green */
.sama-header-text {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    color: #2e7d32;
    text-align: center;
    width: auto;
    max-width: fit-content;
}
.proc-link-text {
    font-size: 0.9rem !important;
    vertical-align: middle;
    margin-left: 10px;
    color: #2e7d32;
    text-decoration: none;
    opacity: 0.8;
}

.proc-link-text:hover {
    opacity: 1;
    text-decoration: underline;
}

.procedure-box {
    background: #F0F4F7;
    border-left: 4px solid #2e7d32;
    padding: var(--spacing-md) var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

.procedure-label {
    font-size: 0.75rem;
    color: #2e7d32;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.procedure-text {
    font-family: var(--font-sanskrit);
    font-size: 1.4rem;
    line-height: 1.8;
    color: var(--text-primary);
}

/* Sama Metadata Text - displayed above Sama/Mantra text in Brown */
.sama-metadata-text {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    color: #8B4513;
    text-align: center;
    width: auto;
    max-width: fit-content;
}
.proc-link-text {
    font-size: 0.9rem !important;
    vertical-align: middle;
    margin-left: 10px;
    color: #2e7d32;
    text-decoration: none;
    opacity: 0.8;
}

.proc-link-text:hover {
    opacity: 1;
    text-decoration: underline;
}

.procedure-box {
    background: #F0F4F7;
    border-left: 4px solid #2e7d32;
    padding: var(--spacing-md) var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}

.procedure-label {
    font-size: 0.75rem;
    color: #2e7d32;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.procedure-text {
    font-family: var(--font-sanskrit);
    font-size: 1.4rem;
    line-height: 1.8;
    color: var(--text-primary);
}

/* Rik Text Box */
.rik-box {
    background: #FFF8DC;
    border-left: 4px solid var(--primary-gold);
    padding: var(--spacing-md) var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    border-radius: 0 8px 8px 0;
}

.rik-label {
    font-size: 0.75rem;
    color: var(--primary-gold);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.rik-text {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    line-height: 2;
    color: #1565c0;
    text-align: center;
}

/* Mantra Text Box */
.mantra-box {
    background: var(--bg-verse);
    border-left: 4px solid var(--primary-maroon);
    padding: var(--spacing-md) var(--spacing-lg);
    margin-bottom: var(--spacing-md);
    border-radius: 0 8px 8px 0;
}

.mantra-label {
    font-size: 0.75rem;
    color: var(--primary-maroon);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.mantra-container {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    line-height: 2.2;
    color: var(--text-primary);
    text-align: left;
}

/* Audio Section */
.audio-section {
    margin-top: var(--spacing-md);
}

.audio-player {
    width: 100%;
    margin-top: 5px;
}

.index-list {
    column-count: 3;
    column-gap: 2.5rem;
    column-rule: 1px solid var(--border-light);
    margin-top: 2rem;
}

@media (max-width: 1200px) {
    .index-list {
        column-count: 2;
    }
}

@media (max-width: 800px) {
    .index-list {
        column-count: 1;
    }
}

.index-char-group {
    break-inside: avoid-column;
    margin-bottom: 2rem;
}

.audio-pending {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg-sidebar);
    border: 1px dashed var(--border-color);
    border-radius: 4px;
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Footnotes */
.footnotes {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-md);
    border-top: 1px dashed var(--border-color);
}

.footnotes-label {
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-bottom: var(--spacing-xs);
}

.footnote-item {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-xs);
    padding-left: var(--spacing-md);
    border-left: 2px solid var(--border-color);
}

/* Homepage Styles */
.home-hero {
    text-align: center;
    padding: var(--spacing-lg) 0;
    margin-bottom: var(--spacing-xl);
    border-bottom: 1px solid var(--border-light);
}

.home-hero h1 {
    font-size: 3rem;
    margin-bottom: var(--spacing-sm);
}

.home-hero .subtitle {
    font-size: 1.5rem;
    color: var(--text-secondary);
}

.stats-row {
    display: flex;
    justify-content: center;
    gap: var(--spacing-2xl);
    margin-top: var(--spacing-xl);
}

.stat-item {
    text-align: center;
}

.stat-value {
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--primary-maroon);
}

.stat-label {
    font-size: 1.3rem;
    color: var(--text-muted);
}

/* Parva Grid */
.parva-section {
    margin-bottom: var(--spacing-xl);
}

.parva-section h2 {
    margin-bottom: var(--spacing-md);
    padding-bottom: 4px;
    border-bottom: none;
}

.kandah-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: var(--spacing-md);
}

.kandah-card {
    display: block;
    padding: var(--spacing-md);
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    transition: all 0.2s ease;
}

.kandah-card:hover {
    border-color: var(--primary-maroon);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    text-decoration: none;
}

.kandah-card .number {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-maroon);
}

.kandah-card .title {
    font-family: var(--font-sanskrit);
    font-size: 1.4rem;
    color: var(--text-primary);
    margin: var(--spacing-xs) 0;
}

.kandah-card .count {
    font-size: 0.85rem;
    color: var(--text-muted);
}

/* Footer */
.footer {
    margin-top: var(--spacing-2xl);
    padding: var(--spacing-xl);
    border-top: 1px solid var(--border-color);
    text-align: center;
    color: var(--text-muted);
    font-size: 0.9rem;
}

/* Search Modal */
.search-overlay {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9998;
}

.search-overlay.active {
    display: block;
}

.search-modal {
    display: none;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 90%;
    max-width: 700px;
    max-height: 80vh;
    background: var(--bg-main);
    border-radius: 12px;
    z-index: 9999;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
    overflow: hidden;
    flex-direction: column;
}

.search-modal.active {
    display: flex;
}

.search-modal-content {
    display: flex;
    flex-direction: column;
    height: 100%;
    min-height: 0;
}

.search-modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 20px;
    background: var(--bg-sidebar);
    border-bottom: 1px solid var(--border-color);
}

.search-modal-header h3 {
    margin: 0;
    font-family: var(--font-sanskrit);
    font-size: 1.2rem;
    color: var(--text-primary);
}

.search-close {
    background: none;
    border: none;
    font-size: 1.8rem;
    cursor: pointer;
    color: var(--text-muted);
    line-height: 1;
    padding: 0 4px;
}

.search-close:hover {
    color: var(--color-accent);
}

.search-input-container {
    padding: 16px 20px 8px;
}

.search-input {
    width: 100%;
    padding: 12px 16px;
    font-size: 1.2rem;
    font-family: var(--font-sanskrit);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background: var(--bg-card);
    color: var(--text-primary);
    outline: none;
}

.search-input:focus {
    border-color: var(--color-accent);
    box-shadow: 0 0 0 2px rgba(255, 107, 53, 0.15);
}

.search-hint {
    display: block;
    font-size: 0.8rem;
    color: var(--text-muted);
    margin-top: 6px;
    padding-left: 4px;
}

.search-results {
    overflow-y: auto;
    padding: 12px;
    flex: 1;
    user-select: text;
    -webkit-user-select: text;
}

.search-result-item {
    padding: 12px 16px;
    margin-bottom: 8px;
    background: var(--bg-card);
    border-left: 3px solid transparent;
    border-radius: 4px;
    transition: all 0.2s ease;
    user-select: text;
    -webkit-user-select: text;
    -moz-user-select: text;
    -ms-user-select: text;
    display: block;
    text-decoration: none;
    cursor: pointer;
}

.search-result-item:hover {
    border-left-color: var(--color-accent);
    background: rgba(255, 107, 53, 0.08);
}

.search-result-item a {
    text-decoration: none;
    color: inherit;
    pointer-events: auto;
}

.search-result-ref {
    font-weight: 600;
    color: var(--color-accent);
    font-size: 0.85rem;
    margin-bottom: 2px;
}

.search-result-ref a {
    color: var(--color-accent);
    text-decoration: none;
}

.search-result-ref a:hover {
    text-decoration: underline;
}

.search-result-meta {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-bottom: 6px;
}

.search-result-text {
    font-family: var(--font-sanskrit);
    font-size: 1.2rem;
    color: var(--text-primary);
    line-height: 1.8;
    word-wrap: break-word;
    overflow-wrap: break-word;
    user-select: text;
    -webkit-user-select: text;
    -moz-user-select: text;
    -ms-user-select: text;
}

.search-result-text mark {
    background-color: #ffeb3b; 
    color: #000;
    padding: 0 2px;
    border-radius: 2px;
    font-weight: 600;
}

.search-result-field {
    margin-bottom: 8px;
    padding: 6px 10px;
    background: rgba(255,255,255,0.5);
    border-radius: 4px;
}

.search-result-field:last-child {
    margin-bottom: 0;
}

.search-result-field-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--color-accent);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 2px;
    display: block;
}

.search-result-text mark {
    background: #ffff00;
    color: #000;
    padding: 0 2px;
    border-radius: 2px;
    font-weight: 500;
}

.search-no-results {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
}

.search-no-results .icon {
    font-size: 2.5rem;
    margin-bottom: 12px;
}

.search-loading {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
}

/* Responsive */
@media (max-width: 1200px) {
    .sidebar-right {
        display: none;
    }
}

@media (max-width: 900px) {
    .sidebar-left {
        position: static;
        width: 100%;
        height: auto;
        border-right: none;
        border-bottom: 1px solid var(--border-color);
    }
    
    .main-content {
        margin-left: 0;
        padding: var(--spacing-lg);
    }
    
    .page-container {
        flex-direction: column;
    }
}

@media (max-width: 600px) {
    .kandah-grid {
        grid-template-columns: 1fr;
    }
    
    .stats-row {
        flex-direction: column;
        gap: var(--spacing-lg);
    }
    
    .metadata-links {
        flex-direction: column;
    }
}

/* Audio Player Styles */
.audio-section {
    margin-top: var(--spacing-lg);
    display: flex;
    justify-content: center;
    width: 100%;
}

.audio-player-container {
    width: 100%;
    max-width: 400px;
    display: flex;
    justify-content: center;
}

.audio-player {
    width: 100%;
}

/* Mantra/Swara Stacking Styles - Matching renderPDF.py output */
.mantra-break {
    flex-basis: 100%;
    height: 1rem;
    width: 100%;
}

.mantra-word {
    display: inline-flex;
    flex-direction: column;
    align-items: stretch;
    vertical-align: top;
    margin: 0;
    padding: 0;
}

.mantra-text {
    font-family: var(--font-sanskrit);
    font-size: 1.6rem;
    line-height: 1.2;
    color: #000000;
}

.swara-text {
    font-family: var(--font-sanskrit);
    color: #c62828;
    font-size: 1.3rem;
    line-height: 1;
    text-align: center;
    margin-top: -0.2em;
    min-height: 1em;
    border-right: 1px solid transparent;
    padding-right: 2px;
}

.swara-left {
    text-align: left;
}

.mantra-verse {
    margin: 5px 0;
    display: inline-flex;
    flex-wrap: wrap;
    align-items: flex-start;
    text-align: center;
    gap: 0;
}

.word-space {
    width: 0.3em;
}

/* Vedic Accent Mark Styles - Zero-width positioning */
.accent-swarita {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    bottom: {sw_off};
    isolation: isolate;
}

.accent-anudatta {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    bottom: {an_off};
    isolation: isolate;
}

.accent-kampa {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    bottom: {ka_off};
}

.accent-trikampa {
    display: inline-block;
    width: 0;
    overflow: visible;
    color: #1565c0;
    font-weight: bold;
    font-size: 1.2em;
    position: relative;
    left: -0.1em;
    bottom: {tr_off};
}

.accent-visarga {
    left: -0.42em !important;
}

.footnote-separator, .closing-separator {
    border: 0;
    border-top: 1px solid var(--border-color);
    margin: var(--spacing-xl) 0;
    width: 200px;
}

.closing-mantras-section {
    margin-top: var(--spacing-2xl);
    padding: var(--spacing-xl);
    text-align: center;
    background-color: #f8fafc; /* Muted Slate-50 background */
    border-radius: 12px;
    border: 1px solid #e2e8f0; /* Muted border */
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
}

.closing-mantras-content {
    font-family: var(--font-sanskrit);
    font-size: 1.25rem;
    color: #475569; /* Muted Slate-600 */
    line-height: 2;
}

.closing-mantra-line {
    margin-bottom: 0.5rem;
}

.footer {

}

.danda {
    margin: 0 0.2em;
}

.mantra-number {
    display: inline-block;
    white-space: nowrap;
    color: var(--primary-maroon);
    font-weight: 500;
    font-size: 1.6rem;
}

/* Footnote Section Styles - matching renderPDF.py */
.footnotes {
    margin-top: var(--spacing-lg);
}

.footnote-separator {
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 20px 0 10px 0;
    width: 40%;
    margin-left: 0;
}

    padding: 10px 0;
    text-align: left;
    font-size: 0.9rem;
    line-height: 1.5;
    font-family: var(--font-sanskrit);
}

.footnote-item {
    padding: 5px 0;
    display: flex;
    align-items: flex-start;
}

.footnote-item .footnote-ref {
    color: #1565c0;
    font-weight: bold;
    margin-right: 0.5em;
    min-width: 1.5em;
    font-family: var(--font-sanskrit);
}

.footnote-item .footnote-text {
    margin-left: 0.5em;
}

/* Inline footnote superscript references - matching renderPDF.py */
sup.footnote-ref {
    font-size: 0.7em;
    vertical-align: super;
    line-height: 0;
    position: relative;
    top: -0.5em;
}

sup.footnote-ref a {
    color: #1565c0;
    text-decoration: none;
    font-weight: bold;
}

sup.footnote-ref a:hover {
    text-decoration: underline;
}

/* Print Styles */
@media print {
    .sidebar-left, .sidebar-right {
        display: none;
    }
    
    .main-content {
        margin: 0;
        max-width: 100%;
    }
}
/* Classification & Index Styles */
.classification-grid {
    display: grid;
    gap: var(--spacing-xl);
    max-width: 800px;
    margin: 0 auto;
}

.class-section {
    background: var(--bg-card);
    padding: var(--spacing-xl);
    border-radius: 8px;
    border: 1px solid var(--border-color);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.class-section h2 {
    color: var(--accent-orange);
    text-align: center;
    margin-bottom: var(--spacing-lg);
    font-size: 1.4rem;
}

.button-row {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-md);
    justify-content: center;
}

.index-btn {
    display: inline-block;
    padding: var(--spacing-md) var(--spacing-lg);
    background: var(--bg-card);
    color: var(--text-primary);
    border-radius: 4px;
    border: 1px solid var(--border-color);
    font-family: var(--font-heading);
    transition: all 0.2s ease;
}

.index-btn:hover {
    border-color: var(--primary-maroon);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    color: var(--text-primary);
    text-decoration: none;
    transform: translateY(-2px);
}

.index-btn:hover {
    border-color: var(--primary-maroon);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    color: var(--text-primary);
    text-decoration: none;
    transform: translateY(-2px);
}

.anya-vargeekaran-card {
    background: transparent;
    padding: 2.5rem 0;
    border-top: 3px solid #C08535;
    border-bottom: 3px solid #C08535;
    max-width: 900px;
    margin: 4rem auto;
    text-align: center;
}

.anya-vargeekaran-card h2 {
    color: var(--color-secondary);
    font-size: 2.2rem;
    margin-bottom: 2rem;
    border-bottom: none;
    padding-bottom: 0;
    text-transform: none;
    font-weight: 700;
}

.index-grid-homepage {
    display: flex;
    justify-content: center;
    flex-wrap: wrap;
    gap: 0.75rem;
    margin-top: 0.5rem;
}

.index-link-item {
    display: inline-flex;
    align-items: center;
    padding: 0.5rem 1.5rem;
    background: #FFFDF8;
    border-radius: 40px;
    border: 1px solid #D8CCB8;
    text-decoration: none;
    transition: all 0.2s ease;
    color: #FF6B35;
    font-family: var(--font-sanskrit);
    font-weight: 600;
    gap: 0.6rem;
}

.index-link-item .title {
    font-size: 1.5rem;
}

.index-link-item .stats {
    font-size: 0.8rem;
    color: #888;
    position: relative;
    top: 3px; /* Align with Devanagari midline */
}

.index-link-item:hover {
    border-color: var(--primary-maroon);
    background: white;
    box-shadow: 0 3px 10px rgba(0,0,0,0.04);
    text-decoration: none;
    transform: translateY(-1px);
}


.index-list {
    max-width: 800px;
    margin: 0 auto;
}

.index-entry {
    margin-bottom: var(--spacing-lg);
    border-bottom: 1px solid var(--border-light);
    padding-bottom: var(--spacing-sm);
}

.index-term {
    font-family: var(--font-heading);
    font-size: 1.2rem;
    color: var(--primary-maroon);
    margin-bottom: var(--spacing-xs);
    font-weight: 600;
}

.index-refs {
    font-size: 0.9rem;
    line-height: 1.6;
}

.index-refs a {
    color: var(--text-link);
    margin-right: 8px;
    display: inline-block;
}

.index-char-header {
    padding-bottom: 4px;
}

/* Classification Table */
.classification-table {
    width: 100%;
    margin-top: 2px;
    margin-bottom: 15px;
    border-collapse: collapse;
    font-size: 1.1rem;
    background: rgba(255, 255, 255, 0.5);
    border-radius: 4px;
    overflow: hidden;
}

.sama-entry .number {
    font-size: 0.9rem;
}

.classification-table th, .classification-table td {
    padding: 6px 10px;
    text-align: left;
    border: 1px solid var(--border-light);
}

.classification-table th {
    background-color: var(--primary-gold);
    color: white;
    font-weight: 500;
}

.class-label {
    color: var(--text-muted);
    font-size: 0.8rem;
    font-family: var(--font-heading);
}

.class-value {
    font-family: var(--font-sanskrit);
    font-size: 1.3rem;
    color: var(--color-secondary);
}

/* Classification Grid Home */
.classification-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-xl);
    margin-top: var(--spacing-2xl);
}

@media (max-width: 900px) {
    .classification-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .classification-grid {
        grid-template-columns: 1fr;
    }
}

.class-card {
    background: white;
    padding: var(--spacing-xl);
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    border: 1px solid var(--border-light);
    text-align: center;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s ease;
}

.class-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    border-color: var(--primary-maroon);
}

.class-card h2 {
    color: var(--primary-maroon);
    font-size: 1.8rem;
    margin-bottom: var(--spacing-md);
}

.class-card .count {
    font-size: 1.1rem;
    color: var(--text-muted);
}

/* Index Summarization */

/* Index Summarization */
.index-section-header {
    font-family: var(--font-heading);
    color: var(--primary-maroon);
    margin: 2rem 0 1rem 0;
    font-size: 1.6rem;
    border-bottom: 2px solid var(--primary-gold);
    padding-bottom: 6px;
}

.top-20-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}

@media (max-width: 1100px) {
    .top-20-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 768px) {
    .top-20-grid {
        grid-template-columns: 1fr;
    }
}

.alphabet-nav {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    background: #f9f9f9;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 2.5rem;
    border: 1px solid var(--border-light);
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);
}

.alpha-btn {
    display: flex;
    align-items: center;
    padding: 0.5rem 1rem;
    background: #eeeeee; /* Match image light gray */
    border: 1px solid transparent;
    border-radius: 6px;
    text-decoration: none;
    color: var(--primary-maroon);
    transition: all 0.2s ease;
    min-width: 4.5rem;
    justify-content: center;
}

.alpha-btn:hover {
    background: white;
    border-color: var(--primary-gold);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}

.alpha-char {
    font-family: var(--font-sanskrit);
    font-weight: 700;
    font-size: 1.2rem;
    margin-right: 8px;
    color: #b03a2e; /* Slightly brighter red for letters */
}

.alpha-count {
    font-size: 0.75rem;
    color: #666;
    font-weight: 500;
    position: relative;
    top: 2px; /* Pull down to align with Devanagari midline */
}

.index-list-container {
    background: #f9f9f9;
    padding: 1.5rem;
    border-radius: 10px;
    margin-top: 1rem;
    border: 1px solid var(--border-light);
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.01);
    overflow: hidden;
}

.index-items-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    width: 100%;
}

/* Maintain equal heights for the Headers Index only on home page */
.header-index-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    grid-auto-rows: 1fr;
    gap: 1rem;
    column-count: auto;
}

@media (max-width: 1100px) {
    .index-items-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    .header-index-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 700px) {
    .index-items-grid {
        grid-template-columns: 1fr;
    }
    .header-index-grid {
        grid-template-columns: minmax(0, 1fr);
    }
}

.index-item-card {
    background: #eeeeee;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 0.6rem 1rem;
    display: flex;
    flex-direction: column;
    justify-content: center;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
    box-sizing: border-box;
}

/* New compact list entry for Rishi/Devata/Chandas indices */
.index-list-item {
    padding: 0.4rem 0.5rem;
    background: transparent;
    border-bottom: 1px solid #eee;
    display: block;
    width: 100%;
    box-sizing: border-box;
}

.index-list-item:hover {
    background: #fdfdfd;
    color: var(--color-primary);
}

.index-item-card:hover {
    background: white;
    border-color: var(--primary-gold);
    box-shadow: 0 6px 15px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}

/* Compact version for Headers Index */
.simple-card {
    padding: 0.6rem 1rem;
    min-height: 48px;
}

.simple-card .item-main {
    align-items: center;
    overflow: hidden;
    min-width: 0;
    width: 100%;
    gap: 0.75rem;
}

.simple-card .item-name {
    font-size: 1.05rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
    min-width: 0;
}

.simple-card .item-count-badge {
    padding: 1px 8px;
    font-size: 0.75rem;
}

.item-main {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.75rem;
    width: 100%;
    min-width: 0;
}

.item-name {
    font-family: var(--font-sanskrit);
    font-size: 1.3rem;
    color: var(--text-primary);
    font-weight: 600;
    line-height: 1.3;
}

.item-count-badge {
    background: transparent;
    color: #777;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 0.75rem;
    font-weight: 600;
    flex-shrink: 0;
}

.item-refs {
    margin-top: 0.2rem;
    display: block;
    line-height: 1.8;
}

/* Custom scrollbar for compact view */
.item-refs::-webkit-scrollbar {
    width: 3px;
}
.item-refs::-webkit-scrollbar-thumb {
    background: #ccc;
    border-radius: 10px;
}

.item-refs a {
    font-size: 0.8rem;
    color: var(--text-link);
    text-decoration: none;
    margin-right: 0.5rem;
    display: inline-block;
}

.item-count {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 500;
}

.item-refs a::after {
    content: ',';
    color: #999;
}

.item-refs a:last-child::after {
    content: '';
}

.item-refs a:hover {
    text-decoration: underline;
    color: var(--primary-maroon);
}

.index-char-group {
    margin-bottom: 2rem;
    scroll-margin-top: 2rem;
}

.index-char-title {
    font-size: 1.8rem;
    color: var(--primary-maroon);
    font-family: var(--font-sanskrit);
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}

.index-char-title::after {
    content: '';
    flex-grow: 1;
    height: 3px;
    background: var(--primary-gold);
    border-radius: 2px;
}

.rishi-card {
    display: flex;
    align-items: center;
    background: white;
    padding: 0.5rem 0.8rem;
    border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    border: 1px solid var(--border-light);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    text-decoration: none;
    color: inherit;
    min-height: 54px;
}

.rishi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    border-color: var(--primary-maroon);
}

.rest-card {
    background: #f8f8f8;
    border: 2px dashed var(--border-light);
    justify-content: center;
    background-image: linear-gradient(135deg, rgba(0,0,0,0.02) 25%, transparent 25%, transparent 50%, rgba(0,0,0,0.02) 50%, rgba(0,0,0,0.02) 75%, transparent 75%, transparent);
    background-size: 20px 20px;
}

.rest-card .rishi-rank {
    background: var(--text-muted);
}

.rest-card .rishi-name {
    color: var(--text-secondary);
    font-style: italic;
}

.rest-card:hover {
    background-color: #f1f1f1;
    border-color: var(--primary-gold);
}

.rishi-rank {
    background: var(--primary-maroon);
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 500; /* Medium instead of bold */
    font-size: 0.85rem;
    margin-right: 0.8rem;
    flex-shrink: 0;
}

.rishi-info {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    overflow: hidden;
}

.rishi-name {
    font-family: var(--font-sanskrit);
    font-weight: 400; /* Regular instead of semi-bold */
    font-size: 1.15rem;
    display: block;
    line-height: 1.2;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.rishi-count {
    color: var(--text-secondary);
    font-size: 0.8rem;
    text-align: right;
    font-weight: 400; /* Regular instead of semi-bold */
    margin-left: 1rem;
    white-space: nowrap;
}


.count-tag {
    font-size: 0.8rem;
    color: var(--text-muted);
    font-weight: 400;
    margin-left: 8px;
}


.index-char-group {
    break-inside: avoid-column;
    margin-bottom: 2rem;
}
"""

    if is_malayalam:
        font_doc = "'Noto Serif Malayalam', 'Noto Sans Malayalam', 'Gayathri', serif, sans-serif"
        swara_size_val = "calc(var(--font-size) * 0.78)"
    else:
        font_doc = f"'{font}', '{font_sans}', 'Noto Serif Devanagari', 'Tiro Devanagari Sanskrit', serif"
        swara_size_val = "var(--font-size)"

    css = css.replace('{self.font}', font)
    css = css.replace('{self.font_sans}', font_sans)
    css = css.replace('{font_doc}', font_doc)
    css = css.replace('{swara_size_val}', swara_size_val)
    css = css.replace('{sw_off}', sw_off)
    css = css.replace('{ka_off}', ka_off)
    css = css.replace('{tr_off}', tr_off)
    css = css.replace('{an_off}', an_off)

    font_face = """
@font-face {
    font-family: 'JaimineeyaSwara';
    src: url('../fonts/JaimineeyaSwara.ttf') format('truetype'),
         url('fonts/JaimineeyaSwara.ttf') format('truetype');
    font-weight: normal;
    font-style: normal;
}
"""

    swara_mod_css = """
/* Swara Modifiers - Standalone HTML Viewer Alignment */
.swara-mod {
    font-family: var(--font-swara), var(--font-doc);
    color: var(--modifier-color, #0284c7);
    font-weight: 800;
    -webkit-text-stroke: 0.025em currentColor;
    line-height: 1;
    display: inline-block;
    vertical-align: baseline;
}

.swara-mod.mod-a {
    position: absolute;
    top: -0.32em;
    left: 100%;
    transform: translateX(-40%);
    font-size: 0.60em;
    pointer-events: none;
    z-index: 2;
}

.danda-word-a1,
.mantra-word:has(.danda-with-arc),
.danda.danda-with-arc:not(.danda-word-a1 *) {
    margin-left: 0;
    margin-right: 0;
}
.danda-with-arc,
.danda.danda-with-arc {
    position: relative;
    display: inline-flex !important;
    align-items: flex-end !important;
    vertical-align: bottom !important;
}
.danda-with-arc .swara-mod.mod-a1,
.danda.danda-with-arc .swara-mod.mod-a1,
.swara-mod.mod-a1 {
    position: absolute;
    top: -0.22em;
    left: 62%;
    transform: translateX(-50%);
    font-size: 1.0em;
    pointer-events: none;
    z-index: 2;
}

.swara-mod.mod-a2 {
    position: absolute;
    top: -0.32em;
    left: 50%;
    transform: translateX(-50%);
    font-size: 0.60em;
    pointer-events: none;
    z-index: 2;
}
.swara-mod.mod-b {
    position: absolute;
    top: -0.28em;
    left: 100%;
    transform: translateX(-45%);
    font-size: 0.50em;
    pointer-events: none;
    z-index: 2;
}
.swara-mod.mod-b .caret-glyph {
    display: block;
    color: var(--modifier-color, #0284c7);
    font-size: 0.95rem;
    line-height: 1;
}
.swara-mod.mod-b .swara-on-caret {
    position: absolute;
    top: -1.70em;
    left: 50%;
    transform: translateX(-50%);
    color: var(--swara-red, #c62828) !important;
    font-size: 0.70rem;
    font-weight: bold;
    font-family: var(--font-swara);
    line-height: 1;
    white-space: nowrap;
}
.swara-mod.mod-b1 {
    position: absolute;
    top: -0.35em;
    left: 100%;
    transform: translateX(-20%);
    font-size: 0.95rem;
    pointer-events: none;
}
.swara-mod.mod-c {
    position: absolute;
    top: -0.20em;
    left: 100%;
    transform: translateX(-0.20em);
    font-size: 0.90em;
    font-weight: 800;
    -webkit-text-stroke: 0.03em currentColor;
    pointer-events: none;
    z-index: 2;
}
.swara-mod.mod-d {
    position: absolute;
    top: -0.32em;
    left: 100%;
    transform: translateX(-45%);
    font-size: 0.90em;
    font-weight: 800;
    -webkit-text-stroke: 0.04em currentColor;
    pointer-events: none;
    z-index: 2;
}
.swara-mod.mod-d1 {
    position: absolute;
    top: -0.26em;
    left: 100%;
    transform: translateX(-35%);
    font-size: 1.10em;
    font-weight: 800;
    -webkit-text-stroke: 0.04em currentColor;
    pointer-events: none;
    z-index: 2;
}
.swara-mod.mod-d2 {
    font-size: 0.48em;
    margin-left: 1px;
    vertical-align: 0.35em;
}
.swara-mod.mod-e {
    font-family: var(--font-swara) !important;
    font-size: 0.65em;
    font-weight: 900 !important;
    -webkit-text-stroke: 0.05em currentColor !important;
    text-shadow: 0.02em 0 currentColor;
    display: inline-block;
    vertical-align: 0.05em;
    margin-left: 2px;
}
.swara-mod.mod-f {
    font-size: 0.95em;
    font-weight: 900 !important;
    -webkit-text-stroke: 0.055em currentColor;
    text-shadow: 0.02em 0 currentColor, -0.02em 0 currentColor;
    margin-left: 2px;
    vertical-align: 0.12em;
    display: inline-block;
}
.syl-mod-g-wrap {
    position: relative;
    display: inline-flex;
    align-items: flex-end;
}
.swara-mod.mod-g,
.syl-mod-g-wrap .swara-mod.mod-g {
    position: absolute;
    bottom: 0.1em;
    left: 50%;
    transform: translateX(-50%) translateX(0.75em);
    font-size: 0.85em;
    font-weight: 800;
    -webkit-text-stroke: 0.04em currentColor;
    pointer-events: none;
}
.swara-mod.mod-h {
    position: absolute;
    top: -0.28em;
    left: 100%;
    transform: translateX(-0.35em);
    font-size: 0.90em;
    font-weight: 800;
    -webkit-text-stroke: 0.04em currentColor;
    pointer-events: none;
}
.swara-mod.mod-i {
    font-family: var(--font-swara);
    font-size: 1.45rem;
    font-weight: bold;
    color: var(--modifier-color, #0284c7);
    position: absolute;
    top: -0.25em;
    right: -0.25em;
    line-height: 1;
    pointer-events: none;
}
.swara-mod.mod-j {
    font-family: var(--font-swara);
    font-size: 1.45rem;
    font-weight: bold;
    color: var(--modifier-color, #0284c7);
    position: absolute;
    top: -0.28em;
    right: -0.20em;
    line-height: 1;
    pointer-events: none;
}
.swara-mod.mod-k {
    font-family: var(--font-swara);
    font-size: 1.45rem;
    font-weight: bold;
    color: var(--modifier-color, #0284c7);
    position: absolute;
    top: -0.25em;
    right: -0.50em;
    line-height: 1;
    pointer-events: none;
}
.swara-mod.mod-under,
.swara-mod.mod-underbar {
    font-family: var(--font-doc);
    font-size: 1.1em;
    color: var(--modifier-color, #0284c7);
    display: inline;
    margin-left: -0.04em;
    margin-right: 0.02em;
    font-weight: 900;
    -webkit-text-stroke: 0.04em currentColor;
    position: relative;
    bottom: 0.12em;
    line-height: 1;
}
.swara-mod.mod-dot,
.swara-mod.mod-comma {
    font-family: 'Noto Serif Malayalam', 'Noto Serif Devanagari', var(--font-doc);
    color: var(--modifier-color, #0284c7);
    display: inline-block;
    margin: 0;
    font-size: 1.25em;
    font-weight: 500;
    vertical-align: baseline;
}
.mantra-connected-group {
    display: inline-flex;
    flex-wrap: nowrap;
    align-items: flex-end;
    white-space: nowrap;
    margin: 0;
    padding: 0;
}
.mantra-connected-group .danda {
    margin: 0;
}
.danda.danda-adjacent {
    margin-left: -0.28em !important;
    margin-right: 2px !important;
}
.mantra-punct {
    font-family: 'Noto Serif Malayalam', 'Noto Serif Devanagari', serif !important;
    font-size: 1.45rem;
    line-height: 1.2;
    color: var(--modifier-color, #0284c7);
    margin-right: 0.05em;
}
"""
    malayalam_css = """
/* Malayalam Swara & Modifier Typography - Standalone Viewer Parity */
.mantra-verse {
    margin: 6px 0;
    display: inline-flex;
    flex-wrap: wrap;
    align-items: flex-end !important;
    justify-content: center;
    text-align: center;
    gap: 0;
    width: 100%;
}
.mantra-connected-group {
    display: inline-flex;
    flex-wrap: nowrap;
    align-items: flex-end !important;
    white-space: nowrap;
    margin: 0;
    padding: 0;
}
.mantra-word {
    display: inline-flex !important;
    flex-direction: row !important;
    align-items: flex-end !important;
    vertical-align: bottom !important;
    margin: 0;
    padding: 0;
    position: relative;
}
.swara-text {
    font-family: var(--font-swara, 'JaimineeyaSwara'), serif !important;
    color: var(--swara-red, #c62828) !important;
    font-weight: bold;
    font-size: var(--swara-size, 1.05rem) !important;
    line-height: 1;
    text-align: center;
    margin-bottom: 4px;
    min-height: 1.1em;
    user-select: none;
}
.mantra-text {
    font-family: var(--font-doc, 'Noto Serif Malayalam'), serif !important;
    font-size: var(--mantra-size, 1.45rem);
    line-height: 1.25;
    color: #000000;
    position: relative;
}
/* Ruby Stacking for Malayalam Vedic Swaras */
ruby.vedic-ruby {
    ruby-position: over;
    ruby-align: center;
    display: inline-flex !important;
    flex-direction: column-reverse !important;
    align-items: center !important;
    vertical-align: bottom !important;
    margin: 0;
    padding: 0;
    position: relative;
}
rt.swara-above {
    font-family: var(--font-swara, 'JaimineeyaSwara') !important;
    font-size: var(--swara-size, 1.05rem) !important;
    color: var(--swara-red, #c62828) !important;
    font-weight: 700;
    line-height: 1;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    margin-bottom: 4px;
    user-select: text;
    white-space: nowrap;
}
rb.akshara-base,
.akshara-base {
    font-family: var(--font-doc, 'Noto Serif Malayalam');
    font-size: var(--mantra-size, 1.45rem);
    color: var(--primary-color, #000);
    display: inline-flex;
    align-items: flex-end;
    justify-content: center;
    line-height: 1.25;
    text-align: center;
    position: relative;
}
.word-space {
    display: inline-block;
    width: 0.35em;
}
.danda {
    font-family: var(--font-doc);
    font-size: var(--mantra-size, 1.45rem);
    line-height: 1.25;
    margin: 0 0.08em;
    vertical-align: bottom !important;
    display: inline-flex !important;
    align-items: flex-end !important;
    position: relative;
}
.verse-num-marker {
    display: inline-flex;
    align-items: center;
    margin-left: 0.45em;
    white-space: nowrap;
    font-family: var(--font-doc);
    font-size: var(--mantra-size, 1.45rem);
    line-height: 1.25;
    vertical-align: baseline;
}
.verse-num-marker .danda {
    margin: 0;
    vertical-align: baseline !important;
    display: inline !important;
}
.verse-num {
    font-family: var(--font-doc);
    font-size: var(--mantra-size, 1.45rem);
    font-weight: bold;
    color: var(--primary-color, #000);
    padding: 0 0.12em;
    line-height: 1.25;
    vertical-align: baseline;
    display: inline;
}

/* Rachana Typography Calibration: matches visual scale and weight of Noto Sans Malayalam */
body.font-rachana .akshara-base,
body.font-rachana rb.akshara-base {
    font-size: calc(var(--mantra-size) * 1.25);
    font-weight: 100;
    -webkit-text-stroke: 0.0em currentColor;
}
body.font-rachana .danda,
body.font-rachana .verse-num-marker,
body.font-rachana .verse-num,
body.font-rachana .mantra-punct {
    font-size: calc(var(--mantra-size) * 1.15);
    font-weight: 500;
}
body.font-rachana .rik-text,
body.font-rachana .samam-text {
    font-size: calc(var(--mantra-size) * 1.15);
}
body.font-rachana rt.swara-above {
    font-size: calc(var(--swara-size) * 0.85);
    font-weight: 600;
    margin-bottom: 2px;
}
body.font-rachana .swara-mod {
    font-size: 0.90em;
}
body.font-rachana .swara-mod.mod-c {
    font-size: 0.75em !important;
    -webkit-text-stroke: 0 !important;
    font-weight: 600 !important;
    top: -0.3em !important;
    right: 0.2em;
}
body.font-rachana .swara-mod.mod-h {
    font-size: 0.75em !important;
    -webkit-text-stroke: 0 !important;
    font-weight: 700 !important;
    top: -0.18em !important;
}
body.font-rachana .swara-mod.mod-e {
    font-size: 0.60em !important;
    font-weight: 900 !important;
    -webkit-text-stroke: 0.05em currentColor !important;
    text-shadow: 0.02em 0 currentColor !important;
    position: relative !important;
    top: -0.30em !important;
    vertical-align: 0.05em !important;
    margin-left: 2px !important;
}
body.font-rachana .swara-mod.mod-comma {
    font-size: 1.0em !important;
    position: relative !important;
    display: inline-block !important;
    transform: translateY(-0.2em) translateX(0.05em) !important;
}
body.font-rachana .swara-mod.mod-dot {
    font-size: 1.0em !important;
    position: relative !important;
    top: -0.15em !important;
    left: 0.0em !important;
}
"""
    kpully_deva_css = """
/* KPULLY Mode (Kodunthirapully Paddhati) for Devanagari: Swara text rendered ABOVE mantra text */
.mantra-verse {
    align-items: flex-end !important;
}
.mantra-word {
    flex-direction: column-reverse !important;
    justify-content: flex-start !important;
    vertical-align: bottom !important;
}
.mantra-connected-group {
    align-items: flex-end !important;
}
.swara-text {
    margin-top: 0 !important;
    margin-bottom: 2px !important;
}
.mantra-verse > sup.footnote-ref {
    align-self: flex-end !important;
    margin-bottom: 0.2em !important;
}
"""

    if is_malayalam:
        css = font_face + css + swara_mod_css + malayalam_css
    elif kpully:
        css = font_face + css + swara_mod_css + kpully_deva_css
    else:
        css = font_face + css + swara_mod_css

    return css
