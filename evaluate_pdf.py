#!/usr/bin/env python3
"""evaluate_pdf.py

CLI driver that reads **compliance_config.py** and evaluates whatever
extractors are implemented.  Rules whose extractor cannot yet be resolved
print *[NOT IMPLEMENTED]* instead of crashing.

Example
-------
$ python evaluate_pdf.py submission.pdf
$ python evaluate_pdf.py submission.pdf --output json

The script currently supports **Quantitative** and **Existential** rules out
of the box.  Categorical / Structural / Qualitative evaluations will be
marked *SKIPPED* until their extractors are added.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Tuple

import sys
# add this block ↓
PROJECT_ROOT = Path(__file__).resolve().parent
SRC_PATH = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))


from compliance_config import (
    CRITERIA,
    QuantitativeCriterion,
    ExistentialCriterion,
    CategoricalCriterion,
    StructuralCriterion,
    QualitativeCriterion,
)

# -----------------------------------------------------------------------------
#  Extractor resolver
# -----------------------------------------------------------------------------

def _resolve_extractor(path: str) -> Tuple[bool, Any, str]:
    """Return (implemented, callable_or_value, message)."""
    parts = path.split(".")
    if not parts:
        return False, None, "empty extractor path"

    # Step 1: import the base module (could be nested, e.g. a.b.c)
    for i in range(len(parts), 0, -1):
        module_name = ".".join(parts[:i])
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            continue
        attr_chain = parts[i:]
        break
    else:
        return False, None, f"module not found in path '{path}'"

    obj: Any = module
    for idx, attr in enumerate(attr_chain):
        if callable(obj):
            # call the function now; remaining attrs will deref on its return
            obj = obj
            remaining_attrs = attr_chain[idx:]
            break
        if not hasattr(obj, attr):
            return False, None, f"attribute '{attr}' missing in '{'.'.join(parts[:i+idx])}'"
        obj = getattr(obj, attr)
    else:
        remaining_attrs = []

    return True, (obj, remaining_attrs), ""


def _execute_extractor(pdf_path: str, extractor_path: str):
    ok, payload, msg = _resolve_extractor(extractor_path)
    if not ok:
        return None, msg

    obj, tail_attrs = payload  # obj is module / func / value

    # If obj is callable ⇒ call with pdf_path
    try:
        if callable(obj):
            result = obj(pdf_path)
        else:
            result = obj
        # Drill down remainder of attribute/keys
        for attr in tail_attrs:
            # support dict keys first
            if isinstance(result, dict) and attr in result:
                result = result[attr]
            elif hasattr(result, attr):
                result = getattr(result, attr)
            else:
                return None, f"key/attr '{attr}' not found in extractor result"
        return result, ""
    except Exception as exc:
        return None, f"runtime error: {exc}"

# -----------------------------------------------------------------------------
#  Rule evaluators for implemented types
# -----------------------------------------------------------------------------

def _evaluate_quantitative(rule: QuantitativeCriterion, value: Any):
    try:
        val = float(value)
    except Exception:
        return False, f"non-numeric value ({value})"

    if rule.target is not None and rule.tolerance is not None:
        return abs(val - rule.target) <= rule.tolerance, val
    if rule.min_value is not None and rule.max_value is not None:
        return rule.min_value <= val <= rule.max_value, val
    if rule.min_value is not None:
        return val >= rule.min_value, val
    if rule.max_value is not None:
        return val <= rule.max_value, val
    return True, val  # nothing to compare


def _evaluate_existential(rule: ExistentialCriterion, value: Any):
    return bool(value) is rule.must_be_true, value

# -----------------------------------------------------------------------------
#  CLI
# -----------------------------------------------------------------------------

def run(pdf_path: str) -> Dict[str, Dict[str, Any]]:
    report: Dict[str, Dict[str, Any]] = {}

    for rule in CRITERIA:
        # Attempt to execute extractor -----------------------------------
        if not rule.extractor:
            report[rule.id] = {"status": "skipped", "reason": "no extractor path"}
            continue
        val, err = _execute_extractor(pdf_path, rule.extractor)
        if err:
            report[rule.id] = {"status": "skipped", "reason": err}
            continue

        # Evaluate according to rule type --------------------------------
        if isinstance(rule, QuantitativeCriterion):
            passed, detail = _evaluate_quantitative(rule, val)
        elif isinstance(rule, ExistentialCriterion):
            passed, detail = _evaluate_existential(rule, val)
        else:
            report[rule.id] = {"status": "skipped", "reason": f"{type(rule).__name__} not yet supported"}
            continue

        status = "ok" if passed else rule.severity
        report[rule.id] = {"status": status, "value": detail}

    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="PDF compliance checker")
    parser.add_argument("pdf", type=Path, help="Path to PDF")
    parser.add_argument("--output", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    if not args.pdf.exists():
        sys.exit(f"File not found: {args.pdf}")

    results = run(str(args.pdf))

    if args.output == "json":
        print(json.dumps(results, indent=2))
        return

    # Pretty text ---------------------------------------------------------
    for rid, res in results.items():
        status = res.get("status", "?")
        print(f"[{rid:5}] {status}")
        if "value" in res:
            print("    value :", res["value"])
        if "reason" in res:
            print("    reason:", res["reason"])


if __name__ == "__main__":
    main()
