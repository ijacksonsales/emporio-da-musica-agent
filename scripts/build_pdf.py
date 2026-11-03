"""Build the submission PDF from the README and the docs (decision D16).

Markdown -> one HTML file (Mermaid diagrams rendered in the browser) -> PDF printed by a
headless Chromium browser (Chrome or Edge). The PDF always matches the repository content.

Usage: python scripts/build_pdf.py
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "dist"
PDF_NAME = (
    "Jackson Sales - AI Engineer – Full-Stack para Aplicações com IA Generativa - "
    "Vaga afirmativa para pessoas negras.pdf"
)

SOURCES = [
    "README.md",
    "docs/DECISION_LOG.md",
    "docs/ARCHITECTURE.md",
    "docs/DATA_AUDIT.md",
    "docs/SECURITY.md",
    "docs/RED_TEAM_RESULTS.md",
    *sorted(str(p.relative_to(ROOT)) for p in (ROOT / "examples").glob("*.md")),
]

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
    "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10.5pt;
       line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 20pt; border-bottom: 2px solid #e6007e; padding-bottom: 4px; }
h2 { font-size: 14pt; margin-top: 1.4em; }
h3 { font-size: 12pt; }
table { border-collapse: collapse; width: 100%; margin: 0.8em 0; font-size: 9pt; }
th, td { border: 1px solid #ccc; padding: 4px 6px; vertical-align: top; text-align: left; }
th { background: #f3f3f3; }
code { background: #f4f4f4; padding: 1px 3px; border-radius: 3px; font-size: 9pt; }
pre { background: #f4f4f4; padding: 8px; border-radius: 4px; overflow-x: hidden;
      white-space: pre-wrap; font-size: 8.5pt; }
pre.mermaid { background: none; text-align: center; }
blockquote { border-left: 3px solid #ccc; margin: 0.6em 0; padding: 0.2em 0.8em; color: #555; }
.doc { page-break-before: always; }
.doc:first-of-type { page-break-before: auto; }
.cover { text-align: center; padding-top: 30vh; page-break-after: always; }
.cover h1 { border: none; font-size: 26pt; }
"""


def find_browser() -> str:
    for candidate in BROWSERS:
        path = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if path:
            return path
    sys.exit("Chrome/Edge not found: install one or print dist/submission.html to PDF manually.")


def render(markdown_text: str) -> str:
    # Mermaid blocks become <pre class="mermaid"> so mermaid.js renders them.
    def mermaid(match: re.Match) -> str:
        return f'<pre class="mermaid">{html.escape(match.group(1))}</pre>'

    text = re.sub(r"```mermaid\n(.*?)```", mermaid, markdown_text, flags=re.S)
    return markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])


def build_html() -> str:
    docs = []
    for source in SOURCES:
        body = render((ROOT / source).read_text(encoding="utf-8"))
        docs.append(f'<section class="doc"><p><small>{source}</small></p>{body}</section>')
    cover = (
        '<section class="cover"><h1>Empório da Música<br>Customer Service Agent</h1>'
        "<p>Artefact — AI Engineer technical challenge</p>"
        "<p><strong>Jackson Sales</strong></p>"
        "<p>README and documentation</p></section>"
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Jackson Sales - AI Engineer</title>
<style>{CSS}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{ startOnLoad: true, theme: "neutral" }});</script>
</head><body>{cover}{''.join(docs)}</body></html>"""


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    html_path = OUT_DIR / "submission.html"
    html_path.write_text(build_html(), encoding="utf-8")
    pdf_path = OUT_DIR / PDF_NAME
    subprocess.run(
        [
            find_browser(),
            "--headless=new",
            "--disable-gpu",
            "--no-pdf-header-footer",
            "--virtual-time-budget=15000",  # let mermaid.js render before printing
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ],
        check=True,
        capture_output=True,
    )
    print(f"PDF written to {pdf_path}")


if __name__ == "__main__":
    main()
