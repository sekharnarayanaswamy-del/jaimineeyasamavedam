"""
Jaimineeya Samaveda - Automated 3-Tier Versioning & Build Metadata Module
-------------------------------------------------------------------------
Tier 1: Engine Version (Software SemVer + Git commit/dirty tag)
Tier 2: Corpus Editions (Independent editions for Samhita, Aaranam, Collections)
Tier 3: Content Fingerprint (SHA-256 hash of master input files)
"""

import os
import sys
import re
import subprocess
import hashlib
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union, Tuple
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_FILE = REPO_ROOT / "src" / "pipeline_config.yaml"
VERSION_FILE = REPO_ROOT / "src" / "VERSION"

def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}

def get_git_info() -> Dict[str, Any]:
    """Retrieves current Git status, commit hash, branch, and dirty flag."""
    info = {
        "is_git": False,
        "commit": "unknown",
        "branch": "unknown",
        "is_dirty": False,
        "describe": "unknown"
    }
    try:
        # Check if inside git work tree
        in_tree = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if in_tree.returncode != 0:
            return info
            
        info["is_git"] = True
        
        # Short commit
        commit_proc = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if commit_proc.returncode == 0:
            info["commit"] = commit_proc.stdout.strip()
            
        # Branch name
        branch_proc = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if branch_proc.returncode == 0:
            info["branch"] = branch_proc.stdout.strip()
            
        # Dirty check
        status_proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3
        )
        if status_proc.returncode == 0:
            info["is_dirty"] = bool(status_proc.stdout.strip())
            
        # Describe
        desc_proc = subprocess.run(
            ["git", "describe", "--tags", "--always", "--dirty"],
            cwd=str(REPO_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if desc_proc.returncode == 0:
            info["describe"] = desc_proc.stdout.strip()
            
    except Exception:
        pass
        
    return info

def get_engine_version() -> str:
    """Tier 1: Returns engine semantic version string, augmented with git metadata."""
    cfg = _load_config()
    base_engine = cfg.get("project", {}).get("engine_version", "4.0.0")
    git = get_git_info()
    if git["is_git"] and git["commit"] != "unknown":
        dirty_suffix = "-dirty" if git["is_dirty"] else ""
        return f"v{base_engine}+{git['commit']}{dirty_suffix}"
    return f"v{base_engine}"

def get_corpus_edition(corpus_name: str = "samhita") -> str:
    """Tier 2: Returns the edition string for a specific corpus."""
    normalized = corpus_name.lower().strip()
    aliases = {
        "collection": "collections",
        "purva": "purvarchikam",
        "uttara": "uttararchikam",
        "malayalam": "kpully"
    }
    normalized = aliases.get(normalized, normalized)
    cfg = _load_config()
    editions = cfg.get("editions", {})
    if normalized in editions:
        return str(editions[normalized]).strip()
        
    # Fallback to src/VERSION if samhita or unspecified
    if VERSION_FILE.exists():
        try:
            return VERSION_FILE.read_text(encoding='utf-8').strip()
        except Exception:
            pass
            
    return cfg.get("project", {}).get("version", "3.0")

def set_corpus_edition(corpus_name: str, edition_str: str) -> bool:
    """Updates the corpus edition in pipeline_config.yaml (and src/VERSION for samhita)."""
    normalized = corpus_name.lower().strip()
    aliases = {
        "collection": "collections",
        "purva": "purvarchikam",
        "uttara": "uttararchikam",
        "malayalam": "kpully"
    }
    normalized = aliases.get(normalized, normalized)
    try:
        if CONFIG_FILE.exists():
            content = CONFIG_FILE.read_text(encoding='utf-8')
            # Restrict replacement strictly to the editions block
            ed_match = re.search(r'(^editions\s*:\s*\r?\n(?:[ ]+.*\r?\n)*)', content, re.MULTILINE)
            if ed_match:
                ed_block = ed_match.group(1)
                pattern = re.compile(rf'(^[ ]+{re.escape(normalized)}\s*:\s*)["\']?[^"\'\r\n]+["\']?', re.MULTILINE)
                if pattern.search(ed_block):
                    new_ed_block = pattern.sub(rf'\g<1>"{edition_str}"', ed_block, count=1)
                    content = content[:ed_match.start(1)] + new_ed_block + content[ed_match.end(1):]
                    CONFIG_FILE.write_text(content, encoding='utf-8')
                else:
                    new_ed_block = ed_block.rstrip() + f'\n  {normalized}: "{edition_str}"\n'
                    content = content[:ed_match.start(1)] + new_ed_block + content[ed_match.end(1):]
                    CONFIG_FILE.write_text(content, encoding='utf-8')
            else:
                cfg = _load_config()
                if "editions" not in cfg:
                    cfg["editions"] = {}
                cfg["editions"][normalized] = edition_str
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        if normalized == "samhita" and VERSION_FILE.exists():
            VERSION_FILE.write_text(edition_str, encoding='utf-8')
        return True
    except Exception as e:
        print(f"[WARNING] Failed to set corpus edition: {e}")
        return False

def get_file_hash(file_path: Union[str, Path]) -> Optional[str]:
    """Tier 3: Computes SHA-256 fingerprint of a given file."""
    path = Path(file_path)
    if not path.is_absolute():
        path = REPO_ROOT / path
    if not path.exists():
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def get_build_metadata(
    corpus_name: str = "samhita",
    input_file: Optional[Union[str, Path]] = None,
    increment: bool = False
) -> Dict[str, Any]:
    """
    Constructs comprehensive 3-tier build metadata.
    Backward-compatible with legacy scripts expecting 'version' and 'generated_at'.
    """
    if increment:
        increment_corpus_edition(corpus_name)
        
    edition = get_corpus_edition(corpus_name)
    engine = get_engine_version()
    git = get_git_info()
    now_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    file_sha = None
    if input_file:
        file_sha = get_file_hash(input_file)
        
    meta = {
        # Legacy backward-compatibility keys
        "version": edition,
        "generated_at": now_str,
        
        # 3-Tier Metadata
        "corpus": corpus_name,
        "edition": edition,
        "engine_version": engine,
        "git_commit": git["commit"],
        "git_branch": git["branch"],
        "is_dirty": git["is_dirty"],
        "git_describe": git["describe"],
        "input_file": str(input_file) if input_file else None,
        "input_sha256": file_sha
    }
    return meta

def increment_corpus_edition(corpus_name: str = "samhita") -> str:
    """Safely increments the patch version for a specific corpus."""
    current = get_corpus_edition(corpus_name)
    try:
        parts = current.split('.')
        if len(parts) >= 2:
            width = len(parts[-1])
            new_val = int(parts[-1]) + 1
            parts[-1] = f"{new_val:0{width}d}"
            new_edition = ".".join(parts)
        else:
            new_edition = current + ".1"
        set_corpus_edition(corpus_name, new_edition)
        return new_edition
    except Exception as e:
        print(f"[WARNING] Failed to increment corpus edition: {e}")
        return current

def format_build_stamp(meta: Dict[str, Any]) -> str:
    """Formats a concise human-readable build stamp for footers and summaries."""
    edition = meta.get("edition") or meta.get("version", "unknown")
    engine = meta.get("engine_version", "")
    commit = meta.get("git_commit", "")
    timestamp = meta.get("generated_at", "")
    if timestamp:
        timestamp = re.sub(r'\b(\d{4})-(\d{2})-(\d{2})\b', r'\3-\2-\1', str(timestamp))
    
    parts = [f"Edition {edition}"]
    if engine:
        parts.append(f"Engine {engine}")
    elif commit and commit != "unknown":
        parts.append(f"git {commit}")
    if timestamp:
        parts.append(timestamp)
        
    return " · ".join(parts)

def check_and_auto_increment_edition(corpus_name: str = "samhita", input_file: Optional[Union[str, Path]] = None) -> Tuple[str, bool]:
    """
    Checks if the SHA-256 fingerprint of the input file has changed since the last manifest run.
    If changed (input updated in correction workflow), automatically increments the patch edition version.
    Returns (current_or_new_edition, was_incremented).
    """
    edition = get_corpus_edition(corpus_name)
    if not input_file:
        return edition, False

    input_path = Path(input_file)
    if not input_path.is_absolute():
        input_path = REPO_ROOT / input_path
    if not input_path.exists():
        return edition, False

    current_hash = get_file_hash(input_path)
    if not current_hash:
        return edition, False

    normalized = corpus_name.lower().strip()
    folder_map = {
        "collection": "collections",
        "purva": "Rik",
        "purvarchikam": "Rik",
        "uttara": "Rik",
        "uttararchikam": "Rik",
        "rik": "Rik",
    }
    corpus_folder = folder_map.get(normalized, normalized)

    manifest_path = REPO_ROOT / "data" / "corpora" / corpus_folder / "run_manifest.json"
    stored_hash = None
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            # Try to match the exact input file name in artifacts["01_input"]
            for art in manifest_data.get("artifacts", {}).get("01_input", []):
                if art.get("name") == input_path.name:
                    stored_hash = art.get("sha256")
                    break
            # Fall back to root input_sha256 if not found by name
            if not stored_hash:
                stored_hash = manifest_data.get("hashes", {}).get("input_sha256")
        except Exception:
            pass

    if stored_hash and current_hash != stored_hash:
        new_edition = increment_corpus_edition(corpus_name)
        if corpus_folder == "Rik":
            set_corpus_edition("rik", new_edition)
            set_corpus_edition("purvarchikam", new_edition)
            set_corpus_edition("uttararchikam", new_edition)
        # Update manifest in place so subsequent calls in the same pipeline run do not double-increment
        try:
            if manifest_path.exists():
                with open(manifest_path, "r", encoding="utf-8") as f:
                    m_data = json.load(f)
                if "hashes" not in m_data:
                    m_data["hashes"] = {}
                m_data["hashes"]["input_sha256"] = current_hash
                for art in m_data.get("artifacts", {}).get("01_input", []):
                    if art.get("name") == input_path.name:
                        art["sha256"] = current_hash
                with open(manifest_path, "w", encoding="utf-8") as f:
                    json.dump(m_data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        print(f"[AUTO-VERSION] Input file '{input_path.name}' changed for '{corpus_name}'. Incremented edition: {edition} -> {new_edition}")
        return new_edition, True

    return edition, False


# Backward-compatibility helpers for legacy callers
def get_project_version() -> str:
    return get_corpus_edition("samhita")

def increment_project_version() -> str:
    return increment_corpus_edition("samhita")

