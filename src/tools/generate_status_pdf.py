import os
import subprocess
from pathlib import Path

ROOT_DIR = Path(r"c:\Users\sekha\OneDrive\Documents\GitHub\jaimineeyasamavedam")
OUTPUT_DIR = ROOT_DIR / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

html_path = OUTPUT_DIR / "JSV_Refactoring_and_Manifest_Status_Report.html"
pdf_path = OUTPUT_DIR / "JSV_Refactoring_and_Manifest_Status_Report.pdf"

html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>JSV Pipeline Refactoring, Manifest Architecture & Data Bloat Audit</title>
<style>
  @page {
    size: A4 portrait;
    margin: 14mm 14mm 14mm 14mm;
  }

  * {
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1f2937;
    background: #ffffff;
    line-height: 1.42;
    font-size: 9pt;
    margin: 0;
    padding: 0;
  }

  .header {
    border-bottom: 2.5px solid #2563eb;
    padding-bottom: 8px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
  }

  .title-area h1 {
    font-size: 16pt;
    color: #1e3a8a;
    margin: 0 0 3px 0;
    font-weight: 700;
    letter-spacing: -0.02em;
  }

  .title-area .subtitle {
    font-size: 9pt;
    color: #4b5563;
    margin: 0;
    font-weight: 500;
  }

  .meta-box {
    text-align: right;
    font-size: 8pt;
    color: #6b7280;
    line-height: 1.35;
  }

  h2 {
    font-size: 11pt;
    color: #1e3a8a;
    border-left: 4px solid #2563eb;
    padding-left: 7px;
    margin: 12px 0 6px 0;
    font-weight: 700;
  }

  p {
    margin: 0 0 7px 0;
    color: #374151;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.2pt;
    margin: 6px 0 10px 0;
  }

  th {
    background-color: #f1f5f9;
    color: #1e293b;
    text-align: left;
    padding: 5px 7px;
    font-weight: 600;
    border: 1px solid #cbd5e1;
  }

  td {
    padding: 5px 7px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
  }

  tr:nth-child(even) td {
    background-color: #f8fafc;
  }

  .badge {
    display: inline-block;
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 7.2pt;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .badge-done { background: #dcfce7; color: #15803d; border: 1px solid #bbf7d0; }
  .badge-progress { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }
  .badge-planned { background: #e0e7ff; color: #4338ca; border: 1px solid #c7d2fe; }
  .badge-alert { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }

  .callout {
    background-color: #f0f9ff;
    border-left: 3.5px solid #0284c7;
    padding: 7px 11px;
    margin: 8px 0;
    border-radius: 0 4px 4px 0;
    font-size: 8.2pt;
    color: #0369a1;
  }

  .code-block {
    background: #0f172a;
    color: #f8fafc;
    font-family: "Cascadia Code", Consolas, Monaco, monospace;
    font-size: 7.6pt;
    padding: 7px 9px;
    border-radius: 5px;
    margin: 6px 0;
    line-height: 1.35;
    white-space: pre;
    overflow-x: hidden;
  }

  ul, ol {
    margin: 0 0 6px 0;
    padding-left: 17px;
  }

  li {
    margin-bottom: 2px;
  }

  .grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin: 6px 0;
  }

  .card {
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 8px 10px;
    background: #ffffff;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
  }

  .card-header {
    font-weight: 600;
    font-size: 8.7pt;
    color: #1e3a8a;
    margin-bottom: 5px;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 3px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .page-break {
    page-break-before: always;
  }

  .page-footer {
    display: flex;
    justify-content: space-between;
    font-size: 7.5pt;
    color: #9ca3af;
    border-top: 1px solid #e5e7eb;
    padding-top: 5px;
    margin-top: 10px;
  }
</style>
</head>
<body>

  <!-- ==================== PAGE 1 ==================== -->
  <div class="header">
    <div class="title-area">
      <h1>Jaimineeya Samavedam — System Architecture Report</h1>
      <div class="subtitle">Refactoring Status, Manifest Implementation &amp; Dataset Bloat Audit</div>
    </div>
    <div class="meta-box">
      <strong>Branch:</strong> refactor<br>
      <strong>Engine Version:</strong> v4.0.0+b71e07f8<br>
      <strong>Date:</strong> 23-September-2026<br>
      <strong>Corpora:</strong> Samhita &amp; Aaranam
    </div>
  </div>

  <p>
    This report provides a comprehensive status audit of the ongoing architectural refactoring specified in
    <code>src/tools/refactoring_spec.md</code>. It assesses current milestones completed across core domain models,
    evaluates the state of the dataset baselining and manifest systems, details the extent of flat-file sprawl
    in <code>data/input/</code> and <code>data/output/</code>, and outlines the concrete transition path to the
    <strong>Two-Manifest Architecture</strong> and <strong>Stage-Numbered Corpus Structure</strong>.
  </p>

  <h2>1. Status of the Refactoring Roadmap</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 17%;">Phase</th>
        <th style="width: 25%;">Scope &amp; Deliverables</th>
        <th style="width: 13%;">Status</th>
        <th style="width: 45%;">Accomplished &amp; Pending Tasks</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>Phase 1: Core Domain &amp; Swara Engine</strong></td>
        <td>AST models (<code>models.py</code>), Swara logic (<code>swara_engine.py</code>), tokenization, regression tests.</td>
        <td><span class="badge badge-done">Completed</span></td>
        <td>
          Unified Pydantic AST models implemented. <code>tokenize_mantra_line</code>, <code>WORD_RE</code>, swara whitespace normalization, and Visarga order fixes centralized in <code>src/core/swara_engine.py</code>. Architectural inversion between <code>render_pdf.py</code> and <code>src/malayalam/ml_text.py</code> resolved. 8/8 invariant checks passing in regression test suite.
        </td>
      </tr>
      <tr>
        <td><strong>Phase 2: Renderer Modularization</strong></td>
        <td>Decompose <code>render_pdf.py</code> (4,800+ LOC) into discrete engines: LaTeX, HTML, Plaintext, and Jinja filters.</td>
        <td><span class="badge badge-progress">Scaffolded</span></td>
        <td>
          <code>src/renderers/</code> sub-package created (<code>base_renderer.py</code>, <code>latex_renderer.py</code>, <code>html_renderer.py</code>, <code>text_renderer.py</code>). However, monolithic <code>render_pdf.py</code> remains the primary active generator because legacy footnote rules, accents, and 25+ filters are still being decoupled.
        </td>
      </tr>
      <tr>
        <td><strong>Phase 3: Baraha Purge &amp; Decoupling</strong></td>
        <td>Retire external experimental Baraha DOCX readers and isolate pure Jaimineeya pipeline.</td>
        <td><span class="badge badge-done">Completed</span></td>
        <td>
          External Baraha DOCX workflows migrated to dedicated external repositories (VedaVMS). Core pipeline code exclusively handles canonical Jaimineeya inputs.
        </td>
      </tr>
      <tr>
        <td><strong>Phase 4: Universal HTML Viewer &amp; Site Sync</strong></td>
        <td>Abstract responsive web reader (Suchi TOC drawer, swara alignment, mobile orientations) and sync with static site.</td>
        <td><span class="badge badge-progress">In Progress</span></td>
        <td>
          61 standalone HTML readers updated with high-performance scroll-spy, sticky TOC anchoring, and zero-flicker viewport rotation. Static site generator in <code>docs/</code> actively synchronized.
        </td>
      </tr>
      <tr>
        <td><strong>Phase 5: Baselining &amp; Invariants</strong></td>
        <td>Immutable dataset snapshots, invariant validation suite, and continuity verification.</td>
        <td><span class="badge badge-progress">Partially Done</span></td>
        <td>
          <code>src/tools/baseline.py</code> and <code>data/baselines/LATEST.json</code> created. Verified golden outputs recorded for Samhita v3.28. Full Two-Manifest dynamic reconciliation workflow still pending.
        </td>
      </tr>
      <tr>
        <td><strong>Phase 6: 3-Tier Versioning</strong></td>
        <td>Decouple software engine version, corpus edition strings, and SHA-256 data fingerprints.</td>
        <td><span class="badge badge-done">Completed</span></td>
        <td>
          <code>src/core/version.py</code> implemented with git-derived tags, corpus editions in <code>pipeline_config.yaml</code>, and automated cryptographic fingerprints.
        </td>
      </tr>
    </tbody>
  </table>

  <div class="page-footer">
    <span>Jaimineeya Samavedam System Architecture</span>
    <span>Page 1 of 3</span>
  </div>

  <!-- ==================== PAGE 2 ==================== -->
  <div class="page-break"></div>

  <h2>2. Dataset Manifests: Current Implementation vs. Target Spec</h2>
  <div class="grid-2">
    <div class="card">
      <div class="card-header">
        <span>Current State: Monolithic Snapshot</span>
        <span class="badge badge-progress">Partial</span>
      </div>
      <p>Implemented in <code>src/tools/baseline.py</code> and <code>data/baselines/LATEST.json</code>:</p>
      <ul>
        <li>Tracks flat file checksums for primary inputs and outputs.</li>
        <li>Records git branch, commit hash, and aggregate domain metrics (6 Pathas, 59 Khandas, 722/1226 Samas).</li>
        <li><strong>Bottleneck (Alert Fatigue):</strong> When a maintainer fixes a single typo or swara in <code>Samhita_corrected.txt</code>, the hash mismatches and flags a red violation, failing to differentiate between intended editorial curation and code bugs.</li>
      </ul>
    </div>
    <div class="card">
      <div class="card-header">
        <span>Target State: Two-Manifest Architecture</span>
        <span class="badge badge-planned">Specification</span>
      </div>
      <p>Designed in <code>refactoring_spec.md</code> (Subsystem E):</p>
      <ul>
        <li><strong>Golden Baseline Anchor</strong> (<code>data/baselines/golden/</code>): Immutable verified ground truth for each major release.</li>
        <li><strong>Active Run Manifest</strong> (<code>data/corpora/&lt;corpus&gt;/run_manifest.json</code>): Working draft manifest recording build stages and verse-level change diffs.</li>
        <li><strong>Dual-Track Validator (<code>validate_run.py</code>)</strong>:
          <ol style="margin-left: 13px; padding-left: 0;">
            <li><em>Track A (Engine Invariance):</em> Re-runs baseline input to guarantee 100% byte parity against golden output.</li>
            <li><em>Track B (Semantic Diff):</em> Compares Active AST against Golden AST to confirm only target verses changed while all 59 Khandas remain structurally intact.</li>
          </ol>
        </li>
      </ul>
    </div>
  </div>

  <h2>3. Comprehensive Data Bloat Audit</h2>
  <p>
    Over months of liturgical editing, automated pipelines and manual reconciliation passes accumulated redundant
    files directly into the root directories of <code>data/input/</code> and <code>data/output/</code>.
  </p>

  <div class="grid-2">
    <div class="card">
      <div class="card-header">
        <span><code>data/input/</code> Sprawl (44 Files, ~25 MB)</span>
        <span class="badge badge-alert">Bloat Detected</span>
      </div>
      <ul>
        <li><strong>Redundant Copy Duplicates:</strong>
          <ul>
            <li><code>Aaranam_latest - Copy (2).txt</code> (409 KB)</li>
            <li><code>Aaranam_latest - Copy.txt</code> (408 KB)</li>
            <li><code>Aaranam_latest_.txt</code> (495 KB)</li>
            <li><code>Agneyam-Pavamanam_corrected.txt</code> vs <code>Agneyam-Pavamanam_latest.txt</code></li>
          </ul>
        </li>
        <li><strong>Heavy Editorial Workbooks in Input:</strong>
          <ul>
            <li><code>veda_anukriti - Jitendra Bansal.xlsx</code> (<strong>10.6 MB</strong>)</li>
            <li><code>Samved-RDC_.xlsx</code> (<strong>3.1 MB</strong>)</li>
          </ul>
        </li>
        <li><strong>Temporary OS / Office Lock Files:</strong>
          <ul>
            <li><code>~$veda_anukriti - Jitendra Bansal.xlsx</code> (165 bytes)</li>
          </ul>
        </li>
        <li><strong>Ad-Hoc / Scratch Input Files:</strong>
          <ul>
            <li><code>broken_test.txt</code>, <code>section_list.txt</code></li>
          </ul>
        </li>
      </ul>
    </div>

    <div class="card">
      <div class="card-header">
        <span><code>data/output/</code> Sprawl (222 Files + 9 Subdirs, ~100+ MB)</span>
        <span class="badge badge-alert">Severe Bloat</span>
      </div>
      <ul>
        <li><strong>Scratch &amp; One-Off Generation Runs:</strong>
          <ul>
            <li><code>1.txt</code> (488 KB)</li>
            <li><code>Aaranam_test_renum.txt</code>, <code>Aaranam_test_renum_v2.txt</code></li>
            <li><code>Aaranam_config_test.txt</code></li>
            <li><code>sep_test_*</code> (6 files: HTML, TeX, PDF totaling ~15 MB)</li>
            <li><code>test_logic_*</code> (HTML, TeX totaling ~10 MB)</li>
          </ul>
        </li>
        <li><strong>Redundant AST Snapshots:</strong>
          <ul>
            <li><code>Samhita_corrected_out.json</code> (1.8 MB)</li>
            <li><code>Samhita_Devanagari_Unicode_out.json</code> (1.8 MB)</li>
            <li><code>Samhita_with_Rishi_Devata_Chandas_out.json</code> (1.8 MB)</li>
            <li><code>Samhita_with_vargekaran.json</code> (1.5 MB)</li>
            <li><code>Vargeekaran_latest.json</code> (2.3 MB) vs <code>Vargeekaran-bak.json</code></li>
          </ul>
        </li>
        <li><strong>Overlapping Excel Reconciliation Runs:</strong>
          <ul>
            <li>5 variations of <code>Rik Reconciliation table (JSV-KSV)*.xlsx</code>.</li>
            <li>Multiple temporary lock files: <code>~$*.xlsx</code>.</li>
          </ul>
        </li>
      </ul>
    </div>
  </div>

  <div class="page-footer">
    <span>Jaimineeya Samavedam System Architecture</span>
    <span>Page 2 of 3</span>
  </div>

  <!-- ==================== PAGE 3 ==================== -->
  <div class="page-break"></div>

  <h2>4. Stage-Numbered Corpus Architecture (`data/corpora/`)</h2>
  <p>
    To permanently resolve the bloat and maintain clear lineage across multi-month gaps, all active assets
    must be reorganized into stage-numbered directories per corpus, with stale files moved to <code>data/archive/</code>:
  </p>

  <div class="code-block">data/corpora/
├── samhita/
│   ├── 01_input/           # Single source of truth: Samhita_corrected.txt
│   ├── 02_ast/             # Normalized JSON AST: Samhita_ast.json
│   ├── 03_reconciliation/  # Human workbooks: JSV_KSV_Recon.xlsx, Rishi/Devata/Chandas tables
│   ├── 04_canonical/       # Enriched AST: Vargeekaran.json (Canonical 1226 Samas)
│   ├── 05_renders/         # Build outputs: PDF, TXT, standalone HTML readers
│   ├── 06_reports/         # Continuity logs, structure metrics, reconciliation diffs
│   └── run_manifest.json   # Working Run Manifest (Stage status, modified verse count)
├── aaranam/
│   ├── 01_input/           # Single source of truth: Aaranam_latest.txt
│   ├── 02_ast/             # Normalized JSON AST: Aaranam_ast.json
│   ├── 03_reconciliation/  # Aaranam Rik & Samam tables
│   ├── 04_canonical/       # Aaranam_vargeekaran.json
│   ├── 05_renders/         # Formatted outputs (PDF, HTML, TXT)
│   ├── 06_reports/         # Aaranam continuity reports
│   └── run_manifest.json   # Working Run Manifest
└── collections/            # Sooktamala & Prayogamala curated corpora
data/archive/
└── legacy_2026/            # Deprecated copies, scratch test runs (*.bak, sep_test_*, 1.txt, etc.)</div>

  <h2>5. Recommended Immediate Action Plan</h2>
  <ol>
    <li>
      <strong>Execute Stage 1 Archival Purge:</strong> Safely sweep all office lock files (<code>~$*.xlsx</code>), scratch test runs (<code>sep_test_*</code>, <code>test_logic_*</code>, <code>1.txt</code>), and redundant duplicate copy files (<code>* - Copy*</code>) into <code>data/archive/legacy_2026/</code>.
    </li>
    <li>
      <strong>Establish <code>data/corpora/</code> Stage Hierarchy:</strong> Initialize directories for <code>samhita</code> and <code>aaranam</code>, placing single canonical files in their designated <code>01_input</code> through <code>04_canonical</code> folders.
    </li>
    <li>
      <strong>Deploy Two-Manifest Engine (<code>src/tools/validate_run.py</code>):</strong>
      Implement the dual-track validator to verify code-engine invariance (Track A) and semantic verse-level diffs (Track B), enabling confident promote operations via <code>python src/tools/baseline.py promote &lt;corpus&gt;</code>.
    </li>
    <li>
      <strong>Complete Renderer Decomposition:</strong> Migrate the remaining Jinja filters and footnote layout macros out of monolithic <code>render_pdf.py</code> into <code>src/renderers/</code>.
    </li>
  </ol>

  <div class="callout">
    <strong>Conclusion:</strong> The foundational engineering (Core Domain, Swara Engine, 3-Tier Versioning, Invariant Suite) is complete and verified. The primary operational next step is transitioning from flat file directories to the structured <code>data/corpora/</code> hierarchy and implementing the Two-Manifest reconciliation workflow.
  </div>

  <div class="page-footer">
    <span>Jaimineeya Samavedam System Architecture</span>
    <span>Page 3 of 3</span>
  </div>

</body>
</html>
"""

html_path.write_text(html_content, encoding="utf-8")
print(f"[1/2] Wrote HTML report to: {html_path}")

edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(edge_path):
    edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

cmd = [
    edge_path,
    "--headless",
    "--disable-gpu",
    "--no-pdf-header-footer",
    "--run-all-compositor-stages-before-draw",
    f"--print-to-pdf={pdf_path}",
    str(html_path)
]

print(f"[2/2] Compiling PDF via Headless Edge...")
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0 and pdf_path.exists():
    print(f"[SUCCESS] PDF successfully created: {pdf_path} ({pdf_path.stat().st_size} bytes)")
else:
    print(f"[ERROR] Failed to compile PDF: {res.stderr}")
