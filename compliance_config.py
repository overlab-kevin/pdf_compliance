from __future__ import annotations
"""compliance_config.py

Canonical *Pattern Recognition* checklist encoded as Python dataclasses.

Criterion **types**:
    • Quantitative – numeric target or range, tolerance in same units.
    • Categorical  – value must be inside an allowed set, or proportion of
      out‑of‑set values must be ≤ threshold.
    • Existential  – Boolean presence (true/false).
    • Structural   – Layout or ordering property spanning the document.
    • Qualitative  – Free‑text evaluation via LLM prompt.

Each rule mirrors an ID in **check_list.md**  fileciteturn2file0.
Alter the `CRITERIA` list to tweak policy without changing engine code.
"""

from dataclasses import dataclass, field
from typing import List, Sequence

# -----------------------------------------------------------------------------
#  Base & specialised criterion classes
# -----------------------------------------------------------------------------
@dataclass
class Criterion:
    id: str
    description: str
    severity: str = "warning"  # "warning" | "error" | "info"
    extractor: str = ""         # dotted‑path to helper function

@dataclass
class QuantitativeCriterion(Criterion):
    target: float | None = None
    tolerance: float | None = None
    min_value: float | None = None
    max_value: float | None = None
    units: str = ""

@dataclass
class CategoricalCriterion(Criterion):
    allowed_values: Sequence[str] = field(default_factory=list)
    proportion_threshold: float | None = None  # share allowed vs other

@dataclass
class ExistentialCriterion(Criterion):
    must_be_true: bool = True

@dataclass
class StructuralCriterion(Criterion):
    expected_structure: str = ""  # e.g. "single_column", "double_spaced"

@dataclass
class QualitativeCriterion(Criterion):
    prompt_template: str = ""
    llm_model: str = "gpt-4o-mini"

# -----------------------------------------------------------------------------
#  Criteria list – ordered exactly as in check_list.md
# -----------------------------------------------------------------------------
CRITERIA: List[Criterion] = [
    # ------------------------------------------------------------------
    # 2.1  Physical layout (L‑group)
    # ------------------------------------------------------------------
    QuantitativeCriterion(
        id="L01W",
        description="Page width must be Letter 8.5 in (21.59 cm)",
        severity="error",
        extractor="geometry.page_metrics.page_w_cm",
        target=21.59,
        tolerance=0.2,
        units="cm",
    ),
    QuantitativeCriterion(
        id="L01H",
        description="Page height must be Letter 11 in (27.94 cm)",
        severity="error",
        extractor="geometry.page_metrics.page_h_cm",
        target=27.94,
        tolerance=0.2,
        units="cm",
    ),
    QuantitativeCriterion(
        id="L02T",
        description="Top margin exactly 4.3 cm ±0.2 cm",
        severity="warning",
        extractor="geometry.page_metrics.top_margin_cm",
        target=4.3,
        tolerance=0.2,
        units="cm",
    ),
    QuantitativeCriterion(
        id="L02B",
        description="Bottom margin exactly 4.3 cm ±0.2 cm",
        severity="warning",
        extractor="geometry.page_metrics.bottom_margin_cm",
        target=4.3,
        tolerance=0.2,
        units="cm",
    ),
    QuantitativeCriterion(
        id="L02L",
        description="Left margin exactly 4.8 cm ±0.2 cm",
        severity="warning",
        extractor="geometry.page_metrics.left_margin_cm",
        target=4.8,
        tolerance=0.2,
        units="cm",
    ),
    QuantitativeCriterion(
        id="L02R",
        description="Right margin exactly 4.8 cm ±0.2 cm",
        severity="warning",
        extractor="geometry.page_metrics.right_margin_cm",
        target=4.8,
        tolerance=0.2,
        units="cm",
    ),
    StructuralCriterion(
        id="L03",
        description="Single column, double‑spaced throughout",
        severity="error",
        extractor="geometry.structure.single_column_double_spaced",
        expected_structure="single_column_double_spaced",
    ),
    QuantitativeCriterion(
        id="L04",
        description="Manuscript length 20–35 pages (≤40 for review)",
        severity="warning",
        extractor="structure.page_count",
        min_value=20,
        max_value=35,
        units="pages",
    ),
    StructuralCriterion(
        id="L05",
        description="All manuscript pages numbered consecutively",
        severity="error",
        extractor="structure.consecutive_page_numbers",
        expected_structure="consecutive_page_numbers",
    ),
    QuantitativeCriterion(
        id="L06",
        description="Footnote baseline 2.6 cm from bottom",
        severity="warning",
        extractor="geometry.page_metrics.footnote_baseline_cm",
        target=2.6,
        tolerance=0.2,
        units="cm",
    ),

    # ------------------------------------------------------------------
    # 2.2  Typography (T‑group)
    # ------------------------------------------------------------------
    CategoricalCriterion(
        id="T01",
        description="Default (most frequent) font must be Times New Roman",
        severity="error",
        extractor="fonts.most_common_body_font",
        allowed_values=["TimesNewRomanPSMT", "Times New Roman"],
    ),
    QuantitativeCriterion(
        id="T02_title",
        description="Title font size 14 pt ±1 pt",
        severity="warning",
        extractor="fonts.fontsize.title_pt",
        target=14,
        tolerance=0,
        units="pt",
    ),
    QuantitativeCriterion(
        id="T02_body",
        description="Body text 10 pt ±1 pt",
        severity="warning",
        extractor="fonts.fontsize.body_pt",
        target=10,
        tolerance=0,
        units="pt",
    ),
    QuantitativeCriterion(
        id="T02_captions",
        description="Captions / footnotes / affiliations 8 pt ±1 pt",
        severity="warning",
        extractor="fonts.fontsize.smalltext_pt",
        target=8,
        tolerance=0,
        units="pt",
    ),

    # ------------------------------------------------------------------
    # 2.3  Section‑level content (S‑group)
    # ------------------------------------------------------------------
    ExistentialCriterion(
        id="S00",
        description="Dedicated title page present (page 1)",
        severity="error",
        extractor="structure.has_title_page",
    ),
    QualitativeCriterion(
        id="S01",
        description="Title ≤15 words, grammatical, no unexplained abbreviations",
        severity="warning",
        extractor="structure.title_text",
        prompt_template="prompts/title_check.jinja2",
    ),
    QuantitativeCriterion(
        id="S02",
        description="Abstract ≤250 words",
        severity="error",
        extractor="structure.abstract_wordcount",
        max_value=250,
        units="words",
    ),
    QualitativeCriterion(
        id="S03",
        description="Conclusions present, distinct from abstract, cover key points",
        severity="warning",
        extractor="structure.conclusions_vs_abstract",
        prompt_template="prompts/conclusions_check.jinja2",
    ),
    ExistentialCriterion(
        id="S04",
        description="Highlights file present (3–5 bullets, ≤85 chars each)",
        severity="warning",
        extractor="structure.highlights_ok",
    ),
    ExistentialCriterion(
        id="S05",
        description="CRediT author‑contribution statement present",
        severity="warning",
        extractor="structure.has_credit_statement",
    ),
    ExistentialCriterion(
        id="S06",
        description="Generative‑AI use declaration present if AI mentioned",
        severity="warning",
        extractor="structure.ai_use_statement",
    ),
    QuantitativeCriterion(
        id="S07",
        description="Keywords section with 1–7 English keywords",
        severity="error",
        extractor="structure.keyword_count",
        min_value=1,
        max_value=7,
        units="keywords",
    ),

    # ------------------------------------------------------------------
    # 2.4  References & citations (R‑group)
    # ------------------------------------------------------------------
    QuantitativeCriterion(
        id="R01",
        description="Total references 35–55 (warn if review >55 but ≤120)",
        severity="warning",
        extractor="references.count",
        min_value=35,
        max_value=55,
        units="references",
    ),
    QuantitativeCriterion(
        id="R02",
        description="≥30 % references from last 5 years",
        severity="warning",
        extractor="references.share_recent_pct",
        min_value=30,
        units="percent",
    ),
    QuantitativeCriterion(
        id="R03",
        description="≤20 % arXiv / non‑peer‑reviewed",
        severity="warning",
        extractor="references.share_preprint_pct",
        max_value=20,
        units="percent",
    ),
    StructuralCriterion(
        id="R04",
        description="Bulk citation ranges must include commentary",
        severity="warning",
        extractor="references.bulk_citation_commentary",
        expected_structure="commentary_present",
    ),
    QuantitativeCriterion(
        id="R05",
        description="Cite ≥3 recent Pattern‑Recognition papers",
        severity="warning",
        extractor="references.count_pattern_recognition",
        min_value=3,
        units="papers",
    ),
]

# Convenience lookup
CRITERIA_BY_ID = {c.id: c for c in CRITERIA}
