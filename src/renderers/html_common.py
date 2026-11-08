"""
Common HTML Reader Components & Functions.
------------------------------------------
Shared across all Vedic and Samaveda HTML reader generators (JSV Devanagari,
JSV Malayalam, Gramageyaganam G1/G2, and standalone viewers).

Provides:
- Atomic chanting pada segmentation (wrap_chant_padas)
- Inline note button generator (render_inline_note_btn)
- Section header bookmark button generator (render_section_bm_btn)
- Complete CSS stylesheets for Post-It stationery, tabs, drawer, and pada layouts
- Complete HTML markup for Bookmarks drawer and overlay layers
- Complete client-side JavaScript engine for notes, drag-and-drop, persistence,
  hover cards, and pada-per-line chanting toggle
"""

import html
import re
from typing import Optional


# Regex matching sentences ending with dandas (| or ||), handling both raw characters
# and HTML-wrapped danda spans (<span class="danda">...</span>).
PADA_SPLIT_PATTERN = None


def wrap_chant_padas(html_text: str) -> str:
    """Pass-through for chant lines (single pada view is disabled; natural left-to-right flow)."""
    return html_text


def insert_pada_flex_breaks(html_text: str) -> str:
    """Pass-through for flexbox verses (single pada view is disabled; natural left-to-right flow)."""
    return html_text

def render_inline_note_btn(target_id: str, snippet: str = "") -> str:
    """Renders the inline '📌+' button appended to verse lines."""
    if not target_id:
        return ""
    safe_id = html.escape(target_id, quote=True)
    # Clean and escape snippet for JS onclick string parameter
    clean_snip = snippet.replace("'", "\\'").replace('"', '&quot;').replace('\n', ' ')
    return (
        f'<button type="button" class="add-note-inline-btn" '
        f'onclick="createNoteAtTarget(\'{safe_id}\', \'{clean_snip}\', event)" '
        f'title="Add Post-It Note">📌+</button>'
    )


def render_section_bm_btn(section_id: str, label: str = "Note") -> str:
    """Renders the section-level bookmark button."""
    if not section_id:
        return ""
    safe_id = html.escape(section_id, quote=True)
    safe_label = html.escape(label)
    return (
        f'<button type="button" class="anuvaka-bm-btn" '
        f'onclick="toggleAnuvakaBookmark(\'{safe_id}\', event)" '
        f'title="Add Post-It / Note to this section">🔖 <span class="bm-btn-label">{safe_label}</span></button>'
    )


def get_viewer_toolbar_controls_html() -> str:
    """Returns HTML for top navigation bar action buttons: ➕ Note, 🔖 Notes."""
    return (
        '<button class="btn-ctrl" id="btn-add-quick-note" onclick="createFloatingNote()" '
        'title="Create a new Post-It Note (or double-click anywhere in text)">➕ Note</button>\n'
        '<button class="btn-ctrl" id="bookmarks-toggle-btn" onclick="toggleBookmarksDrawer()" '
        'title="View Bookmarks & Post-It Notes">🔖 Notes <span id="bm-badge-count" class="bm-badge" style="display:none;">0</span></button>'
    )


def get_viewer_notes_html() -> str:
    """Returns HTML markup for the Post-It layer, drawer backdrop, and Bookmarks slide-out drawer."""
    return """
    <!-- Autonomous Post-It Layer & Bookmarks Slide-out Drawer -->
    <div id="postit-overlay-layer"></div>
    <div class="bm-drawer-backdrop" id="bm-drawer-backdrop" onclick="toggleBookmarksDrawer(false)"></div>
    <div class="bookmarks-drawer" id="bookmarks-drawer">
        <div class="bm-drawer-header">
            <div class="bm-drawer-title">
                <span>🔖 Bookmarks & Notes</span>
                <span class="bm-drawer-count" id="bm-drawer-count">0</span>
            </div>
            <div class="bm-drawer-actions">
                <button type="button" class="btn-clear-all-bm" onclick="clearAllBookmarks()" title="Clear all bookmarks and notes">Clear All</button>
                <button type="button" class="bm-drawer-close" onclick="toggleBookmarksDrawer(false)" title="Close Drawer">✕</button>
            </div>
        </div>
        <div class="bm-drawer-list" id="bm-drawer-list"></div>
    </div>
    """


def get_viewer_notes_css() -> str:
    """Returns complete CSS styles for Post-It notes, tabs, hover cards, drawer, badges, and pada layouts."""
    return """
        /* --- Post-It Stationery & Bookmarks Entity System --- */
        .bm-badge {
            background: #FFD54F;
            color: #5C2C00;
            font-size: 0.72rem;
            font-weight: 700;
            border-radius: 10px;
            padding: 0.1rem 0.45rem;
            margin-left: 0.35rem;
            vertical-align: middle;
            display: inline-block;
            line-height: 1.2;
        }

        .section-title-wrap {
            position: relative;
            width: 100%;
            margin-bottom: 1.25rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px dashed #E0D0C0;
            display: flex;
            justify-content: center;
            align-items: center;
            box-sizing: border-box;
        }
        .section-title-wrap .section-title {
            margin: 0;
            padding: 0;
            border-bottom: none !important;
            text-align: center;
        }
        .section-title-wrap .anuvaka-bm-btn {
            position: absolute;
            right: calc(1.6rem + 1px);
            top: 50%;
            transform: translateY(-50%);
        }
        .subsection-header {
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
        }
        .subsection-header .anuvaka-bm-btn {
            position: absolute;
            right: 0;
            top: 50%;
            transform: translateY(-50%);
        }
        .rik-metadata {
            text-align: center;
        }
        .rik-text {
            text-align: center;
        }
        @media (max-width: 600px) {
            .section-title-wrap, .subsection-header {
                flex-direction: column;
                gap: 0.4rem;
            }
            .section-title-wrap .anuvaka-bm-btn,
            .subsection-header .anuvaka-bm-btn {
                position: static;
                transform: none;
                right: auto;
            }
        }

        .anuvaka-bm-btn {
            background: #FAF5EE;
            border: 1px solid #D7C4B2;
            color: #795548;
            border-radius: 6px;
            padding: 0.22rem 0.55rem;
            font-size: 0.78rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            flex-shrink: 0;
            user-select: none;
        }
        .anuvaka-bm-btn:hover {
            background: #FFF3E0;
            border-color: #D84315;
            color: #D84315;
            transform: translateY(-1px);
        }
        .anuvaka-bm-btn.active {
            background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
            border-color: #FBC02D;
            color: #7F5000;
            box-shadow: 0 1px 4px rgba(251, 192, 45, 0.35);
            font-weight: 700;
        }

        #postit-overlay-layer {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 1200;
        }

        .postit-entity {
            position: absolute;
            z-index: 2100;
            width: 240px;
            min-height: 210px;
            max-height: 320px;
            padding: 0.7rem 0.85rem 0.65rem;
            border-radius: 5px;
            box-shadow: 2px 6px 20px rgba(0, 0, 0, 0.18), 0 1px 4px rgba(0, 0, 0, 0.1);
            pointer-events: auto;
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            border: 1px solid rgba(0, 0, 0, 0.14);
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            transform: rotate(-0.5deg);
            transition: box-shadow 0.2s ease;
            animation: postitPop 0.18s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .postit-entity:focus-within {
            z-index: 2250 !important;
            box-shadow: 3px 10px 28px rgba(0, 0, 0, 0.24);
        }

        @keyframes postitPop {
            from {
                opacity: 0;
                transform: scale(0.9) rotate(-1.5deg);
            }
            to {
                opacity: 1;
                transform: scale(1) rotate(-0.5deg);
            }
        }

        .postit-entity.dragging {
            transform: scale(1.03) rotate(0deg) !important;
            box-shadow: 5px 14px 32px rgba(0, 0, 0, 0.28) !important;
            cursor: grabbing !important;
            user-select: none;
            z-index: 2300 !important;
        }

        .postit-entity:hover {
            box-shadow: 3px 9px 24px rgba(0, 0, 0, 0.22);
        }

        /* Post-It Themes */
        .postit-theme-yellow { background: #FEF9C3; border-color: #FDE047; color: #713F12; }
        .postit-theme-saffron { background: #FFEDD5; border-color: #FDBA74; color: #7C2D12; }
        .postit-theme-green { background: #DCFCE7; border-color: #86EFAC; color: #14532D; }
        .postit-theme-rose { background: #FFE4E6; border-color: #FDA4AF; color: #881337; }

        /* In-Place Collapsed Sticky Tab Flag */
        .postit-inplace-tab {
            position: absolute;
            z-index: 1190;
            pointer-events: auto;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.22rem 0.65rem 0.22rem 0.5rem;
            border-radius: 4px 12px 12px 4px;
            font-size: 0.78rem;
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 1px 3px 10px rgba(0, 0, 0, 0.16), 0 1px 3px rgba(0,0,0,0.1);
            transform: rotate(-1deg);
            transition: transform 0.18s ease, box-shadow 0.18s ease;
            user-select: none;
            border: 1px solid rgba(0,0,0,0.18);
            border-left: 4px solid #EAB308;
            white-space: nowrap;
            max-width: 220px;
            overflow: hidden;
            text-overflow: ellipsis;
            animation: postitPop 0.15s ease;
        }
        .postit-inplace-tab:hover {
            transform: scale(1.08) rotate(0deg);
            box-shadow: 2px 6px 16px rgba(0, 0, 0, 0.24);
            z-index: 1250;
        }
        .postit-inplace-tab.postit-theme-yellow { border-left-color: #EAB308; }
        .postit-inplace-tab.postit-theme-saffron { border-left-color: #F97316; }
        .postit-inplace-tab.postit-theme-green { border-left-color: #22C55E; }
        .postit-inplace-tab.postit-theme-rose { border-left-color: #F43F5E; }
        .postit-inplace-tab.dragging {
            opacity: 0.85;
            transform: scale(1.1) rotate(0deg) !important;
            cursor: grabbing !important;
            z-index: 2200 !important;
        }
        .inplace-tab-pin {
            font-size: 0.85rem;
            filter: drop-shadow(1px 1px 1px rgba(0,0,0,0.25));
            flex-shrink: 0;
        }
        .inplace-tab-title {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .postit-entity-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px dashed rgba(0, 0, 0, 0.15);
            padding-bottom: 0.35rem;
            margin-bottom: 0.45rem;
            gap: 0.4rem;
            cursor: grab;
            user-select: none;
        }
        .postit-entity-header:active {
            cursor: grabbing;
        }

        .postit-drag-handle {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            overflow: hidden;
            flex: 1;
            min-width: 0;
        }

        .postit-pin {
            font-size: 1rem;
            filter: drop-shadow(1px 2px 1px rgba(0,0,0,0.25));
            flex-shrink: 0;
        }

        .postit-entity-title {
            font-size: 0.78rem;
            font-weight: 700;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            letter-spacing: 0.02em;
        }

        .postit-entity-tools {
            display: flex;
            align-items: center;
            gap: 0.25rem;
            flex-shrink: 0;
            cursor: default;
        }

        .postit-color-picker {
            display: flex;
            gap: 0.2rem;
            margin-right: 0.25rem;
        }

        .color-btn {
            width: 13px;
            height: 13px;
            border-radius: 50%;
            border: 1px solid rgba(0,0,0,0.25);
            cursor: pointer;
            padding: 0;
            transition: transform 0.15s ease;
        }
        .color-btn:hover, .color-btn.active {
            transform: scale(1.35);
            box-shadow: 0 0 0 1.5px #333;
        }
        .color-yellow { background: #FDE047; }
        .color-saffron { background: #FB923C; }
        .color-green { background: #4ADE80; }
        .color-rose { background: #FB7185; }

        .postit-tool-btn {
            background: transparent;
            border: none;
            cursor: pointer;
            font-size: 0.88rem;
            color: inherit;
            opacity: 0.65;
            padding: 0.1rem 0.28rem;
            border-radius: 3px;
            line-height: 1;
            transition: all 0.15s ease;
        }
        .postit-tool-btn:hover {
            opacity: 1;
            background: rgba(0,0,0,0.08);
        }
        .postit-tool-del:hover {
            color: #DC2626;
            background: rgba(220, 38, 38, 0.15);
        }
        .postit-tool-close {
            font-weight: 700;
        }

        .postit-entity-body {
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
        }

        .postit-textarea {
            width: 100%;
            flex: 1;
            min-height: 110px;
            border: none;
            background: transparent;
            resize: none;
            font-family: inherit;
            font-size: 0.88rem;
            line-height: 1.45;
            color: inherit;
            outline: none;
            box-sizing: border-box;
            padding: 0;
        }
        .postit-textarea::placeholder {
            color: inherit;
            opacity: 0.55;
            font-style: italic;
        }

        .postit-footer-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 0.35rem;
            padding-top: 0.25rem;
            border-top: 1px dotted rgba(0, 0, 0, 0.15);
            font-size: 0.7rem;
            gap: 0.4rem;
        }

        .postit-status {
            opacity: 0.7;
        }

        .postit-done-btn {
            background: rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.15);
            color: inherit;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.18rem 0.55rem;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s ease;
            line-height: 1.2;
        }
        .postit-done-btn:hover {
            background: rgba(0, 0, 0, 0.16);
            transform: translateY(-1px);
        }

        /* Verse line inline add button and pin markers */
        .verse-p {
            position: relative;
            line-height: 2.2;
            word-break: keep-all;
        }

        /* Continuous natural left-to-right flow (no forced pada breaks) */

        .add-note-inline-btn {
            background: transparent;
            border: none;
            color: #C07040;
            font-size: 0.78rem;
            cursor: pointer;
            opacity: 0;
            margin-left: 0.5rem;
            vertical-align: middle;
            transition: all 0.2s ease;
            padding: 0.1rem 0.3rem;
            border-radius: 4px;
            line-height: 1;
            user-select: none;
        }
        .verse-p:hover .add-note-inline-btn, .mantra-verse:hover .add-note-inline-btn {
            opacity: 0.75;
            background: rgba(216, 67, 21, 0.08);
        }
        .add-note-inline-btn:hover {
            opacity: 1 !important;
            background: #D84315 !important;
            color: white !important;
            transform: scale(1.15);
        }

        /* Hover Preview Card for Notes */
        .postit-hover-card {
            position: absolute;
            z-index: 1500;
            width: 220px;
            max-width: 85vw;
            padding: 0.65rem 0.8rem;
            border-radius: 6px;
            box-shadow: 2px 8px 24px rgba(0, 0, 0, 0.25), 0 2px 6px rgba(0, 0, 0, 0.12);
            pointer-events: none;
            font-family: system-ui, -apple-system, sans-serif;
            font-size: 0.82rem;
            line-height: 1.45;
            transform: translateY(-4px) rotate(-0.5deg);
            transition: opacity 0.12s ease, transform 0.12s ease;
            opacity: 0;
            display: none;
            border: 1px solid rgba(0, 0, 0, 0.18);
        }
        .postit-hover-card.visible {
            opacity: 1;
            display: block;
            transform: translateY(0) rotate(-0.5deg);
        }
        .hover-card-header {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            font-weight: 700;
            font-size: 0.76rem;
            border-bottom: 1px dashed rgba(0,0,0,0.18);
            padding-bottom: 0.25rem;
            margin-bottom: 0.35rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .hover-card-content {
            word-break: break-word;
            white-space: pre-wrap;
            max-height: 160px;
            overflow: hidden;
        }

        /* Floating Selection Note Button */
        .selection-note-btn {
            position: absolute;
            z-index: 1300;
            background: #7B1113;
            color: white;
            border: 1px solid #8B5A2B;
            border-radius: 16px;
            padding: 0.32rem 0.75rem;
            font-size: 0.78rem;
            font-weight: 700;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
            display: none;
            align-items: center;
            gap: 0.3rem;
            animation: postitPop 0.15s ease;
            white-space: nowrap;
        }
        .selection-note-btn:hover {
            background: #D84315;
            transform: scale(1.05);
        }

        /* Bookmarks Slide-out Drawer */
        .bm-drawer-backdrop {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.45);
            backdrop-filter: blur(2px);
            z-index: 10000;
            opacity: 0;
            transition: opacity 0.25s ease;
        }
        .bm-drawer-backdrop.active {
            display: block;
            opacity: 1;
        }

        .bookmarks-drawer {
            position: fixed;
            top: 0;
            right: 0;
            width: min(90vw, 380px);
            height: 100vh;
            background: #FFFDF9;
            box-shadow: -4px 0 24px rgba(0,0,0,0.22);
            z-index: 10001;
            transform: translateX(105%);
            transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            flex-direction: column;
            border-left: 2px solid #EADDC9;
        }
        .bookmarks-drawer.active {
            transform: translateX(0);
        }

        .bm-drawer-header {
            background: linear-gradient(135deg, #153E75 0%, #1D5296 100%);
            color: white;
            padding: 1.1rem 1.25rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #8B5A2B;
        }
        .bm-drawer-title {
            font-weight: 700;
            font-size: 1.05rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .bm-drawer-count {
            background: #FFD54F;
            color: #3E1B00;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.12rem 0.5rem;
            border-radius: 12px;
        }
        .bm-drawer-actions {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .btn-clear-all-bm {
            background: rgba(255,255,255,0.18);
            border: 1px solid rgba(255,255,255,0.3);
            color: white;
            border-radius: 4px;
            font-size: 0.72rem;
            padding: 0.25rem 0.5rem;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-clear-all-bm:hover {
            background: rgba(220, 38, 38, 0.85);
            border-color: #EF4444;
        }
        .bm-drawer-close {
            background: transparent;
            border: none;
            color: white;
            font-size: 1.2rem;
            cursor: pointer;
            padding: 0.2rem 0.4rem;
            line-height: 1;
            opacity: 0.85;
            transition: opacity 0.2s;
        }
        .bm-drawer-close:hover {
            opacity: 1;
        }

        .bm-drawer-list {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .bm-card {
            background: #FFFFFF;
            border-radius: 8px;
            border: 1px solid #EADDC9;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
            padding: 0.85rem;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            border-left: 5px solid #FDE047;
        }
        .bm-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.12);
        }
        .bm-card.card-theme-yellow { border-left-color: #FDE047; }
        .bm-card.card-theme-saffron { border-left-color: #FB923C; }
        .bm-card.card-theme-green { border-left-color: #4ADE80; }
        .bm-card.card-theme-rose { border-left-color: #FB7185; }

        .bm-card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.35rem;
        }
        .bm-card-ch {
            font-size: 0.76rem;
            font-weight: 700;
            color: #D84315;
            text-transform: uppercase;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            flex: 1;
        }
        .bm-card-actions {
            display: flex;
            align-items: center;
            gap: 0.35rem;
            flex-shrink: 0;
        }
        .bm-card-action-btn {
            background: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.12);
            border-radius: 4px;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.15rem 0.45rem;
            cursor: pointer;
            color: #5D4037;
            transition: all 0.15s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.2rem;
        }
        .bm-card-jump:hover {
            background: #D84315;
            color: white;
            border-color: #D84315;
        }
        .bm-card-del {
            color: #757575;
        }
        .bm-card-del:hover {
            color: #DC2626;
            background: rgba(220, 38, 38, 0.12);
            border-color: #DC2626;
        }

        .bm-card-edit-wrap {
            margin: 0.35rem 0;
        }
        .bm-card-textarea {
            width: 100%;
            min-height: 55px;
            max-height: 140px;
            font-family: inherit;
            font-size: 0.84rem;
            line-height: 1.4;
            padding: 0.4rem 0.55rem;
            border: 1px solid rgba(0, 0, 0, 0.16);
            border-radius: 5px;
            background: #FAF7F2;
            color: #3E2723;
            resize: vertical;
            box-sizing: border-box;
            outline: none;
            transition: border-color 0.2s, background 0.2s;
        }
        .bm-card-textarea:focus {
            background: #FFFFFF;
            border-color: #D84315;
            box-shadow: 0 0 0 2px rgba(234, 179, 8, 0.25);
        }

        .bm-card-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.7rem;
            color: #8D6E63;
            margin-top: 0.25rem;
        }
        .bm-card-snippet-text {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 65%;
            font-style: italic;
            opacity: 0.85;
        }
        .bm-card-date {
            font-size: 0.7rem;
            color: #8D6E63;
        }

        .bm-empty-state {
            text-align: center;
            padding: 3rem 1.5rem;
            color: #8D6E63;
        }
        .bm-empty-icon {
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            opacity: 0.7;
        }
        .bm-empty-title {
            font-weight: 700;
            font-size: 1rem;
            color: #2D1E18;
            margin-bottom: 0.5rem;
        }
        .bm-empty-desc {
            font-size: 0.85rem;
            line-height: 1.5;
        }

        @keyframes anuvakaPulse {
            0% { box-shadow: 0 0 0 0 rgba(216, 67, 21, 0.6); }
            50% { box-shadow: 0 0 0 8px rgba(216, 67, 21, 0); }
            100% { box-shadow: 0 0 0 0 rgba(216, 67, 21, 0); }
        }

        .anuvaka-highlight {
            animation: anuvakaPulse 1.8s ease-out;
            border-color: #D84315 !important;
        }

        @media print {
            .header, .toc-sidebar, .back-to-top, .modal-overlay, .bookmarks-drawer,
            .bm-drawer-backdrop, .anuvaka-bm-btn, .postit-entity, .postit-inplace-tab,
            #postit-overlay-layer, .verse-pin-badge, .add-note-inline-btn, .selection-note-btn,
            #btn-add-quick-note, #bookmarks-toggle-btn {
                display: none !important;
            }
            
        }
    """


def get_viewer_notes_js(storage_prefix: str = "jsv") -> str:
    """Returns complete JavaScript engine for Notes, Drag & Drop, Hover cards, and Drawer."""
    js_template = """// --- Autonomous Post-It & Bookmarks Entity System ---
        const BM_STORAGE_KEY = 'vedavms_bm_' + (location.pathname.split('/').pop().replace('.html', '') || 'reader');

        function loadNotes() {
            try {
                const raw = localStorage.getItem(BM_STORAGE_KEY);
                return raw ? JSON.parse(raw) : {};
            } catch (e) {
                return {};
            }
        }

        function saveNotes(data) {
            try {
                localStorage.setItem(BM_STORAGE_KEY, JSON.stringify(data));
                updateBookmarksUI();
            } catch (e) {
                console.error('Failed to save notes', e);
            }
        }

        function findNearestTextTarget(docX, docY) {
            const vpX = docX - window.scrollX;
            const vpY = docY - window.scrollY;
            if (vpX >= 0 && vpX <= window.innerWidth && vpY >= 0 && vpY <= window.innerHeight) {
                const elAtPoint = document.elementFromPoint(vpX, vpY);
                if (elAtPoint) {
                    const vp = elAtPoint.closest('.verse-p, .anuvaka-block, .subsection, .section, .mantra-verse, .sanskrit-text');
                    if (vp && vp.id) return vp;
                }
            }
            const targets = document.querySelectorAll('.verse-p, .anuvaka-block, .subsection, .section, .mantra-verse, .sanskrit-text');
            let bestEl = null;
            let minDist = Infinity;
            targets.forEach(el => {
                const rect = el.getBoundingClientRect();
                const midY = window.scrollY + rect.top + (rect.height / 2);
                const dist = Math.abs(midY - docY);
                if (dist < minDist) {
                    minDist = dist;
                    bestEl = el;
                }
            });
            return bestEl;
        }

        function createFloatingNote() {
            const scrollY = window.scrollY;
            const targetY = scrollY + Math.max(100, Math.round(window.innerHeight * 0.28));
            const contentEl = document.querySelector('.main-content');
            const contentRect = contentEl ? contentEl.getBoundingClientRect() : null;

            let targetX = 30;
            if (contentRect) {
                targetX = Math.round(window.scrollX + contentRect.left + Math.min(220, contentRect.width * 0.35));
                if (targetX + 245 > window.innerWidth - 20) {
                    targetX = Math.max(15, window.innerWidth - 260);
                }
            } else {
                targetX = Math.max(15, Math.round(window.innerWidth / 2 - 120));
            }

            const nearest = findNearestTextTarget(targetX + 40, targetY + 20);
            const targetId = nearest ? nearest.id : null;
            createNoteAtCoords(targetId, targetX, targetY, nearest ? '' : 'General Note');
        }

        function createNoteAtCoords(targetId, posX, posY, titleOverride, initialSnippet) {
            hideHoverPreview();
            const data = loadNotes();
            const noteId = 'note_' + Date.now();

            let targetTitle = titleOverride || '';
            let targetSnippet = initialSnippet || '';

            const targetEl = targetId ? document.getElementById(targetId) : null;
            if (targetEl && !targetTitle) {
                const chEl = targetEl.closest('.chapter-container');
                const chHeading = chEl ? chEl.querySelector('.chapter-heading') : null;
                const secEl = (targetEl.closest('.anuvaka-block') || targetEl.closest('.section') || targetEl.closest('.subsection'));
                const numNode = secEl ? (secEl.querySelector('.anuvaka-num') || secEl.querySelector('.section-title')) : null;

                const chTitle = chHeading ? chHeading.textContent.trim() : '';
                const secTitle = numNode ? numNode.textContent.trim() : '';
                targetTitle = secTitle ? (chTitle ? chTitle + ' • ' + secTitle : secTitle) : (chTitle || targetId);

                if (!targetSnippet) {
                    const text = targetEl.textContent.replace('📌+', '').trim();
                    targetSnippet = text.substring(0, 50) + (text.length > 50 ? '...' : '');
                }
            } else if (!targetTitle) {
                targetTitle = 'Post-It Note';
            }

            data[noteId] = {
                id: noteId,
                targetId: targetId || '',
                targetTitle: targetTitle,
                targetSnippet: targetSnippet,
                color: 'yellow',
                text: '',
                posX: Math.round(posX),
                posY: Math.round(posY),
                isOpen: true,
                updatedAt: Date.now()
            };

            saveNotes(data);

            setTimeout(() => {
                const noteEl = document.getElementById('postit-entity-' + noteId);
                if (noteEl) {
                    const ta = noteEl.querySelector('.postit-textarea');
                    if (ta) ta.focus({ preventScroll: true });
                }
            }, 100);
        }

        function createNoteAtTarget(targetId, initialSnippet, event) {
            hideHoverPreview();
            if (event) {
                event.stopPropagation();
                event.preventDefault();
            }

            const data = loadNotes();
            const existingNote = targetId ? Object.values(data).find(n => n.targetId === targetId) : null;
            if (existingNote) {
                openNote(existingNote.id, event);
                return;
            }

            let defaultTop = window.scrollY + 150;
            let defaultLeft = 20;

            const targetEl = targetId ? document.getElementById(targetId) : null;
            if (targetEl) {
                const targetRect = targetEl.getBoundingClientRect();
                const contentEl = document.querySelector('.main-content');
                const contentRect = contentEl ? contentEl.getBoundingClientRect() : targetRect;

                defaultTop = Math.round(window.scrollY + targetRect.top);
                defaultLeft = Math.round(window.scrollX + contentRect.left + Math.min(220, contentRect.width * 0.35));
                if (defaultLeft + 245 > window.innerWidth - 20) {
                    defaultLeft = Math.max(15, window.innerWidth - 260);
                }
            } else if (event && event.pageX && event.pageY) {
                defaultLeft = Math.max(15, Math.min(window.innerWidth - 260, Math.round(event.pageX - 100)));
                defaultTop = Math.max(50, Math.round(event.pageY - 20));
            }

            createNoteAtCoords(targetId, defaultLeft, defaultTop, '', initialSnippet);
        }

        function toggleAnuvakaBookmark(secId, event) {
            hideHoverPreview();
            if (event) {
                event.stopPropagation();
                event.preventDefault();
            }
            const data = loadNotes();
            const existingNote = Object.values(data).find(n => n.targetId === secId);
            if (existingNote) {
                existingNote.isOpen = !existingNote.isOpen;
                saveNotes(data);
                if (existingNote.isOpen) {
                    setTimeout(() => {
                        const noteEl = document.getElementById('postit-entity-' + existingNote.id);
                        if (noteEl) {
                            const ta = noteEl.querySelector('.postit-textarea');
                            if (ta) ta.focus({ preventScroll: true });
                        }
                    }, 80);
                }
            } else {
                createNoteAtTarget(secId, '', event);
            }
        }

        let wasDragMoved = false;
        let isDragActive = false;

        function openNote(noteId, event) {
            hideHoverPreview();
            if (isDragActive || wasDragMoved) {
                wasDragMoved = false;
                isDragActive = false;
                return;
            }
            if (event) {
                event.stopPropagation();
            }
            const data = loadNotes();
            const note = data[noteId];
            if (note) {
                note.isOpen = true;
                const target = note.targetId ? document.getElementById(note.targetId) : null;
                if (target) {
                    const rect = target.getBoundingClientRect();
                    const contentEl = document.querySelector('.main-content');
                    const cRect = contentEl ? contentEl.getBoundingClientRect() : rect;
                    const pageTop = window.scrollY + rect.top;
                    if (!note.posY || Math.abs(note.posY - pageTop) > 600) {
                        note.posY = Math.round(pageTop);
                    }
                    if (!note.posX) {
                        note.posX = Math.round(window.scrollX + cRect.left + Math.min(220, cRect.width * 0.35));
                    }
                }
                saveNotes(data);
                setTimeout(() => {
                    const noteEl = document.getElementById('postit-entity-' + noteId);
                    if (noteEl) {
                        const ta = noteEl.querySelector('.postit-textarea');
                        if (ta) ta.focus({ preventScroll: true });
                    }
                }, 80);
            }
        }

        function closeNote(noteId) {
            hideHoverPreview();
            if (typeof noteDebounce !== 'undefined' && noteDebounce[noteId]) {
                clearTimeout(noteDebounce[noteId]);
                delete noteDebounce[noteId];
            }
            const noteEl = document.getElementById('postit-entity-' + noteId);
            let currentText = null;
            if (noteEl) {
                const ta = noteEl.querySelector('.postit-textarea');
                if (ta) currentText = ta.value;
            }
            const data = loadNotes();
            if (data[noteId]) {
                if (currentText !== null) {
                    data[noteId].text = currentText;
                    data[noteId].updatedAt = Date.now();
                }
                data[noteId].isOpen = false;
                saveNotes(data);
            }
        }

        function deleteNote(noteId) {
            hideHoverPreview();
            const data = loadNotes();
            if (data[noteId]) {
                const hasText = data[noteId].text && data[noteId].text.trim().length > 0;
                if (!hasText || confirm('Delete this Post-It note?')) {
                    delete data[noteId];
                    saveNotes(data);
                }
            }
        }

        function setNoteColor(noteId, color) {
            const data = loadNotes();
            if (data[noteId]) {
                data[noteId].color = color;
                saveNotes(data);
            }
        }

        let noteDebounce = {};
        function updateNoteText(noteId, text) {
            clearTimeout(noteDebounce[noteId]);
            const statusEl = document.getElementById('postit-status-' + noteId);
            if (statusEl) {
                statusEl.textContent = 'Saving...';
                statusEl.style.opacity = '0.6';
            }
            noteDebounce[noteId] = setTimeout(() => {
                const data = loadNotes();
                if (data[noteId]) {
                    data[noteId].text = text;
                    data[noteId].updatedAt = Date.now();
                    try {
                        localStorage.setItem(BM_STORAGE_KEY, JSON.stringify(data));
                        const statusDone = document.getElementById('postit-status-' + noteId);
                        if (statusDone) {
                            statusDone.textContent = 'Saved';
                            statusDone.style.opacity = '1';
                        }
                        const noteEl = document.getElementById('postit-entity-' + noteId);
                        if (noteEl) {
                            const ta = noteEl.querySelector('.postit-textarea');
                            if (ta && ta.value !== text) ta.value = text;
                        }
                        const tabEl = document.getElementById('postit-tab-' + noteId);
                        if (tabEl) {
                            const snip = tabEl.querySelector('.inplace-tab-title');
                            if (snip) snip.textContent = (text || '(Empty note)').substring(0, 16);
                            tabEl.setAttribute('data-note-preview', text || '(Empty note)');
                        }
                    } catch (e) {}
                }
            }, 350);
        }

        function clearAllBookmarks() {
            if (confirm('Are you sure you want to remove all bookmarks and notes for this text?')) {
                localStorage.removeItem(BM_STORAGE_KEY);
                updateBookmarksUI();
            }
        }

        function toggleBookmarksDrawer(force) {
            const drawer = document.getElementById('bookmarks-drawer');
            const backdrop = document.getElementById('bm-drawer-backdrop');
            if (!drawer || !backdrop) return;
            const shouldOpen = force !== undefined ? force : !drawer.classList.contains('active');
            if (shouldOpen) {
                closeMobileToc();
                closePrintModal();
                drawer.classList.add('active');
                backdrop.classList.add('active');
                renderBookmarksDrawer();
            } else {
                drawer.classList.remove('active');
                backdrop.classList.remove('active');
            }
        }

        function jumpToBookmark(noteId) {
            hideHoverPreview();
            toggleBookmarksDrawer(false);
            const data = loadNotes();
            const note = data[noteId];
            if (!note) return;

            note.isOpen = true;
            saveNotes(data);

            setTimeout(() => {
                const noteEl = document.getElementById('postit-entity-' + noteId);
                if (noteEl) {
                    noteEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    const ta = noteEl.querySelector('.postit-textarea');
                    if (ta) ta.focus({ preventScroll: true });
                } else if (note.targetId) {
                    const target = document.getElementById(note.targetId);
                    if (target) {
                        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        target.classList.add('anuvaka-highlight');
                        setTimeout(() => { target.classList.remove('anuvaka-highlight'); }, 2000);
                    }
                }
            }, 100);
        }

        // --- Dragging Logic with Exact Page Coordinates ---
        let activeDragNote = null;
        let dragOffsetX = 0;
        let dragOffsetY = 0;
        let dragStartClientX = 0;
        let dragStartClientY = 0;

        function startDragNote(noteId, e) {
            hideHoverPreview();
            if (e.target.closest('.postit-entity-tools') || e.target.closest('button') || e.target.closest('textarea')) return;
            const noteEl = document.getElementById('postit-entity-' + noteId) || document.getElementById('postit-tab-' + noteId);
            if (!noteEl) return;
            activeDragNote = noteId;
            wasDragMoved = false;
            isDragActive = false;

            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            dragStartClientX = clientX;
            dragStartClientY = clientY;

            const rect = noteEl.getBoundingClientRect();
            dragOffsetX = clientX - rect.left;
            dragOffsetY = clientY - rect.top;
        }

        function onDragMove(e) {
            if (!activeDragNote) return;
            const noteEl = document.getElementById('postit-entity-' + activeDragNote) || document.getElementById('postit-tab-' + activeDragNote);
            if (!noteEl) return;

            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;

            // Only treat as drag if movement exceeds 6px threshold
            if (!isDragActive) {
                const dist = Math.hypot(clientX - dragStartClientX, clientY - dragStartClientY);
                if (dist < 6) return;
                isDragActive = true;
                wasDragMoved = true;
                noteEl.classList.add('dragging');
                document.querySelectorAll('.postit-entity, .postit-inplace-tab').forEach(el => el.style.zIndex = '1200');
                noteEl.style.zIndex = '2100';
            }

            const docX = clientX + window.scrollX - dragOffsetX;
            const docY = clientY + window.scrollY - dragOffsetY;

            const maxLeft = Math.max(10, document.documentElement.scrollWidth - 120);
            const clampLeft = Math.max(10, Math.min(maxLeft, docX));
            const clampTop = Math.max(50, docY);

            noteEl.style.left = clampLeft + 'px';
            noteEl.style.top = clampTop + 'px';
            noteEl.style.right = 'auto';
        }

        document.addEventListener('mousemove', onDragMove);
        document.addEventListener('touchmove', onDragMove, { passive: false });

        function endDragNote() {
            if (!activeDragNote) return;
            const noteEl = document.getElementById('postit-entity-' + activeDragNote) || document.getElementById('postit-tab-' + activeDragNote);
            if (noteEl) {
                noteEl.classList.remove('dragging');
                if (isDragActive && wasDragMoved) {
                    const data = loadNotes();
                    if (data[activeDragNote]) {
                        const newX = parseInt(noteEl.style.left, 10);
                        const newY = parseInt(noteEl.style.top, 10);
                        data[activeDragNote].posX = newX;
                        data[activeDragNote].posY = newY;

                        // Auto-detect nearest verse or section under drop location
                        const nearest = findNearestTextTarget(newX + 40, newY + 20);
                        if (nearest && nearest.id) {
                            data[activeDragNote].targetId = nearest.id;
                            const chEl = nearest.closest('.chapter-container');
                            const chHeading = chEl ? chEl.querySelector('.chapter-heading') : null;
                            const secEl = nearest.closest('.anuvaka-block');
                            const numNode = secEl ? (secEl.querySelector('.anuvaka-num') || secEl.querySelector('.section-title')) : null;
                            const chTitle = chHeading ? chHeading.textContent.trim() : '';
                            const secTitle = numNode ? numNode.textContent.trim() : '';
                            data[activeDragNote].targetTitle = secTitle ? (chTitle ? chTitle + ' • ' + secTitle : secTitle) : (chTitle || nearest.id);
                            if (!data[activeDragNote].text) {
                                const tText = nearest.textContent.replace('📌+', '').trim();
                                data[activeDragNote].targetSnippet = tText.substring(0, 50) + (tText.length > 50 ? '...' : '');
                            }
                        }
                        saveNotes(data);
                    }
                }
            }
            activeDragNote = null;
            isDragActive = false;
        }

        document.addEventListener('mouseup', endDragNote);
        document.addEventListener('touchend', endDragNote);

        // --- Double-Click Anywhere in Body Text to Drop Note ---
        document.addEventListener('dblclick', function(e) {
            if (e.target.closest('.postit-entity') || e.target.closest('button') || e.target.closest('a') || e.target.closest('.bookmarks-drawer') || e.target.closest('.toc-sidebar') || e.target.closest('.header') || e.target.closest('.modal-overlay')) return;
            const targetP = e.target.closest('.verse-p, .anuvaka-block, .subsection, .section, .mantra-verse, .sanskrit-text');
            const targetId = targetP ? targetP.id : null;
            const posX = Math.max(15, e.pageX - 30);
            const posY = Math.max(60, e.pageY - 20);
            createNoteAtCoords(targetId, posX, posY);
        });

        // --- Hover Card Preview for Notes ---
        let hoverCardEl = null;

        function hideHoverPreview() {
            if (hoverCardEl) {
                hoverCardEl.classList.remove('visible');
                hoverCardEl.style.display = 'none';
                hoverCardEl.innerHTML = '';
            }
        }

        function showHoverPreview(targetEl, title, text, color) {
            if (!text && !title) return;
            // Never show hover preview if the target or note is already open
            if (targetEl) {
                const tabId = targetEl.id || '';
                if (tabId.startsWith('postit-tab-')) {
                    const nid = tabId.replace('postit-tab-', '');
                    const notes = loadNotes();
                    if (notes[nid] && notes[nid].isOpen) {
                        hideHoverPreview();
                        return;
                    }
                }
            }
            // Never show hover preview if cursor or focus is inside an open note or drawer
            if (document.querySelector('.postit-entity:hover, .bookmarks-drawer:hover, .postit-entity:focus-within')) {
                hideHoverPreview();
                return;
            }

            if (!hoverCardEl) {
                hoverCardEl = document.createElement('div');
                hoverCardEl.id = 'postit-hover-card';
                document.body.appendChild(hoverCardEl);
            }

            hoverCardEl.style.display = 'block';
            hoverCardEl.className = 'postit-hover-card postit-theme-' + (color || 'yellow') + ' visible';
            hoverCardEl.innerHTML = `
                <div class="hover-card-header">
                    <span class="hover-card-pin">📌</span>
                    <span class="hover-card-title">${escapeHtmlText(title || 'Note Preview')}</span>
                </div>
                <div class="hover-card-content">${escapeHtmlText(text || '(Empty note)')}</div>
            `;

            const rect = targetEl.getBoundingClientRect();
            const cardWidth = 220;
            let left = window.scrollX + rect.left;
            if (left + cardWidth > window.innerWidth - 10) {
                left = window.scrollX + rect.right - cardWidth;
            }
            const top = window.scrollY + rect.bottom + 8;

            hoverCardEl.style.left = Math.max(10, left) + 'px';
            hoverCardEl.style.top = top + 'px';
        }

        document.addEventListener('mouseover', function(e) {
            if (e.target.closest('.postit-entity, .bookmarks-drawer, .modal-overlay')) {
                hideHoverPreview();
                return;
            }
            const btn = e.target.closest('[data-note-preview]');
            if (btn) {
                const tabId = btn.id || '';
                if (tabId.startsWith('postit-tab-')) {
                    const nid = tabId.replace('postit-tab-', '');
                    const notes = loadNotes();
                    if (notes[nid] && notes[nid].isOpen) {
                        hideHoverPreview();
                        return;
                    }
                }
                const text = btn.getAttribute('data-note-preview');
                const color = btn.getAttribute('data-note-color') || 'yellow';
                const title = btn.getAttribute('data-note-title') || 'Note';
                showHoverPreview(btn, title, text, color);
            }
        });

        document.addEventListener('mouseout', function(e) {
            const btn = e.target.closest('[data-note-preview]');
            if (btn) {
                hideHoverPreview();
            }
        });

        // Immediately dismiss hover card on any click, pointerdown, mousedown, touch, or focus on notes or tabs
        const dismissEvents = ['pointerdown', 'mousedown', 'touchstart', 'click'];
        dismissEvents.forEach(evt => {
            document.addEventListener(evt, function(e) {
                if (e.target.closest('.postit-entity, .postit-inplace-tab, .anuvaka-bm-btn, .postit-hover-card, .bm-card')) {
                    hideHoverPreview();
                }
            }, { capture: true, passive: true });
        });

        document.addEventListener('focusin', function(e) {
            if (e.target.closest('.postit-entity, .bm-card-textarea')) {
                hideHoverPreview();
            }
        }, true);

        // --- Selection Tooltip ---
        let selectionNoteBtn = null;
        document.addEventListener('mouseup', function(e) {
            if (e.target.closest('.postit-entity') || e.target.closest('.bookmarks-drawer') || e.target.closest('.modal-overlay')) return;
            const sel = window.getSelection();
            const text = sel ? sel.toString().trim() : '';

            if (text.length >= 3) {
                const range = sel.getRangeAt(0);
                const rect = range.getBoundingClientRect();
                if (!selectionNoteBtn) {
                    selectionNoteBtn = document.createElement('button');
                    selectionNoteBtn.className = 'selection-note-btn';
                    selectionNoteBtn.innerHTML = '📌 Add Post-It';
                    document.body.appendChild(selectionNoteBtn);
                }
                selectionNoteBtn.style.top = Math.round(window.scrollY + rect.bottom + 8) + 'px';
                selectionNoteBtn.style.left = Math.round(window.scrollX + rect.left) + 'px';
                selectionNoteBtn.style.display = 'inline-flex';

                selectionNoteBtn.onmousedown = function(ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    const node = range.commonAncestorContainer;
                    const parentP = node.nodeType === 1 ? node.closest('.verse-p, .anuvaka-block, .subsection, .section, .mantra-verse, .sanskrit-text') : (node.parentElement ? node.parentElement.closest('.verse-p, .anuvaka-block, .subsection, .section, .mantra-verse, .sanskrit-text') : null);
                    const targetId = parentP ? parentP.id : null;
                    selectionNoteBtn.style.display = 'none';
                    createNoteAtTarget(targetId, text);
                    sel.removeAllRanges();
                };
            } else {
                if (selectionNoteBtn) selectionNoteBtn.style.display = 'none';
            }
        });

        function escapeHtmlText(str) {
            if (!str) return '';
            return String(str)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;');
        }

        function updateBookmarksUI() {
            hideHoverPreview();
            const data = loadNotes();
            const notesList = Object.values(data);
            const count = notesList.length;

            const badge = document.getElementById('bm-badge-count');
            const bmBtn = document.getElementById('bookmarks-toggle-btn');
            if (badge) {
                badge.textContent = count;
                badge.style.display = count > 0 ? 'inline-block' : 'none';
            }
            if (bmBtn) {
                if (count > 0) bmBtn.classList.add('active');
                else bmBtn.classList.remove('active');
            }

            let overlay = document.getElementById('postit-overlay-layer');
            if (!overlay) {
                overlay = document.createElement('div');
                overlay.id = 'postit-overlay-layer';
                document.body.appendChild(overlay);
            }

            let overlayHtml = '';
            notesList.forEach(note => {
                const color = note.color || 'yellow';
                const previewText = note.text ? note.text : '(Empty note)';
                const leftStyle = note.posX ? `left: ${note.posX}px;` : 'right: 25px;';
                const topStyle = note.posY ? `top: ${note.posY}px;` : 'top: 150px;';

                if (note.isOpen) {
                    overlayHtml += `
                        <div class="postit-entity postit-theme-${color}" id="postit-entity-${note.id}" style="${leftStyle} ${topStyle}">
                            <div class="postit-entity-header" onmousedown="startDragNote('${note.id}', event)" ontouchstart="startDragNote('${note.id}', event)">
                                <div class="postit-drag-handle" title="Drag anywhere in text">
                                    <span class="postit-pin">📌</span>
                                    <span class="postit-entity-title" title="${escapeHtmlText(note.targetTitle)}">${escapeHtmlText(note.targetTitle)}</span>
                                </div>
                                <div class="postit-entity-tools">
                                    <div class="postit-color-picker" title="Change color">
                                        <button type="button" class="color-btn color-yellow ${color === 'yellow' ? 'active' : ''}" onclick="setNoteColor('${note.id}', 'yellow')" title="Yellow"></button>
                                        <button type="button" class="color-btn color-saffron ${color === 'saffron' ? 'active' : ''}" onclick="setNoteColor('${note.id}', 'saffron')" title="Saffron"></button>
                                        <button type="button" class="color-btn color-green ${color === 'green' ? 'active' : ''}" onclick="setNoteColor('${note.id}', 'green')" title="Green"></button>
                                        <button type="button" class="color-btn color-rose ${color === 'rose' ? 'active' : ''}" onclick="setNoteColor('${note.id}', 'rose')" title="Rose"></button>
                                    </div>
                                    <button type="button" class="postit-tool-btn postit-tool-del" onclick="deleteNote('${note.id}')" title="Delete note">🗑️</button>
                                    <button type="button" class="postit-tool-btn postit-tool-close" onclick="closeNote('${note.id}')" title="Close / Fold note in-place">✕</button>
                                </div>
                            </div>
                            <div class="postit-entity-body">
                                <textarea class="postit-textarea" placeholder="Add study note, chant count, commentary..." oninput="updateNoteText('${note.id}', this.value)">${escapeHtmlText(note.text || '')}</textarea>
                                <div class="postit-footer-bar">
                                    <span class="postit-status" id="postit-status-${note.id}">Saved</span>
                                    <button type="button" class="postit-done-btn" onclick="closeNote('${note.id}')" title="Fold to in-place tab">✔ Done</button>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    overlayHtml += `
                        <div class="postit-inplace-tab postit-theme-${color}" id="postit-tab-${note.id}" style="${leftStyle} ${topStyle}" onclick="openNote('${note.id}', event)" onmousedown="startDragNote('${note.id}', event)" ontouchstart="startDragNote('${note.id}', event)" data-note-preview="${escapeHtmlText(previewText)}" data-note-title="${escapeHtmlText(note.targetTitle)}" data-note-color="${color}" title="Click to open Post-It note • Drag to move">
                            <span class="inplace-tab-pin">📌</span>
                            <span class="inplace-tab-title">${escapeHtmlText(previewText.substring(0, 16))}</span>
                        </div>
                    `;
                }
            });
            overlay.innerHTML = overlayHtml;

            document.querySelectorAll('.verse-pin-badge').forEach(el => el.remove());

            const targetsMap = {};
            notesList.forEach(note => {
                if (note.targetId) {
                    if (!targetsMap[note.targetId]) targetsMap[note.targetId] = [];
                    targetsMap[note.targetId].push(note);
                }
            });

            document.querySelectorAll('.section, .anuvaka-block, .subsection').forEach(sec => {
                const secId = sec.id;
                const btn = sec.querySelector('.anuvaka-bm-btn');
                const secNotes = targetsMap[secId] || [];
                if (btn) {
                    if (secNotes.length > 0) {
                        btn.classList.add('active');
                        const anyOpen = secNotes.some(n => n.isOpen);
                        const noteWithText = secNotes.find(n => n.text && n.text.trim()) || secNotes[0];
                        const previewText = noteWithText && noteWithText.text ? noteWithText.text : '(Empty note)';

                        btn.title = '📌 ' + previewText;
                        btn.setAttribute('data-note-preview', previewText);
                        btn.setAttribute('data-note-color', noteWithText.color || 'yellow');
                        btn.setAttribute('data-note-title', noteWithText.targetTitle || 'Anuvaka Note');

                        if (anyOpen) {
                            btn.innerHTML = '✕ <span class="bm-btn-label">Close Note</span>';
                            btn.removeAttribute('data-note-preview');
                            btn.title = 'Close note for this section';
                        } else {
                            btn.innerHTML = '📌 <span class="bm-btn-label">View Note</span>';
                        }
                    } else {
                        btn.classList.remove('active');
                        btn.removeAttribute('data-note-preview');
                        btn.title = 'Attach Post-It Note to this section (or double-click text)';
                        btn.innerHTML = '🔖 <span class="bm-btn-label">Note</span>';
                    }
                }
            });

            renderBookmarksDrawer();
        }

        function renderBookmarksDrawer() {
            const listEl = document.getElementById('bm-drawer-list');
            const countEl = document.getElementById('bm-drawer-count');
            if (!listEl) return;

            const data = loadNotes();
            const entries = Object.values(data);
            if (countEl) countEl.textContent = entries.length;

            if (entries.length === 0) {
                listEl.innerHTML = `
                    <div class="bm-empty-state">
                        <div class="bm-empty-icon">📌</div>
                        <div class="bm-empty-title">No Post-It Notes Yet</div>
                        <div class="bm-empty-desc">Attach a sticky note anywhere: click <strong>➕ Note</strong> in the top bar, double-click anywhere in the text, or click <strong>📌+</strong> beside any verse line.</div>
                    </div>
                `;
                return;
            }

            entries.sort((a, b) => (b.updatedAt || 0) - (a.updatedAt || 0));

            let html = '';
            entries.forEach(item => {
                const color = item.color || 'yellow';
                const dateStr = item.updatedAt ? new Date(item.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '';

                html += `
                    <div class="bm-card card-theme-${color}">
                        <div class="bm-card-top">
                            <div class="bm-card-ch" title="${escapeHtmlText(item.targetTitle || 'Note')}">${escapeHtmlText(item.targetTitle || 'Note')}</div>
                            <div class="bm-card-actions">
                                <button type="button" class="bm-card-action-btn bm-card-jump" onclick="jumpToBookmark('${item.id}')" title="View note in text">↗ View</button>
                                <button type="button" class="bm-card-action-btn bm-card-del" onclick="deleteNote('${item.id}')" title="Delete note">🗑️</button>
                            </div>
                        </div>
                        <div class="bm-card-edit-wrap">
                            <textarea class="bm-card-textarea" placeholder="Add study note, chant count, commentary..." oninput="updateNoteText('${item.id}', this.value)">${escapeHtmlText(item.text || '')}</textarea>
                        </div>
                        <div class="bm-card-meta">
                            <span class="bm-card-snippet-text">${item.targetSnippet ? 'Attached: ' + escapeHtmlText(item.targetSnippet) : ''}</span>
                            <span class="bm-card-date">${dateStr}</span>
                        </div>
                    </div>
                `;
            });
            listEl.innerHTML = html;
        }

        function populateSectionDropdown() {
            const select = document.getElementById('section-select-dropdown');
            if (!select) return;
            select.innerHTML = '';

            const chGroup = document.createElement('optgroup');
            chGroup.label = "Chapters / Sections (Complete)";

            const anuvakaGroup = document.createElement('optgroup');
            anuvakaGroup.label = "Individual Anuvakas";

            document.querySelectorAll('.chapter-container').forEach(ch => {
                const chHeading = ch.querySelector('.chapter-heading');
                const chTitle = chHeading ? chHeading.textContent.trim() : ch.id;
                const count = ch.querySelectorAll('.anuvaka-block').length;

                const chOpt = document.createElement('option');
                chOpt.value = ch.id;
                chOpt.textContent = `${chTitle} (${count} anuvakas)`;
                chGroup.appendChild(chOpt);

                ch.querySelectorAll('.anuvaka-block').forEach(sec => {
                    const numEl = sec.querySelector('.anuvaka-num');
                    const codeEl = sec.querySelector('.anuvaka-code');
                    const secTitle = numEl ? numEl.textContent.trim() : (codeEl ? codeEl.textContent.trim() : 'प्रारम्भः (Intro)');
                    const secOpt = document.createElement('option');
                    secOpt.value = sec.id;
                    secOpt.textContent = `${chTitle} - ${secTitle}`;
                    anuvakaGroup.appendChild(secOpt);
                });
            });

            select.appendChild(chGroup);
            select.appendChild(anuvakaGroup);
        }

        document.addEventListener('DOMContentLoaded', function() {
            populateSectionDropdown();

            const firstCh = document.querySelector('.chapter-container');
            if (firstCh) {
                currentActiveChapterId = firstCh.id;
                const chHeading = firstCh.querySelector('.chapter-heading');
                currentActiveChapterTitle = chHeading ? chHeading.textContent.trim() : firstCh.id;
                currentActiveChapterCount = firstCh.querySelectorAll('.anuvaka-block').length;
            }

            // IntersectionObserver for tracking active Chapter and Anuvaka during scroll
            const navObserver = new IntersectionObserver((entries) => {
                let bestEntry = null;
                let minDistance = Infinity;

                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const dist = Math.abs(entry.boundingClientRect.top - 85);
                        if (dist < minDistance) {
                            minDistance = dist;
                            bestEntry = entry;
                        }
                    }
                });

                if (bestEntry) {
                    updateActiveContext(bestEntry.target);
                    const secNode = bestEntry.target.classList.contains('anuvaka-block') 
                        ? bestEntry.target 
                        : bestEntry.target.querySelector('.anuvaka-block');
                    if (secNode) {
                        currentActiveSectionId = secNode.id;
                        const numNode = secNode.querySelector('.anuvaka-num');
                        const codeNode = secNode.querySelector('.anuvaka-code');
                        if (numNode) {
                            currentActiveSectionTitle = numNode.textContent.trim();
                        } else if (codeNode) {
                            currentActiveSectionTitle = codeNode.textContent.trim();
                        } else {
                            currentActiveSectionTitle = currentActiveChapterTitle || "";
                        }
                    }
                    const parentCh = bestEntry.target.closest('.chapter-container') || (bestEntry.target.classList.contains('chapter-container') ? bestEntry.target : null);
                    if (parentCh) {
                        currentActiveChapterId = parentCh.id;
                        const chHeading = parentCh.querySelector('.chapter-heading');
                        currentActiveChapterTitle = chHeading ? chHeading.textContent.trim() : parentCh.id;
                        currentActiveChapterCount = parentCh.querySelectorAll('.anuvaka-block').length;
                    }
                }
            }, { rootMargin: '-75px 0px -70% 0px', threshold: 0 });

            document.querySelectorAll('.chapter-container, .anuvaka-block').forEach(el => navObserver.observe(el));

            // Direct click on Suchi item immediately highlights and smoothly scrolls to target
            document.querySelectorAll('.toc-sub-list a, .toc-ch-title a').forEach(link => {
                link.addEventListener('click', function(e) {
                    if (isMobileView()) {
                        closeMobileToc();
                    }
                    const href = this.getAttribute('href');
                    if (href && href.startsWith('#')) {
                        const targetId = href.slice(1);
                        const target = document.getElementById(targetId);
                        if (target) {
                            e.preventDefault();
                            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            if (history.pushState) {
                                history.pushState(null, '', href);
                            }
                            updateActiveContext(target);
                            const secNode = target.classList.contains('anuvaka-block') 
                                ? target 
                                : target.querySelector('.anuvaka-block');
                            if (secNode) {
                                currentActiveSectionId = secNode.id;
                                const numNode = secNode.querySelector('.anuvaka-num');
                                const codeNode = secNode.querySelector('.anuvaka-code');
                                if (numNode) {
                                    currentActiveSectionTitle = numNode.textContent.trim();
                                } else if (codeNode) {
                                    currentActiveSectionTitle = codeNode.textContent.trim();
                                } else {
                                    currentActiveSectionTitle = currentActiveChapterTitle || "";
                                }
                            }
                            const parentCh = target.closest('.chapter-container') || (target.classList.contains('chapter-container') ? target : null);
                            if (parentCh) {
                                currentActiveChapterId = parentCh.id;
                                const chHeading = parentCh.querySelector('.chapter-heading');
                                currentActiveChapterTitle = chHeading ? chHeading.textContent.trim() : parentCh.id;
                                currentActiveChapterCount = parentCh.querySelectorAll('.anuvaka-block').length;
                            }
                        }
                    }
                });
            });

            // Close mobile Suchi on Escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    closeMobileToc();
                    closePrintModal();
                    toggleBookmarksDrawer(false);
                }
            });

            function onOrientationOrResize() {
                handleLayoutChange();
                // Ensure viewport zoom and scaling reset cleanly on mobile orientation switch
                const viewportMeta = document.querySelector('meta[name="viewport"]');
                if (viewportMeta) {
                    viewportMeta.setAttribute('content', 'width=device-width, initial-scale=1.0, viewport-fit=cover');
                }
            }

            // Trap window resize
            window.addEventListener('resize', onOrientationOrResize);

            // Trap mobile device orientation change (both legacy and modern APIs)
            window.addEventListener('orientationchange', function() {
                setTimeout(onOrientationOrResize, 50);
                setTimeout(onOrientationOrResize, 150);
                setTimeout(onOrientationOrResize, 350);
            });

            if (window.screen && window.screen.orientation) {
                window.screen.orientation.addEventListener('change', function() {
                    setTimeout(onOrientationOrResize, 50);
                    setTimeout(onOrientationOrResize, 150);
                    setTimeout(onOrientationOrResize, 350);
                });
            }

            const mqlPortrait = window.matchMedia('(orientation: portrait)');
            if (mqlPortrait.addEventListener) {
                mqlPortrait.addEventListener('change', onOrientationOrResize);
            } else if (mqlPortrait.addListener) {
                mqlPortrait.addListener(onOrientationOrResize);
            }

            const sidebar = document.querySelector('.toc-sidebar');
            if (sidebar) {
                let tocTimeout;
                sidebar.addEventListener('wheel', () => {
                    isUserInteractingWithToc = true;
                    clearTimeout(tocTimeout);
                    tocTimeout = setTimeout(() => { isUserInteractingWithToc = false; }, 1500);
                }, { passive: true });
            }

            // Synchronize initial layout state based on screen orientation and width
            handleLayoutChange();
            const tocState = JSON.parse(localStorage.getItem('toc-chapters') || '{}');
            for (const [id, isCollapsed] of Object.entries(tocState)) {
                if (isCollapsed) {
                    const el = document.getElementById(id);
                    if (el) el.classList.add('collapsed');
                }
            }
            const savedFont = localStorage.getItem('reader-font-idx');
            if (savedFont !== null) {
                setFont(parseInt(savedFont, 10) || 0);
            }
            const savedSize = localStorage.getItem('reader-font-size');
            if (savedSize !== null) {
                currentSize = parseFloat(savedSize) || defaultSize;
                applyFontSize();
            } else {
                updateFontSizeDisplay();
            }
            updateBookmarksUI();
        });

        window.addEventListener('scroll', function() {
            const btn = document.getElementById('back-to-top');
            if (btn) {
                if (window.scrollY > 350) btn.classList.add('visible');
                else btn.classList.remove('visible');
            }
        });
    
    """
    return js_template.replace("__STORAGE_PREFIX__", storage_prefix)
