# --------------------------------------------
# driver.py  –   run checklist
# --------------------------------------------
from geometry import page_metrics
from fonts import font_inventory, has_only_times_and_arial

def run_checks(pdf_path):
    g = page_metrics(pdf_path)
    fonts = font_inventory(pdf_path)

    print("Margins (pt): L={:.1f}  R={:.1f}".format(
            g["left_margin"], g["right_margin"]))
    print("Two-column layout:", g["two_column"])
    print("Top fonts:", fonts[:5])
    print("Allowed fonts only:", has_only_times_and_arial(fonts))

if __name__ == "__main__":
    run_checks("submission.pdf")
