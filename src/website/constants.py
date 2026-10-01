"""
Constants and Configuration for Jaimineeya Samaveda Website Generator
"""

AUDIO_FILENAME_FORMAT = "JSV_{parva}_{kandah}_{sama}.mp3"

SITE_CONFIG = {
    'samhita': {
        'title_sa': 'जैमिनीयसामवेद संहिता',
        'title_en': 'Jaimineeya Sama Samhita',
        'footer_sa': 'जैमिनीयसामवेद संहिता',
        'meta_desc': 'Jaimineeya Sama Samhita digital archive',
        'keywords': 'Samaveda, Jaimineeya, Samhita, Ganam, Vedas, Sanskrit'
    },
    'aaranam': {
        'title_sa': 'जैमिनीयसामवेद आरण्यकम्',
        'title_en': 'Jaimineeya Sama Aaranya Ganam', 
        'footer_sa': 'जैमिनीयसामवेद आरण्यकम्',
        'meta_desc': 'Jaimineeya Sama Aaranam digital archive',
        'keywords': 'Samaveda, Jaimineeya, Aaranam, Aranya, Ganam, Vedas, Sanskrit'
    },
    'collection': {
        'title_sa': 'जैमिनीयसामवेद सङ्ग्रहः',
        'title_en': 'Jaimineeya Sama Sangraha',
        'footer_sa': 'जैमिनीयसामवेद सङ्ग्रहः',
        'meta_desc': 'Jaimineeya Sama Sangraha collection',
        'keywords': 'Samaveda, Jaimineeya, Sangraha, Collection, Vedas, Sanskrit'
    },
    'malayalam': {
        'title_sa': 'ജൈമിനീയ സാമവേദ സംഹിത',
        'title_en': 'Jaimineeya Sama Samhita (Malayalam)',
        'footer_sa': 'ജൈമിനീയ സാമവേദ സംഹിത',
        'meta_desc': 'Jaimineeya Sama Samhita digital archive in Malayalam script with Grantha swara notations',
        'keywords': 'Samaveda, Jaimineeya, Samhita, Malayalam, Grantha, Swara, Vedas, Sanskrit'
    },
    'kpully_devanagari': {
        'title_sa': 'जैमिनीयसामवेद संहिता (कोडुन्तिरपुळ्ळि पाठः)',
        'title_en': 'Jaimineeya Sama Samhita (Kodunthirapully Devanagari)',
        'footer_sa': 'जैमिनीयसामवेद संहिता (कोडुन्तिरपुळ्ळि पाठः)',
        'meta_desc': 'Jaimineeya Sama Samhita in Kodunthirapully swara-above layout',
        'keywords': 'Samaveda, Jaimineeya, Samhita, Kodunthirapully, KPully, Devanagari'
    },
    'samhita_samam': {
        'title_sa': 'जैमिनीयसामवेद संहिता (साम सविशेषम्)',
        'title_en': 'Jaimineeya Sama Samhita (Samam Chants with Metadata)',
        'footer_sa': 'जैमिनीयसामवेद संहिता (साम सविशेषम्)',
        'meta_desc': 'Jaimineeya Sama Samhita chants with Rishi, Devata, Chandas metadata',
        'keywords': 'Samaveda, Jaimineeya, Samam, Metadata, Ganam'
    },
    'samhita_rik': {
        'title_sa': 'जैमिनीय सामवेद संहिता (ऋक् सविशेषम्)',
        'title_en': 'Jaimineeya Sama Samhita (Rik Verses with Metadata)',
        'footer_sa': 'जैमिनीय सामवेद संहिता (ऋक् सविशेषम्)',
        'meta_desc': 'Jaimineeya Sama Samhita Rik verses with Vargeekaran classification',
        'keywords': 'Samaveda, Jaimineeya, Rik, Archikam, Metadata'
    },
    'samhita_samam_nometa': {
        'title_sa': 'जैमिनीय सामवेद संहिता (साम गान पाठः)',
        'title_en': 'Jaimineeya Sama Samhita (Samam Chanting Edition - No Metadata)',
        'footer_sa': 'जैमिनीय सामवेद संहिता (साम गान पाठः)',
        'meta_desc': 'Jaimineeya Sama Samhita recitation edition with chants only',
        'keywords': 'Samaveda, Jaimineeya, Samam, Chanting, Ganam'
    },
    'samhita_rik_nometa': {
        'title_sa': 'जैमिनीय सामवेद संहिता (ऋक् पाठः)',
        'title_en': 'Jaimineeya Sama Samhita (Rik Recitation Edition - No Metadata)',
        'footer_sa': 'जैमिनीय सामवेद संहिता (ऋक् पाठः)',
        'meta_desc': 'Jaimineeya Sama Samhita pure Rik recitation text',
        'keywords': 'Samaveda, Jaimineeya, Rik, Archikam'
    }
}


def _sync_site_config_from_yaml():
    try:
        from utils import load_pipeline_config
        cfg = load_pipeline_config()
        web_cfg = cfg.get('generate_website', {})
        for mode, mcfg in web_cfg.items():
            if isinstance(mcfg, dict) and 'title' in mcfg:
                if mode in SITE_CONFIG:
                    SITE_CONFIG[mode]['title_sa'] = mcfg['title']
                    SITE_CONFIG[mode]['footer_sa'] = mcfg['title']
    except Exception:
        pass


_sync_site_config_from_yaml()

MALAYALAM_MODIFIER_MAP = {
    'A': ('mod-a', '&#xE004;'),
    'a': ('mod-a', '&#xE004;'),
    '⁀': ('mod-a', '&#xE004;'),
    'A1': ('mod-a1', '&#xE00D;'),
    'a1': ('mod-a1', '&#xE00D;'),
    'A_1': ('mod-a1', '&#xE00D;'),
    'a_1': ('mod-a1', '&#xE00D;'),
    'A2': ('mod-a2', '&#xE02E;'),
    'a2': ('mod-a2', '&#xE02E;'),
    'A_2': ('mod-a2', '&#xE02E;'),
    'a_2': ('mod-a2', '&#xE02E;'),
    'B': ('mod-b', '&#xE005;'),
    'b': ('mod-b', '&#xE005;'),
    '^': ('mod-b', '&#xE005;'),
    '∧': ('mod-b', '&#xE005;'),
    'C': ('mod-c', '&#xE001;'),
    'c': ('mod-c', '&#xE001;'),
    '·': ('mod-c', '&#xE001;'),
    'D': ('mod-d', '&#xE006;'),
    'd': ('mod-d', '&#xE006;'),
    'Ʌ': ('mod-d', '&#xE006;'),
    'E': ('mod-e', '&#xE002;'),
    'e': ('mod-e', '&#xE002;'),
    '┃': ('mod-e', '&#xE002;'),
    'L': ('mod-e', '&#xE002;'),
    'D1': ('mod-d1', '&#xE00E;'),
    'd1': ('mod-d1', '&#xE00E;'),
    'D_1': ('mod-d1', '&#xE00E;'),
    'd_1': ('mod-d1', '&#xE00E;'),
    '↗': ('mod-d1', '&#xE00E;'),
    '\uE00E': ('mod-d1', '&#xE00E;'),
    'D2': ('mod-d2', '&#xE00F;'),
    'd2': ('mod-d2', '&#xE00F;'),
    'D_2': ('mod-d2', '&#xE00F;'),
    'd_2': ('mod-d2', '&#xE00F;'),
    '✓': ('mod-d2', '&#xE00F;'),
    '\uE00F': ('mod-d2', '&#xE00F;'),
    'I': ('mod-i', '&#xE02A;'),
    'i': ('mod-i', '&#xE02A;'),
    '⫽': ('mod-i', '&#xE02A;'),
    '\uE02A': ('mod-i', '&#xE02A;'),
    'J': ('mod-j', '&#xE02B;'),
    'j': ('mod-j', '&#xE02B;'),
    '¯': ('mod-j', '&#xE02B;'),
    '\uE02B': ('mod-j', '&#xE02B;'),
    'B1': ('mod-b1', '&#xE02C;'),
    'b1': ('mod-b1', '&#xE02C;'),
    'B_1': ('mod-b1', '&#xE02C;'),
    'b_1': ('mod-b1', '&#xE02C;'),
    '/': ('mod-b1', '&#xE02C;'),
    '\uE02C': ('mod-b1', '&#xE02C;'),
    'K': ('mod-k', '&#xE02D;'),
    'k': ('mod-k', '&#xE02D;'),
    '⨯': ('mod-k', '&#xE02D;'),
    '\uE02D': ('mod-k', '&#xE02D;'),
    'F': ('mod-f', '&#x2577;'),
    'f': ('mod-f', '&#x2577;'),
    '╷': ('mod-f', '&#x2577;'),
    'G': ('mod-g', '&#xE003;'),
    'g': ('mod-g', '&#xE003;'),
    '\\': ('mod-g', '&#xE003;'),
    'H': ('mod-h', '&#xE00C;'),
    'h': ('mod-h', '&#xE00C;'),
    '|': ('mod-h', '&#xE00C;'),
    '.': ('mod-dot', '&#xE001;'),
    '_': ('mod-underbar', '&#xE007;'),
    ',': ('mod-comma', '&#xE00A;'),
}

MALAYALAM_SWARA_SUBS = {
    '𑌪𑍍𑌲': '&#xE020;',
    '𑌪𑍍𑌲𑌾': '&#xE021;',
    '𑌪𑍍𑌲𑌿': '&#xE022;',
    '𑌪𑍍𑌲𑍀': '&#xE023;',
    'ശ𑌾': '&#xE010;',
    'ശ𑌿': '&#xE011;',
    'ശ𑍀': '&#xE012;',
    'ശ്': '&#xE013;',
    'ത്ര': '&#xE01D;',
    'ക്ര': '&#xE01E;',
}

HTML_MOD_MAP = {
    'C': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    'c': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    '·': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    'ॱ': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    '़': ('mod-c', '&#xE001;', 'Upper Shoulder Dot (·)'),
    'H': ('mod-h', '&#xE00C;', 'High Pitch Swarita (|)'),
    'h': ('mod-h', '&#xE00C;', 'High Pitch Swarita (|)'),
    '|': ('mod-h', '&#xE00C;', 'High Pitch Swarita (|)'),
    'G': ('mod-g', '&#xE003;', 'Lower Under-Slash (\\)'),
    'g': ('mod-g', '&#xE003;', 'Lower Under-Slash (\\)'),
    '\\': ('mod-g', '&#xE003;', 'Lower Under-Slash (\\)'),
    'A': ('mod-a', '&#xE004;', 'Melodic Arc (⁀)'),
    'a': ('mod-a', '&#xE004;', 'Melodic Arc (⁀)'),
    '⁀': ('mod-a', '&#xE004;', 'Melodic Arc (⁀)'),
    'A1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'a1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'A_1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'a_1': ('mod-a1', '&#xE00D;', 'Arc over Danda'),
    'A2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'a2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'A_2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'a_2': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    '\uE02E': ('mod-a2', '&#xE02E;', 'Overhead Conjunct Arc'),
    'D': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    'd': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    '∧': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    'Ʌ': ('mod-d', '&#xE006;', 'Chevron Roof (∧)'),
    'D1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'd1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'D_1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'd_1': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    '↗': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    '\uE00E': ('mod-d1', '&#xE00E;', 'Rising Stroke (↗)'),
    'D2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'd2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'D_2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'd_2': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    '✓': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    '\uE00F': ('mod-d2', '&#xE00F;', 'Check Tick (✓)'),
    'I': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    'i': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    '⫽': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    '\uE02A': ('mod-i', '&#xE02A;', 'Double Shoulder Dash (⫽)'),
    'J': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    'j': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    '¯': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    '\uE02B': ('mod-j', '&#xE02B;', 'Overhead Horizontal Bar (¯)'),
    'B1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'b1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'B_1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'b_1': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    '/': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    '\uE02C': ('mod-b1', '&#xE02C;', 'Diagonal Bridging Slash (/)'),
    'K': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    'k': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    '⨯': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    '\uE02D': ('mod-k', '&#xE02D;', 'Shoulder Cross Mark (⨯)'),
    'B': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    'b': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    '^': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    '\uE005': ('mod-b', '&#xE005;', 'Peak Elevation Caret (∧)'),
    'E': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    'e': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    '┃': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    '\uE002': ('mod-e', '&#xE002;', 'Bold Tone Column (┃)'),
    'F': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    'f': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    '╷': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    '\uE008': ('mod-f', '&#xE008;', 'Danda with Overhead Dot (╷)'),
    '_': ('mod-under', '_', 'Underbar'),
    ',': ('mod-comma', ',', 'Comma'),
    '.': ('mod-dot', '.', 'Dot')
}
