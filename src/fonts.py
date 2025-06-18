from __future__ import annotations
"""fonts.py

Font‑related compliance helpers using **pdfminer.six**.
Expose two public functions expected by *evaluate_pdf.py*:

* ``font_inventory(pdf_path, first_n_pages=5)`` → list[(fontname, size), count]
* ``has_only_times_and_arial(counter)``         → bool

Implementation notes
--------------------
* pdfminer represents each page as a nested tree of layout objects. We walk it
  recursively, collecting every ``LTChar``.  Some objects (e.g. ``LTRect``)
  are *not* iterable, hence the explicit recursion helper.
* Font names in embedded PDFs often arrive as ``ABCDEF+TimesNewRomanPSMT``.
  The subset prefix before the ``+`` is stripped before policy checks.
"""

from collections import Counter
from pathlib import Path
from typing import List, Tuple

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTChar

# -----------------------------------------------------------------------------
#  Recursive walk helper -------------------------------------------------------
# -----------------------------------------------------------------------------

def _iter_chars(layout_obj):
    """Yield all LTChar descendants of *layout_obj* (depth‑first)."""
    if isinstance(layout_obj, LTChar):
        yield layout_obj
    elif hasattr(layout_obj, "_objs"):
        for child in layout_obj._objs:  # type: ignore[attr-defined]
            yield from _iter_chars(child)

# -----------------------------------------------------------------------------
#  Public API ------------------------------------------------------------------
# -----------------------------------------------------------------------------

def font_inventory(pdf_path: str | Path, first_n_pages: int = 5) -> List[Tuple[Tuple[str, float], int]]:
    """Return a frequency‑sorted list of ((fontname, size), count).

    *fontname* is the **stripped** PostScript name (subset prefix removed),
    *size* is rounded to one decimal place.
    """
    counter: Counter[Tuple[str, float]] = Counter()

    for page_layout in extract_pages(str(pdf_path), maxpages=first_n_pages):
        for lt_char in _iter_chars(page_layout):
            raw_name = lt_char.fontname  # e.g. 'ABCDEE+TimesNewRomanPSMT'
            name = raw_name.split("+")[-1]  # strip subset prefix
            tag = (name, round(lt_char.size, 1))
            counter[tag] += 1

    return counter.most_common()


# Allowed *base* font names (PostScript names) – tweak per journal policy
_ALLOWED_FONTS = {
    "TimesNewRomanPSMT",
    "TimesNewRomanPS-BoldMT",
    "TimesNewRomanPS-ItalicMT",
    "TimesNewRomanPS-BoldItalicMT",
    "ArialMT",
    "Arial-BoldMT",
    "Arial-ItalicMT",
    "Arial-BoldItalicMT",
}


def has_only_times_and_arial(counter: List[Tuple[Tuple[str, float], int]]) -> bool:
    """Return True if *all* fonts in *counter* belong to the allowed set."""
    for (name, _size), _count in counter:
        basename = name.split(",")[0]  # strip style qualifiers if any
        if basename not in _ALLOWED_FONTS:
            return False
    return True
