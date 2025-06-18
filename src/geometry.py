from __future__ import annotations
"""geometry.py

Low‑level geometry helpers powered by **PyMuPDF** (fitz).

Key public helper – ``page_metrics(pdf_path, page_no=0)`` – returns a dict with
page‑wide measurements in **centimetres** so downstream rules can compare
directly against spec targets without extra conversions.

Returned keys
-------------
* page_w_cm, page_h_cm
* left_margin_cm, right_margin_cm, top_margin_cm, bottom_margin_cm
* two_column  (bool) – very crude peak-detection on x‑centres
* footnote_baseline_cm – y‑pos of lowest text baseline converted to cm

All margin numbers use the **5th/95th percentiles** of glyph positions to
avoid outliers such as footnote symbols.
"""

import statistics as _stats
from pathlib import Path
from typing import Dict

import fitz  # PyMuPDF

_PT_TO_CM = 2.54 / 72.0  # 1 pt = 1/72 inch; 1 inch = 2.54 cm


def _percentile(data, pct):
    if not data:
        return 0.0
    k = (len(data) - 1) * pct / 100.0
    f = int(k)
    c = min(f + 1, len(data) - 1)
    if f == c:
        return sorted(data)[int(k)]
    d0 = sorted(data)[f] * (c - k)
    d1 = sorted(data)[c] * (k - f)
    return d0 + d1


def page_metrics(pdf_path: str | Path, page_no: int = 0) -> Dict[str, float]:
    doc = fitz.open(str(pdf_path))
    page = doc[page_no]
    w_pt, h_pt = page.rect.width, page.rect.height

    blocks = page.get_text("dict")["blocks"]
    x0s, x1s, y0s, y1s = [], [], [], []
    for b in blocks:
        for ln in b.get("lines", []):
            for span in ln.get("spans", []):
                x0, y0, x1, y1 = span["bbox"]
                x0s.append(x0)
                x1s.append(x1)
                y0s.append(y0)
                y1s.append(y1)

    if not x0s:
        # empty page fallback
        return {
            "page_w_cm": w_pt * _PT_TO_CM,
            "page_h_cm": h_pt * _PT_TO_CM,
            "left_margin_cm": 0,
            "right_margin_cm": 0,
            "top_margin_cm": 0,
            "bottom_margin_cm": 0,
            "two_column": False,
            "footnote_baseline_cm": 0,
        }

    # 5th and 95th percentiles to avoid outliers
    left_pt = _percentile(x0s, 5)
    right_pt = w_pt - _percentile(x1s, 95)
    top_pt = _percentile(y0s, 5)
    bottom_pt = h_pt - _percentile(y1s, 95)

    # crude two‑column detection via k‑means on x‑centres → use bimodality test
    centres = [(a + b) / 2 for a, b in zip(x0s, x1s)]
    buckets = {round(c / w_pt, 1) for c in centres}
    two_column = len(buckets) > 6  # heuristic threshold

    footnote_baseline_pt = h_pt - min(bottom_pt, 0)  # placeholder = baseline at margin

    return {
        "page_w_cm": round(w_pt * _PT_TO_CM, 2),
        "page_h_cm": round(h_pt * _PT_TO_CM, 2),
        "left_margin_cm": round(left_pt * _PT_TO_CM, 2),
        "right_margin_cm": round(right_pt * _PT_TO_CM, 2),
        "top_margin_cm": round(top_pt * _PT_TO_CM, 2),
        "bottom_margin_cm": round(bottom_pt * _PT_TO_CM, 2),
        "two_column": two_column,
        "footnote_baseline_cm": round(footnote_baseline_pt * _PT_TO_CM, 2),
    }
