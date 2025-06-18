#!/usr/bin/env python3
"""evaluate_pdf.py – PDF format‑compliance CLI.

* Loads criteria from ``compliance_config.py``
* Resolves dotted extractor paths such as
  ``geometry.page_metrics.top_margin_cm``
* Evaluates **Quantitative**, **Existential**, and **Structural** rules.

Usage
-----
$ python evaluate_pdf.py sample.pdf            # pretty text
$ python evaluate_pdf.py sample.pdf --output json
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Sequence, Tuple

from compliance_config import (
    CRITERIA,
    QuantitativeCriterion,
    ExistentialCriterion,
    StructuralCriterion,
    CategoricalCriterion,
    QualitativeCriterion,
)

# -----------------------------------------------------------------------------
#  Make src/ importable --------------------------------------------------------
# -----------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# -----------------------------------------------------------------------------
#  Extractor resolver ----------------------------------------------------------
# -----------------------------------------------------------------------------

def _execute_extractor(pdf_path: str, dotted_path: str) -> Tuple[bool, Any]:
    """Return ``(success, value_or_msg)``.

    *success* is False when the module, attribute, or call fails.
    Example dotted path: ``geometry.page_metrics.left_margin_cm``
    """
    parts: Sequence[str] = dotted_path.split(".")
    if not parts:
        return False, "empty extractor path"

    # Import base module --------------------------------------------------
    try:
        obj: Any = importlib.import_module(parts[0])
    except ModuleNotFoundError as exc:
        return False, f"module import error: {exc}"

    called_first_callable = False

    # Walk remaining attributes/keys -------------------------------------
    for attr in parts[1:]:
        # Call the first callable with the PDF path
        if callable(obj) and not called_first_callable:
            try:
                obj = obj(pdf_path)
            except Exception as exc:
                return False, f"call error: {exc}"
            called_first_callable = True
        # Dereference attr / key
        if isinstance(obj, dict) and attr in obj:
            obj = obj[attr]
        elif hasattr(obj, attr):
            obj = getattr(obj, attr)
        else:
            return False, f"attribute/key '{attr}' missing"

    # If we never called a callable (path ends right after function)
    if callable(obj) and not called_first_callable:
        try:
            obj = obj(pdf_path)
        except Exception as exc:
            return False, f"call error: {exc}"

    return True, obj

# -----------------------------------------------------------------------------
#  Evaluators ------------------------------------------------------------------
# -----------------------------------------------------------------------------

def _eval_quant(rule: QuantitativeCriterion, val: Any):
    try:
        v = float(val)
    except Exception:
        return False, f"non‑numeric ({val})"
    if rule.target is not None and rule.tolerance is not None:
        return abs(v - rule.target) <= rule.tolerance, v
    if rule.min_value is not None and rule.max_value is not None:
        return rule.min_value <= v <= rule.max_value, v
    if rule.min_value is not None:
        return v >= rule.min_value, v
    if rule.max_value is not None:
        return v <= rule.max_value, v
    return True, v


def _eval_boolean(val: Any):
    return bool(val) is True, val

# -----------------------------------------------------------------------------
#  Core runner -----------------------------------------------------------------
# -----------------------------------------------------------------------------

def run(pdf_path: str) -> Dict[str, Dict[str, Any]]:
    report: Dict[str, Dict[str, Any]] = {}

    for rule in CRITERIA:
        success, value_or_msg = _execute_extractor(pdf_path, rule.extractor) if rule.extractor else (False, "no extractor path")
        if not success:
            report[rule.id] = {"status": "skipped", "reason": value_or_msg}
            continue
        val = value_or_msg

        # Dispatch --------------------------------------------------------
        if isinstance(rule, QuantitativeCriterion):
            passed, detail = _eval_quant(rule, val)
        elif isinstance(rule, (ExistentialCriterion, StructuralCriterion)):
            passed, detail = _eval_boolean(val)
        else:
            report[rule.id] = {"status": "skipped", "reason": f"{type(rule).__name__} not supported"}
            continue

        report[rule.id] = {
            "status": "ok" if passed else rule.severity,
            "value": detail,
        }

    return report

# -----------------------------------------------------------------------------
#  CLI -------------------------------------------------------------------------
# -----------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="PDF compliance checker")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    if not args.pdf.exists():
        sys.exit("file not found")

    results = run(str(args.pdf))

    if args.output == "json":
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    # Pretty text ---------------------------------------------------------
    for rid, res in results.items():
        print(f"[{rid:5}] {res['status']}")
        if "value" in res:
            print("    value :", res["value"])
        if "reason" in res:
            print("    reason:", res["reason"])


if __name__ == "__main__":
    main()
