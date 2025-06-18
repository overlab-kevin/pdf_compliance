#!/usr/bin/env python3
"""
evaluate_pdf.py

Command‑line driver for automated format‑compliance checks.
Keeps the CLI thin; individual rules live in separate modules
under *src/*.  Add or modify checks by creating a new module
and decorating a function with @register("check_name").
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, List

# -----------------------------------------------------------------------------
#  Project layout helpers
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"

# Allow "import geometry" when src/geometry.py exists
sys.path.insert(0, str(SRC_PATH))

# -----------------------------------------------------------------------------
#  Graceful optional imports
# -----------------------------------------------------------------------------

def _safe_import(name: str):
    try:
        return __import__(name)
    except Exception as exc:
        print(f"[WARN] Could not import '{name}': {exc}")
        return None

geometry = _safe_import("geometry")
fonts = _safe_import("fonts")

# -----------------------------------------------------------------------------
#  Registry for individual check functions
# -----------------------------------------------------------------------------
CHECK_REGISTRY: Dict[str, Callable[[str], Dict]] = {}


def register(name: str):
    """Decorator to expose a function as a CLI‑addressable check."""

    def decorator(fn: Callable[[str], Dict]):
        CHECK_REGISTRY[name] = fn
        return fn

    return decorator

# -----------------------------------------------------------------------------
#  Geometry check (page size, margins, two‑column)
# -----------------------------------------------------------------------------

@register("geometry")
def check_geometry(pdf_path: str) -> Dict:
    """Requires src/geometry.py with a `page_metrics()` helper."""
    if geometry is None or not hasattr(geometry, "page_metrics"):
        return {
            "status": "skipped",
            "reason": "geometry module not available",
        }

    metrics = geometry.page_metrics(pdf_path)  # values in *points*

    PT_TO_CM = 2.54 / 72.0  # 1 pt = 1/72 inch
    left_cm = metrics["left_margin"] * PT_TO_CM
    right_cm = metrics["right_margin"] * PT_TO_CM

    SPEC_CM = {"left": 2.5, "right": 2.5}  # journal spec – tweak here

    status = "ok" if (left_cm >= SPEC_CM["left"] and right_cm >= SPEC_CM["right"]) else "warning"

    return {
        "status": status,
        "details": {
            "page_w_cm": round(metrics["page_w"] * PT_TO_CM, 2),
            "page_h_cm": round(metrics["page_h"] * PT_TO_CM, 2),
            "left_margin_cm": round(left_cm, 2),
            "right_margin_cm": round(right_cm, 2),
            "two_column": metrics["two_column"],
        },
    }

# -----------------------------------------------------------------------------
#  Font check (allowed families & sizes)
# -----------------------------------------------------------------------------

@register("fonts")
def check_fonts(pdf_path: str) -> Dict:
    """Requires src/fonts.py which in turn depends on pdfminer.six."""
    if fonts is None or not hasattr(fonts, "font_inventory"):
        return {
            "status": "skipped",
            "reason": "fonts module not available (install pdfminer.six)",
        }

    inv = fonts.font_inventory(pdf_path)
    ok = fonts.has_only_times_and_arial(inv) if hasattr(fonts, "has_only_times_and_arial") else False

    return {
        "status": "ok" if ok else "warning",
        "details": inv,
    }

# -----------------------------------------------------------------------------
#  Core runner
# -----------------------------------------------------------------------------

def run_checks(pdf_path: str, checks: List[str]) -> Dict[str, Dict]:
    report = {}
    for name in checks:
        fn = CHECK_REGISTRY.get(name)
        if fn is None:
            report[name] = {"status": "error", "reason": "unknown check"}
        else:
            report[name] = fn(pdf_path)
    return report

# -----------------------------------------------------------------------------
#  CLI entry‑point
# -----------------------------------------------------------------------------

def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a PDF for journal format compliance",
        epilog="Example: python evaluate_pdf.py submission.pdf --output json",
    )
    parser.add_argument("pdf", type=Path, help="PDF file to check")
    parser.add_argument(
        "--checks",
        nargs="+",
        choices=list(CHECK_REGISTRY.keys()),
        default=list(CHECK_REGISTRY.keys()),
        help="Subset of checks to run (default: all)",
    )
    parser.add_argument(
        "--output", choices=["text", "json"], default="text", help="Output format"
    )
    args = parser.parse_args(argv)

    if not args.pdf.exists():
        parser.error(f"{args.pdf} does not exist")

    report = run_checks(str(args.pdf), args.checks)

    if args.output == "json":
        print(json.dumps(report, indent=2))
    else:
        for name, res in report.items():
            print(f"[{name.upper():9}] {res.get('status', '?')}")
            if "details" in res:
                print("    details:", res["details"])
            if "reason" in res:
                print("    reason :", res["reason"])


if __name__ == "__main__":
    main()
