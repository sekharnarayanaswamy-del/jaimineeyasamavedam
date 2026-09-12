"""
Jaimineeya Samaveda - Automated 3-Tier Versioning & Build Metadata Module
-------------------------------------------------------------------------
Tier 1: Engine Version (Software SemVer + Git commit/dirty tag)
Tier 2: Corpus Editions (Independent editions for Samhita, Aaranam, Collections)
Tier 3: Content Fingerprint (SHA-256 hash of master input files)
"""

import os
import sys
import subprocess
import hashlib
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Union
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
    cfg = _load_config()
    if "editions" not in cfg:
        cfg["editions"] = {}
    cfg["editions"][normalized] = edition_str
    
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(cfg, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
        if normalized == "samhita":
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
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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
            parts[-1] = str(int(parts[-1]) + 1)
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
    
    parts = [f"Edition {edition}"]
    if engine:
        parts.append(f"Engine {engine}")
    elif commit and commit != "unknown":
        parts.append(f"git {commit}")
    if timestamp:
        parts.append(timestamp)
        
    return " · ".join(parts)

# Backward-compatibility helpers for legacy callers
def get_project_version() -> str:
    return get_corpus_edition("samhita")

def increment_project_version() -> str:
    return increment_corpus_edition("samhita")
