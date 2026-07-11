#!/usr/bin/env python3
"""
generate_pdf.py
Generates a one-page-per-project PDF portfolio from projects.json.

Usage:
    python generate_pdf.py
    python generate_pdf.py --output path/to/output.pdf
    python generate_pdf.py --json path/to/projects.json

Requirements (Python 3.10+):
    pip install weasyprint requests
"""

import json
import sys
import argparse
import base64
from pathlib import Path

# ---------------------------------------------------------------------------
# Dependency check
# ---------------------------------------------------------------------------

try:
    import requests
    from weasyprint import HTML
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install weasyprint requests")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent.resolve()

# ---------------------------------------------------------------------------
# Image utilities
# ---------------------------------------------------------------------------

def image_to_data_uri(path_or_url: str) -> str | None:
    """
    Fetch a local file or URL and return a base64 data URI.
    Returns None on failure (warning is printed).
    """
    MIME = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".gif": "image/gif",
        ".webp": "image/webp",
    }

    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        try:
            r = requests.get(path_or_url, timeout=12)
            r.raise_for_status()
            ct = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            data = base64.b64encode(r.content).decode()
            return f"data:{ct};base64,{data}"
        except Exception as exc:
            print(f"  ⚠ Could not fetch image: {path_or_url} ({exc})")
            return None
    else:
        full = SCRIPT_DIR / path_or_url
        if not full.exists():
            print(f"  ⚠ Image not found: {full}")
            return None
        ct = MIME.get(full.suffix.lower(), "image/jpeg")
        data = base64.b64encode(full.read_bytes()).decode()
        return f"data:{ct};base64,{data}"


def youtube_url(video_id: str) -> str:
    return f"https://youtube.com/watch?v={video_id}"


def vimeo_url(video_id: str) -> str:
    return f"https://vimeo.com/{video_id}"


# ---------------------------------------------------------------------------
# HTML helpers
# ---------------------------------------------------------------------------

def esc(text: str) -> str:
    return (str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))


def paragraphs(text: str) -> str:
    import re
    result = []
    for p in text.split("\n\n"):
        p = p.strip()
        if not p:
            continue
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', esc(p))
        result.append(f"<p>{html}</p>")
    return "".join(result)


# ---------------------------------------------------------------------------
# Per-project page
# ---------------------------------------------------------------------------

def render_project_page(proj: dict, index: int, portfolio: dict) -> str:
    annotation = f"P.{index + 1:03d}"
    title      = proj.get("title", "Untitled")
    date       = proj.get("date", "")
    tags       = proj.get("tags", [])
    description = proj.get("description") or proj.get("summary") or ""
    hero_src   = proj.get("hero")
    media_items = proj.get("media", [])
    links      = proj.get("links", {})
    owner      = portfolio.get("name", "")
    linkedin   = portfolio.get("linkedin", "")

    print(f"  [{index + 1}] {title}")

    # --- Hero ---
    hero_html = ""
    if hero_src:
        uri = image_to_data_uri(hero_src)
        if uri:
            hero_html = f'<img class="hero-img" src="{uri}" alt="{esc(title)}" />'

    # --- Media grid (up to 4 items; skip if it's the hero image) ---
    media_cells = []
    for item in media_items:
        if len(media_cells) >= 4:
            break

        itype   = item.get("type")
        caption = item.get("caption", "")
        cap_html = f'<p class="caption">{esc(caption)}</p>' if caption else ""

        if itype == "image":
            # Skip if already used as hero
            if item.get("src") == hero_src:
                continue
            uri = image_to_data_uri(item["src"])
            if uri:
                media_cells.append(f'''
<div class="media-cell">
  <img src="{uri}" alt="{esc(caption)}" />
  {cap_html}
</div>''')

        elif itype == "youtube":
            vid_id    = item.get("id", "")
            watch_url = youtube_url(vid_id)
            # No thumbnail, no QR — just a styled link block
            media_cells.append(f'''
<div class="media-cell video-cell">
  {cap_html}
  <p class="video-url">{esc(watch_url)}</p>
</div>''')

        elif itype == "vimeo":
            vid_id    = item.get("id", "")
            watch_url = vimeo_url(vid_id)
            media_cells.append(f'''
<div class="media-cell video-cell">
  {cap_html}
  <p class="video-url">{esc(watch_url)}</p>
</div>''')

    media_html = ""
    if media_cells:
        cells_html = "\n".join(media_cells)
        media_html = f'<div class="media-grid">{cells_html}</div>'

    # --- Links: show label + plain URL text (no QR) ---
    LINK_LABELS = {
        "github": "GitHub ↗", "demo": "Live Demo ↗", "video": "Video ↗",
        "paper": "Paper ↗",  "report": "Report ↗",  "website": "Website ↗",
    }
    active_links = [(LINK_LABELS.get(k, f"{k} ↗"), v) for k, v in links.items() if v]
    links_html = ""
    if active_links:
        btn_html = "".join(
            f'<span class="link-btn">{esc(label)}&nbsp;&nbsp;<span class="link-url">{esc(url)}</span></span>'
            for label, url in active_links
        )
        links_html = f'<div class="links-row">{btn_html}</div>'

    # --- Tags ---
    tags_html = "".join(f'<span class="tag">{esc(t)}</span>' for t in tags)

    # --- Description ---
    desc_html = paragraphs(description)

    return f'''
<div class="project-page">

  <!-- Page header -->
  <div class="page-header">
    <span class="annotation">{annotation}</span>
    <span class="owner-name">{esc(owner)}</span>
  </div>

  <!-- Title block -->
  <div class="date-line">{esc(date)}</div>
  <h1 class="title">{esc(title)}</h1>
  <div class="tags-row">{tags_html}</div>

  <!-- Hero -->
  {hero_html}

  <!-- Description -->
  <div class="description">{desc_html}</div>

  <!-- Media -->
  {media_html}

  <!-- Links -->
  {links_html}

  <!-- Page footer -->
  <div class="page-footer">
    <span>{esc(owner)} — Portfolio</span>
    <span>{esc(linkedin)}</span>
  </div>

</div>
'''


# ---------------------------------------------------------------------------
# PDF CSS (WeasyPrint-compatible)
# ---------------------------------------------------------------------------

PDF_CSS = """
@page {
  size: A4;
  margin: 0;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 9pt;
  color: #111;
  background: white;
}

/* ---- Page wrapper ---- */
.project-page {
  width: 210mm;
  height: 297mm;
  padding: 15mm 18mm 13mm;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: white;
  page-break-after: always;
}

/* ---- Page header ---- */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 0.4pt solid #111;
  padding-bottom: 7pt;
  margin-bottom: 11pt;
  flex-shrink: 0;
}

.annotation, .owner-name {
  font-family: 'Courier New', Courier, monospace;
  font-size: 6.5pt;
  letter-spacing: 0.1em;
  color: #888;
}

/* ---- Title block ---- */
.date-line {
  font-family: 'Courier New', Courier, monospace;
  font-size: 6.5pt;
  color: #999;
  margin-bottom: 4pt;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.title {
  font-size: 24pt;
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.02em;
  margin-bottom: 8pt;
  flex-shrink: 0;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  gap: 4pt;
  margin-bottom: 11pt;
  flex-shrink: 0;
}

.tag {
  font-family: 'Courier New', Courier, monospace;
  font-size: 6pt;
  letter-spacing: 0.04em;
  padding: 1.5pt 4pt;
  border: 0.4pt solid #bbb;
  color: #777;
}

/* ---- Hero image — natural aspect ratio, capped height ---- */
.hero-img {
  width: 100%;
  height: auto;
  max-height: 65mm;
  object-fit: contain;
  object-position: left center;
  display: block;
  margin-bottom: 10pt;
  flex-shrink: 0;
}

/* ---- Description ---- */
.description {
  font-size: 8.5pt;
  line-height: 1.62;
  margin-bottom: 10pt;
  flex-shrink: 1;
  min-height: 0;
  overflow: hidden;
}

.description p + p { margin-top: 4pt; }

/* ---- Media grid (2-column flexbox) ---- */
/*
 * WeasyPrint does not reliably clip overflow on flex-wrap containers.
 * Fix: explicit max-height + overflow:hidden on the grid itself,
 * and min-height:0 on every flex child so shrinking actually works.
 */
.media-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6pt;
  margin-bottom: 9pt;
  flex-shrink: 1;
  min-height: 0;
  max-height: 72mm;
  overflow: hidden;
}

.media-cell {
  width: calc(50% - 3pt);
  overflow: hidden;
  flex-shrink: 1;
  min-height: 0;
}

/* Images preserve natural aspect ratio, hard-capped per-image */
.media-cell img {
  width: 100%;
  height: auto;
  max-height: 33mm;
  object-fit: contain;
  object-position: left top;
  display: block;
}

.caption {
  font-family: 'Courier New', Courier, monospace;
  font-size: 5.5pt;
  color: #999;
  margin-top: 3pt;
  letter-spacing: 0.02em;
}

/* ---- Video cells (no thumbnail, no QR) ---- */
.video-cell {
  border: 0.4pt solid #ddd;
  padding: 6pt;
  display: flex;
  flex-direction: column;
  gap: 4pt;
  justify-content: center;
  min-height: 16mm;
}

.video-url {
  font-family: 'Courier New', Courier, monospace;
  font-size: 5.5pt;
  color: #444;
  word-break: break-all;
}

/* ---- Links row — label + plain URL ---- */
.links-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5pt;
  margin-top: auto;
  padding-top: 8pt;
  border-top: 0.4pt solid #ddd;
  margin-bottom: 7pt;
  flex-shrink: 0;
}

.link-btn {
  font-family: 'Courier New', Courier, monospace;
  font-size: 6.5pt;
  letter-spacing: 0.04em;
  padding: 2.5pt 7pt;
  border: 0.4pt solid #111;
  color: #111;
  display: inline-flex;
  align-items: center;
  gap: 4pt;
}

.link-url {
  color: #555;
  font-size: 5.5pt;
  letter-spacing: 0;
}

/* ---- Page footer ---- */
.page-footer {
  display: flex;
  justify-content: space-between;
  padding-top: 5pt;
  border-top: 0.4pt solid #111;
  font-family: 'Courier New', Courier, monospace;
  font-size: 6pt;
  color: #aaa;
  letter-spacing: 0.03em;
  flex-shrink: 0;
}
"""


# ---------------------------------------------------------------------------
# Assemble full HTML document
# ---------------------------------------------------------------------------

def build_html(pages: list[str], name: str) -> str:
    body = "\n".join(pages)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>{esc(name)} — Portfolio</title>
  <style>{PDF_CSS}</style>
</head>
<body>
{body}
</body>
</html>"""


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a PDF portfolio from projects.json")
    parser.add_argument("--json",   default=str(SCRIPT_DIR / "projects.json"), help="Path to projects.json")
    parser.add_argument("--output", default=str(SCRIPT_DIR / "portfolio.pdf"),  help="Output PDF path")
    args = parser.parse_args()

    json_path = Path(args.json)
    if not json_path.exists():
        print(f"Error: {json_path} not found.")
        sys.exit(1)

    print(f"Loading {json_path} ...")
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    portfolio = data.get("portfolio", {})
    projects  = data.get("projects", [])

    if not projects:
        print("No projects found in projects.json.")
        sys.exit(1)

    print(f"Rendering {len(projects)} project page(s)...")
    pages = [render_project_page(p, i, portfolio) for i, p in enumerate(projects)]
    html  = build_html(pages, portfolio.get("name", "Portfolio"))

    out = Path(args.output)
    print(f"Writing PDF → {out} ...")
    HTML(string=html, base_url=str(SCRIPT_DIR)).write_pdf(str(out))
    print(f"Done! ✓ {out}")


if __name__ == "__main__":
    main()
