# --------------------------------------------
# geometry.py  –   fast geometry checks
# --------------------------------------------
import fitz  # PyMuPDF
from statistics import median

def page_metrics(pdf_path, page_no=0):
    doc = fitz.open(pdf_path)
    page = doc[page_no]

    # Raw media / crop boxes (points → convert to cm if you like)
    mediabox = page.rect         # (x0, y0, x1, y1)
    width, height = mediabox.width, mediabox.height

    # Text spans returned as a list of dictionaries
    blocks = page.get_text("dict")["blocks"]
    x0s = [span["bbox"][0] for b in blocks for l in b.get("lines", [])
                                     for span in l.get("spans", [])]
    x1s = [span["bbox"][2] for b in blocks for l in b.get("lines", [])
                                     for span in l.get("spans", [])]

    left_margin  = min(x0s)
    right_margin = width - max(x1s)
    # crude column detection: bimodal x-center distribution
    centers = [(a + b) / 2 for a, b in zip(x0s, x1s)]
    two_column = len({round(c / width, 1) for c in centers}) > 2

    return {
        "page_w": width, "page_h": height,
        "left_margin": left_margin, "right_margin": right_margin,
        "two_column": two_column
    }
