from __future__ import annotations
"""geometry.py – layout metrics via PyMuPDF (fitz)

The public helper ``page_metrics(pdf_path)`` now scans **every page** and
returns *document‑level* extrema the compliance rules care about:

* ``page_w_cm`` / ``page_h_cm`` – **median** width/height in cm (to catch
  stray cover pages but ignore isolated mis‑sized annexes).
* ``left_margin_cm`` / ``right_margin_cm`` / ``top_margin_cm`` /
  ``bottom_margin_cm`` – **minimum** margin observed on any page.
* ``two_column`` – *True* if **every** page looks two‑column, *False* if
  **any** page is single‑column.
* ``footnote_baseline_cm`` – **median** footnote baseline (distance from
  bottom‑of‑page to lowest text baseline).

Per‑page raw records are also returned under ``_pages`` for debugging.

Why extrema?  Most editorial specs state a *minimum* margin and *maximum*
page count.  Using min/median lets a single offending page trigger a fail
without obscuring where the problem lies.
"""

import statistics as _stats
from pathlib import Path
from typing import Dict, List

import fitz  # PyMuPDF

_PT_TO_CM = 2.54 / 72.0  # 1 pt = 1/72 in; 1 in = 2.54 cm

# -----------------------------------------------------------------------------
#  Low‑level helpers
# -----------------------------------------------------------------------------

def _percentile(data, pct):
    if not data:
        return 0.0
    data_sorted = sorted(data)
    k = (len(data) - 1) * pct / 100.0
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return data_sorted[int(k)]
    d0 = data_sorted[f] * (c - k)
    d1 = data_sorted[c] * (k - f)
    return d0 + d1


def _page_metrics_single(page) -> Dict[str, float]:
    """Return metrics for *one* page in **points** (except bool)."""
    w_pt, h_pt = page.rect.width, page.rect.height
    blocks = page.get_text("dict")["blocks"]
    x0s, x1s, y0s, y1s = [], [], [], []
    for b in blocks:
        for ln in b.get("lines", []):
            for sp in ln.get("spans", []):
                x0, y0, x1, y1 = sp["bbox"]
                x0s.append(x0)
                x1s.append(x1)
                y0s.append(y0)
                y1s.append(y1)

    if not x0s:
        # Blank page fall‑back
        return {
            "page_w": w_pt,
            "page_h": h_pt,
            "left_margin": w_pt,  # absurdly large → never the min
            "right_margin": w_pt,
            "top_margin": h_pt,
            "bottom_margin": h_pt,
            "two_column": False,
            "footnote_baseline": 0,
        }

    left_pt = _percentile(x0s, 5)
    right_pt = w_pt - _percentile(x1s, 95)
    top_pt = _percentile(y0s, 5)
    bottom_pt = h_pt - _percentile(y1s, 95)

    centres = [(a + b) / 2 for a, b in zip(x0s, x1s)]
    # crude bimodality via binning
    buckets = {round(c / w_pt, 1) for c in centres}
    two_col = len(buckets) > 6

    foot_baseline_pt = h_pt - min(y0s)  # distance from bottom edge to lowest glyph top

    return {
        "page_w": w_pt,
        "page_h": h_pt,
        "left_margin": left_pt,
        "right_margin": right_pt,
        "top_margin": top_pt,
        "bottom_margin": bottom_pt,
        "two_column": two_col,
        "footnote_baseline": foot_baseline_pt,
    }

# -----------------------------------------------------------------------------
#  Public entry – aggregates across pages
# -----------------------------------------------------------------------------

def page_metrics(pdf_path: str | Path) -> Dict[str, float]:
    doc = fitz.open(str(pdf_path))

    per_page: List[Dict[str, float]] = [_page_metrics_single(p) for p in doc]

    # Aggregations -------------------------------------------------------------
    page_w_cm = _stats.median(p["page_w"] for p in per_page) * _PT_TO_CM
    page_h_cm = _stats.median(p["page_h"] for p in per_page) * _PT_TO_CM

    left_cm = min(p["left_margin"] for p in per_page) * _PT_TO_CM
    right_cm = min(p["right_margin"] for p in per_page) * _PT_TO_CM
    top_cm = min(p["top_margin"] for p in per_page) * _PT_TO_CM
    bottom_cm = min(p["bottom_margin"] for p in per_page) * _PT_TO_CM

    two_column_consistent = all(p["two_column"] for p in per_page)

    footnote_baseline_cm = _stats.median(p["footnote_baseline"] for p in per_page) * _PT_TO_CM

    return {
        "page_w_cm": round(page_w_cm, 2),
        "page_h_cm": round(page_h_cm, 2),
        "left_margin_cm": round(left_cm, 2),
        "right_margin_cm": round(right_cm, 2),
        "top_margin_cm": round(top_cm, 2),
        "bottom_margin_cm": round(bottom_cm, 2),
        "two_column": two_column_consistent,
        "footnote_baseline_cm": round(footnote_baseline_cm, 2),
        # stash per‑page dict for debugging
        "_pages": per_page,
    }
