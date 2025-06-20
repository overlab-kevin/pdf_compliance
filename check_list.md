### 2.1 Physical layout

| ID      | Requirement                                                                                     | Fail threshold                           |
| ------- | ----------------------------------------------------------------------------------------------- | ---------------------------------------- |
| **L01** | Paper size **Letter 8.5 × 11 in**                                                               | Any other size                           |
| **L02** | Margins exactly **Top 4.3 cm, Bottom 4.3 cm, Left 4.8 cm, Right 4.8 cm**. Note these are very large, approximately 44% of the page width.                     | Deviates > 2 mm                          |
| **L03** | **Single column, double‑spaced** throughout                                                     | Multicolumn anywhere; line spacing < 1.5 |
| **L04** | Manuscript length **< 40 pages** — *exclude cover‑letter / response pages* | Outside limits                           |
| **L05** | All manuscript pages numbered consecutively (OK if first page not numbered)                                                     | Missing or non‑consecutive numbers       |
| **L06** | Footnote baseline **2.6 cm from bottom**                                                        | Footnotes elsewhere                      |

### 2.2 Typography

| ID      | Requirement                                                           | Fail threshold      |
| ------- | --------------------------------------------------------------------- | ------------------- |
| **T01** | Default font **Times New Roman**                                      | Different main font |
| **T02** | Title 14 pt; body 10 pt; footnotes/authors/affiliations/captions 8 pt | Any mismatch > 1 pt |

### 2.3 Section‑level content

| ID      | Requirement                                                                                                    | Fail threshold                         |
| ------- | -------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| **S00** | **Dedicated title page** present as page 1 with title, authors, affiliations, corresponding‑author info        | Missing or incomplete                  |
| **S01** | **Title** ≤ 15 words, grammatical, no unexplained abbreviations                                                | > 15 words or grammar errors           |
| **S02** | **Abstract** ≤ 250 words                                                                                       | Exceeds                                |
| **S03** | **Conclusions** present, distinct from abstract, discuss strengths, weaknesses, benefit to field & future work | Missing or duplicate of abstract       |
| **S04** | **Highlights** page present (3–5 bullets, ≤ 85 chars each)                                                     | Missing                                |
| **S05** | **CRediT author‑contribution statement** present                                                               | Missing                                |
| **S06** | **Declaration of generative‑AI use** present if any AI tools mentioned for preparing the manuscript                                         | AI usage evident but statement missing |
| **S07** | **Keywords section** present with 1–7 English keywords                                                         | Missing or > 7 keywords                |
| **S08** | **Relevancy** Provide a score between 0-100 on how relevant the paper is to the Pattern Recognition journal                                                         | Score < 30                |

### 2.4 References & citations

| ID      | Requirement                                    | Fail / Warn                                |
| ------- | ---------------------------------------------- | ------------------------------------------ |
| **R01** | Total references **35–55** (regular paper)     | < 20 or > 55 (review: up to ≈120 ⇒ *Warn*) |
| **R02** | ≥ 30 % of references from last **5 years**     | < 30 % ⇒ *Warn*                            |
| **R03** | ≤ 20 % arXiv / non‑peer‑reviewed               | > 20 % ⇒ *Warn*                            |
| **R04** | Avoid bulk citations (“…[1–6]”) w/o commentary | ≥ 2 bulk strings ⇒ *Warn*                  |
| **R05** | Cite ≥ 3 recent (within previous year) papers on general topic of pattern recognition (PR, PAMI, CVPR, ICPR, etc)     | < 3 ⇒ *Warn*                               |
