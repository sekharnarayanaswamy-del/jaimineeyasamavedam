#!/usr/bin/env python3
"""
Jaimineeya Samavedam Static Website Generator - CLI Entry Point & Facade

This module provides the backward-compatible CLI entry point and re-exports
for the modular `src/website` package.

Design Reference: Based on https://hvram1.github.io/rigveda.sanatana.in/sukta/1/1/
Structural Hierarchy: Parva -> Kandah -> Sama
"""

import sys
import io
import argparse
from pathlib import Path
from datetime import datetime

# Setup module path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))
tools_dir = current_dir / 'tools'
if tools_dir.exists() and str(tools_dir) not in sys.path:
    sys.path.append(str(tools_dir))

# Re-export all public symbols from website package for 100% backward compatibility
from website import (
    Sama,
    Kandah,
    Parva,
    SITE_CONFIG,
    AUDIO_FILENAME_FORMAT,
    MALAYALAM_MODIFIER_MAP,
    HTML_MOD_MAP,
    JSVParser,
    WebsiteGenerator,
    format_rik_text_html,
    format_mantra_text_html,
    format_malayalam_mantra_html,
    generate_styles_css,
    generate_main_js,
    clean_text_for_search,
    strip_diacritics,
    transliterate_to_latin,
    generate_search_index_file,
    local_escape_for_html,
    local_replace_accents_html,
    local_process_footnotes_html,
    local_format_dandas_html,
    local_remove_mantra_spaces,
    local_handle_consecutive_trikamba,
    split_rik_lines_html,
    split_malayalam_clusters,
)

try:
    from utils import load_pipeline_config
except ImportError:
    try:
        from src.utils import load_pipeline_config
    except ImportError:
        def load_pipeline_config(): return {}


def main():
    """Main function to run the website generator"""
    pipeline_cfg = load_pipeline_config()
    web_cfg = pipeline_cfg.get('generate_website', {})

    parser = argparse.ArgumentParser(
        description='Jaimineeya Samavedam Website Generator (v2.0)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python generate_website.py --samhita
  python generate_website.py -a --source-file aranam.json
  python generate_website.py --samhita -kpully -o docs/kpully-devanagari
        '''
    )
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    default_source = project_root / 'data' / 'output' / 'Vargeekaran.json'
    default_output = project_root / 'docs'
    default_audio = project_root / 'data' / 'input' / 'Audio_Placeholders'
    
    parser.add_argument(
        '--source-file', '-s',
        type=str,
        default=None,
        help='Path to the source text file'
    )
    
    parser.add_argument(
        '--output_dir', '-o',
        type=str,
        default=None,
        help='Output directory for generated website'
    )
    
    parser.add_argument(
        '--audio-dir', '-d',
        type=str,
        default=None,
        help='Directory for audio placeholder folders'
    )
    
    # Mode selection group
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-m', '--samhita',
        action='store_true',
        help='Generate for Samhita'
    )
    group.add_argument(
        '-a', '--aaranam',
        action='store_true',
        help='Generate for Aaranam'
    )
    group.add_argument(
        '-c', '--collection',
        action='store_true',
        help='Generate for Collection (Jaimineeya Sama Sangraha)'
    )
    group.add_argument(
        '-ml', '--malayalam',
        action='store_true',
        help='Generate for Malayalam Samhita'
    )
    parser.add_argument(
        '--output-mode',
        type=str,
        choices=['combined', 'samam', 'rik', 'samam_nometa', 'rik_nometa', 'separate', 'nometa'],
        default=None,
        help='Content filtering mode: combined, samam, rik, samam_nometa, rik_nometa'
    )
    parser.add_argument(
        '--samam-only',
        action='store_true',
        help='Render only Samam chants'
    )
    parser.add_argument(
        '--rik-only',
        action='store_true',
        help='Render only Rik verses'
    )
    parser.add_argument(
        '-kpully', '--kpully',
        action='store_true',
        default=False,
        help='Enable Kodunthirapully swaras-above styling in Devanagari'
    )
    parser.add_argument(
        '--title',
        type=str,
        default=None,
        help='Custom title for collection mode (e.g., "जैमिनीय साम सङ्ग्रहः")'
    )
    parser.add_argument(
        '--font',
        type=str,
        default=None,
        help='Primary font for the website (default: AdishilaVedic)'
    )
    
    args = parser.parse_args()
    
    # Resolve output_mode
    output_mode = args.output_mode
    if not output_mode:
        if args.samam_only:
            output_mode = 'samam'
        elif args.rik_only:
            output_mode = 'rik'
        else:
            output_mode = 'combined'
    elif output_mode == 'separate':
        output_mode = 'rik' if args.rik_only else 'samam'
    elif output_mode == 'nometa':
        output_mode = 'rik_nometa' if args.rik_only else 'samam_nometa'

    # Determine mode: Priority CLI flags > Config
    if args.malayalam:
        mode = 'malayalam'
    elif args.aaranam:
        mode = 'aaranam'
    elif args.samhita:
        if args.kpully:
            mode = 'kpully_devanagari'
        elif output_mode == 'samam':
            mode = 'samhita_samam'
        elif output_mode == 'rik':
            mode = 'samhita_rik'
        elif output_mode == 'samam_nometa':
            mode = 'samhita_samam_nometa'
        elif output_mode == 'rik_nometa':
            mode = 'samhita_rik_nometa'
        else:
            mode = 'samhita'
    elif args.collection:
        mode = 'collection'
    else:
        mode = web_cfg.get('default_type', 'aaranam')

    type_cfg = web_cfg.get(mode, {})
    
    # Defaults for Malayalam mode
    if mode == 'malayalam':
        cand_ml_1 = project_root / 'data' / 'output' / 'malayalam' / 'Samhita_Malayalam.json'
        cand_ml_2 = project_root / 'data' / 'corpora' / 'samhita' / '02_ast' / 'Samam_Malayalam.json'
        cand_ml_3 = project_root / 'data' / 'output' / 'malayalam' / 'Samam_Malayalam.json'
        default_ml_source = cand_ml_1 if cand_ml_1.exists() else (cand_ml_2 if cand_ml_2.exists() else cand_ml_3)
        default_ml_output = project_root / 'docs' / 'malayalam'
        default_ml_audio = project_root / 'docs' / 'malayalam' / 'audio'
        source_file = args.source_file or type_cfg.get('source') or str(default_ml_source)
        output_dir = args.output_dir or type_cfg.get('output_dir') or str(default_ml_output)
        audio_dir = args.audio_dir or type_cfg.get('audio_dir') or str(default_ml_audio)
        font = args.font or type_cfg.get('font') or 'Noto Serif Malayalam'
        font_sans = 'Noto Sans Malayalam'
    else:
        cand_sam_canon = project_root / 'data' / 'corpora' / 'samhita' / '04_canonical' / 'Vargeekaran.json'
        effective_default_source = cand_sam_canon if cand_sam_canon.exists() else default_source
        source_file = args.source_file or type_cfg.get('source') or web_cfg.get('source') or str(effective_default_source)
        output_dir = args.output_dir or type_cfg.get('output_dir') or web_cfg.get('output_dir') or str(default_output)
        audio_dir = args.audio_dir or type_cfg.get('audio_dir') or web_cfg.get('audio_dir') or str(default_audio)
        font = args.font or type_cfg.get('font') or web_cfg.get('font') or 'AdishilaVedic'
        font_sans = 'AdishilaSanVedic'
    
    custom_title = args.title or type_cfg.get('title') or None
    
    source_path = Path(source_file)
    if not source_path.exists():
        print(f"[ERROR] Source file not found: {source_path}")
        return 1
    
    print("=" * 60)
    print("  Jaimineeya Samavedam Website Generator (v2.0)")
    print("  Design: Inspired by rigveda.sanatana.in")
    print("=" * 60)
    print(f"\n[INFO] Source file: {source_path}")
    print(f"[INFO] Output directory: {output_dir}")
    print(f"[INFO] Audio placeholders: {audio_dir}")
    print(f"[INFO] Mode: {mode.upper()}")
    print(f"[INFO] Output mode: {output_mode}")
    print(f"[INFO] KPully mode: {args.kpully}")
    print()
    
    print("[INFO] Parsing source file...")
    parser_obj = JSVParser(str(source_path))
    parvas = parser_obj.parse()
    
    total_kandahs = sum(len(p.kandahs) for p in parvas)
    total_samas = sum(sum(len(k.samas) for k in p.kandahs) for p in parvas)
    
    print(f"\n[STATS] Parsed Structure:")
    print(f"   - {len(parvas)} Parvas (Patha)")
    print(f"   - {total_kandahs} Kandahs (Khanda)")
    print(f"   - {total_samas} Samas (Sama)")
    
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    for parva in parvas:
        print(f"\n   {parva.parva_number}. {parva.title}")
        print(f"      └─ {len(parva.kandahs)} Kandahs, {sum(len(k.samas) for k in parva.kandahs)} Samas")
    
    print("\n[INFO] Generating website (Rig Veda style)...")
    generator = WebsiteGenerator(
        parvas,
        output_dir,
        audio_dir,
        mode=mode,
        custom_title=custom_title,
        font=font,
        metadata=parser_obj.metadata,
        closing_mantras=parser_obj.closing_mantras,
        output_mode=output_mode,
        kpully=args.kpully
    )
    generator.generate()
    
    # Automatically run search highlighting patcher across generated sub-sites
    try:
        from patch_highlight_js import run_patcher
        run_patcher()
    except ImportError:
        print("\n[WARNING] Could not find patch_highlight_js.py - skipping automatic patches.")
    
    print("\n" + "=" * 60)
    print("  Website generation complete!")
    print("=" * 60)
    print(f"\nOpen {output_dir}/index.html to view the website.")
    
    return 0


if __name__ == '__main__':
    exit(main())
