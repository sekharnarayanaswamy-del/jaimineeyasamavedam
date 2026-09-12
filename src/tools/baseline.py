"""
Dataset Baselining and Traceability Manager for Jaimineeya Samaveda.

Provides automated manifest generation, checksum tracking, and baseline comparison
to ensure reproducibility across extended development gaps.
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINES_DIR = PROJECT_ROOT / "data" / "baselines"
VERSION_FILE = PROJECT_ROOT / "src" / "VERSION"

PRIMARY_INPUT_FILES = [
    "data/input/Samhita_corrected.txt",
    "data/input/Aaranam_latest.txt",
    "data/input/rishi_devata_chandas_for_rik.txt",
    "data/input/sama_rishi_chandas_out.txt",
]

PRIMARY_OUTPUT_FILES = [
    "data/output/Samhita_corrected_out.json",
    "data/output/Aaranam_latest_out.json",
    "data/output/JSV_Structure_Summary.csv",
    "data/output/JSV_Structure_Summary.txt",
]


def compute_sha256(filepath: Path) -> Optional[str]:
    """Computes SHA-256 hash of a file."""
    if not filepath.exists():
        return None
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_git_info() -> Dict[str, str]:
    """Retrieves current git commit, branch, and timestamp."""
    info = {"branch": "unknown", "commit": "unknown", "author_date": "unknown"}
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=PROJECT_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        author_date = subprocess.check_output(
            ["git", "log", "-1", "--format=%cd", "--date=iso"],
            cwd=PROJECT_ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
        info = {"branch": branch, "commit": commit, "author_date": author_date}
    except Exception:
        pass
    return info


def extract_domain_metrics() -> Dict[str, Any]:
    """Extracts summary metrics from current output files."""
    metrics = {"total_pathas": 0, "total_khandas": 0, "total_samas": 0}
    json_path = PROJECT_ROOT / "data" / "output" / "Samhita_corrected_out.json"
    if json_path.exists():
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                d = json.load(f)
            ss_dict = d.get("supersections", d.get("supersection", {}))
            metrics["total_pathas"] = len(ss_dict)
            khandas = sum(len(ss.get("sections", {})) for ss in ss_dict.values() if isinstance(ss, dict))
            metrics["total_khandas"] = khandas
            samas = 0
            for ss in ss_dict.values():
                if not isinstance(ss, dict): continue
                for sec in ss.get("sections", {}).values():
                    if not isinstance(sec, dict): continue
                    for sub in sec.get("subsections", {}).values():
                        if not isinstance(sub, dict): continue
                        mantras = sub.get("corrected-mantra_sets", [])
                        samas += max(len(mantras), 1 if sub.get("rik_text") else 0)
            metrics["total_samas"] = samas
        except Exception as e:
            metrics["error"] = str(e)
    return metrics


def create_baseline(tag: str, description: str = "") -> Path:
    """Creates a new baseline manifest snapshot."""
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    git_info = get_git_info()
    version = VERSION_FILE.read_text(encoding="utf-8").strip() if VERSION_FILE.exists() else "3.0"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_key = datetime.now().strftime("%Y%m%d_%H%M%S")

    inputs_meta = {}
    for rel_path in PRIMARY_INPUT_FILES:
        p = PROJECT_ROOT / rel_path
        if p.exists():
            inputs_meta[rel_path] = {
                "sha256": compute_sha256(p),
                "size_bytes": p.stat().st_size,
                "modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }

    outputs_meta = {}
    for rel_path in PRIMARY_OUTPUT_FILES:
        p = PROJECT_ROOT / rel_path
        if p.exists():
            outputs_meta[rel_path] = {
                "sha256": compute_sha256(p),
                "size_bytes": p.stat().st_size,
                "modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            }

    metrics = extract_domain_metrics()

    manifest = {
        "tag": tag,
        "description": description or f"Baseline snapshot for {tag}",
        "version": version,
        "timestamp": now_str,
        "git": git_info,
        "metrics": metrics,
        "inputs": inputs_meta,
        "outputs": outputs_meta
    }

    manifest_path = BASELINES_DIR / f"manifest_{timestamp_key}_{tag}.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Update LATEST.json
    latest_path = BASELINES_DIR / "LATEST.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # Regenerate README.md in baselines
    update_baselines_readme()

    print(f"[SUCCESS] Baseline '{tag}' recorded: {manifest_path.name}")
    print(f"          Git: {git_info['branch']} @ {git_info['commit']} | Version: {version}")
    print(f"          Metrics: {metrics['total_pathas']} Pathas, {metrics['total_khandas']} Khandas, {metrics['total_samas']} Samas")
    return manifest_path


def update_baselines_readme():
    """Generates human-readable summary of all historical baselines in data/baselines/README.md."""
    manifest_files = sorted(BASELINES_DIR.glob("manifest_*.json"))
    rows = []
    for mf in manifest_files:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            m = data.get("metrics", {})
            g = data.get("git", {})
            rows.append(
                f"| `{data.get('timestamp')}` | **{data.get('tag')}** | v{data.get('version')} | `{g.get('commit')}` | {m.get('total_samas', '-')} | {data.get('description', '')} |"
            )
        except Exception:
            continue

    readme_content = f"""# Jaimineeya Samaveda Dataset Baselines

This directory tracks immutable snapshots of canonical inputs, outputs, checksums, and metrics.
When resuming work after months, check `LATEST.json` or run `python src/tools/baseline.py status`.

## Historical Baselines

| Timestamp | Baseline Tag | Version | Commit | Total Samas | Description |
|---|---|---|---|---|---|
""" + "\n".join(rows) + "\n"

    readme_path = BASELINES_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)


def check_baseline_status():
    """Compares current workspace against LATEST baseline manifest."""
    latest_path = BASELINES_DIR / "LATEST.json"
    if not latest_path.exists():
        print("[INFO] No baseline snapshot found. Create one with: python src/tools/baseline.py create <tag>")
        return

    with open(latest_path, "r", encoding="utf-8") as f:
        base = json.load(f)

    print("\n" + "=" * 60)
    print(f"  ACTIVE BASELINE: {base.get('tag')} (Version {base.get('version')})")
    print(f"  Recorded: {base.get('timestamp')} on branch '{base.get('git', {}).get('branch')}' @ {base.get('git', {}).get('commit')}")
    print("=" * 60)

    # Check input files
    print("\n--- Input Files Status ---")
    inputs_ok = True
    for rel_path, meta in base.get("inputs", {}).items():
        p = PROJECT_ROOT / rel_path
        if not p.exists():
            print(f"  [MISSING] {rel_path}")
            inputs_ok = False
        else:
            curr_hash = compute_sha256(p)
            if curr_hash != meta.get("sha256"):
                print(f"  [MODIFIED] {rel_path} (changed since baseline)")
                inputs_ok = False
            else:
                print(f"  [MATCH]    {rel_path}")

    # Check output files
    print("\n--- Output Files Status ---")
    outputs_ok = True
    for rel_path, meta in base.get("outputs", {}).items():
        p = PROJECT_ROOT / rel_path
        if not p.exists():
            print(f"  [MISSING] {rel_path}")
            outputs_ok = False
        else:
            curr_hash = compute_sha256(p)
            if curr_hash != meta.get("sha256"):
                print(f"  [MODIFIED] {rel_path} (changed since baseline)")
                outputs_ok = False
            else:
                print(f"  [MATCH]    {rel_path}")

    # Check metrics
    curr_metrics = extract_domain_metrics()
    base_metrics = base.get("metrics", {})
    print("\n--- Domain Metrics ---")
    print(f"  Pathas : {curr_metrics.get('total_pathas')} (Baseline: {base_metrics.get('total_pathas')})")
    print(f"  Khandas: {curr_metrics.get('total_khandas')} (Baseline: {base_metrics.get('total_khandas')})")
    print(f"  Samas  : {curr_metrics.get('total_samas')} (Baseline: {base_metrics.get('total_samas')})")

    print("=" * 60 + "\n")


def list_baselines():
    """Lists all stored baselines."""
    manifest_files = sorted(BASELINES_DIR.glob("manifest_*.json"))
    if not manifest_files:
        print("[INFO] No historical baselines found in data/baselines/")
        return

    print("\nHistorical Baselines:")
    print(f"{'Timestamp':<20} {'Tag':<20} {'Version':<10} {'Commit':<10} {'Samas':<8} Description")
    print("-" * 80)
    for mf in manifest_files:
        try:
            with open(mf, "r", encoding="utf-8") as f:
                data = json.load(f)
            ts = data.get("timestamp", "")
            tag = data.get("tag", "")
            ver = data.get("version", "")
            cmt = data.get("git", {}).get("commit", "")
            samas = str(data.get("metrics", {}).get("total_samas", ""))
            desc = data.get("description", "")
            print(f"{ts:<20} {tag:<20} {ver:<10} {cmt:<10} {samas:<8} {desc}")
        except Exception:
            continue
    print("-" * 80 + "\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Jaimineeya Samaveda Dataset Baselining & Traceability Manager")
    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser("create", help="Create a new baseline snapshot")
    create_parser.add_argument("tag", help="Descriptive tag (e.g. baseline-sep2026, baseline-v3.28)")
    create_parser.add_argument("-d", "--description", default="", help="Optional description")

    subparsers.add_parser("status", help="Check status against the active baseline")
    subparsers.add_parser("list", help="List all historical baselines")

    args = parser.parse_args()
    if args.command == "create":
        create_baseline(args.tag, args.description)
    elif args.command == "status":
        check_baseline_status()
    elif args.command == "list":
        list_baselines()
    else:
        parser.print_help()
