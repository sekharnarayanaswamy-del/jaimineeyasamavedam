"""
Maintainer Status Dashboard for Jaimineeya Samaveda Pipeline.

Quick command to answer "Where did we leave off?" after gaps of weeks or months.
Displays active branch, latest commit, project version, active baseline status,
and recommended next commands.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.baseline import check_baseline_status, get_git_info, extract_domain_metrics
from utils import get_project_version

def print_maintainer_dashboard():
    git_info = get_git_info()
    version = get_project_version()
    metrics = extract_domain_metrics()

    print("\n" + "=" * 70)
    print("       JAIMINEEYA SAMAVEDA PIPELINE — MAINTAINER STATUS")
    print("=" * 70)
    print(f"  Branch        : {git_info.get('branch')}")
    print(f"  Head Commit   : {git_info.get('commit')} ({git_info.get('author_date')})")
    print(f"  Version (src) : {version}")
    print(f"  Canonical Samas: {metrics.get('total_samas')} across {metrics.get('total_pathas')} Pathas / {metrics.get('total_khandas')} Khandas")
    print("=" * 70)

    # Check baseline status
    check_baseline_status()

    print("--- Quick Pipeline Commands ---")
    print("  1. Verify Baseline Integrity : python src/tools/baseline.py status")
    print("  2. Create New Baseline       : python src/tools/baseline.py create <tag_name>")
    print("  3. Summary Verification      : python src/generate_json_summary.py")
    print("  4. Regenerate Website        : python src/generate_website.py")
    print("  5. Render Documents          : python src/render_pdf.py")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    print_maintainer_dashboard()
