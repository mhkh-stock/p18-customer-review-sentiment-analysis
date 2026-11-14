# P18 — Customer Review Sentiment Analysis

**Client (SAMPLE):** BazaarHub.pk — Pakistani online store,
6 months (Thu 2026-01-01 → Tue 2026-06-30, 181 days) ·
**Status: SAMPLE delivery on DEMO data**
**Tools:** Python (open lexicon) · SQL (SQLite) · Excel (live formulas) · reportlab
**Deliverable:** `outputs/sentiment_report.pdf` (2 pages) +
`outputs/customer_review_sentiment_report_SAMPLE.xlsx`

> ⚠️ **What this is and is not.** The review file is a fictional
> store's demo data, generated to show the method. No real store,
> customer or order is involved. What is real is the analysis: the
> same lexicon, cross-tab and workbook run on a real client's review
> export the same way, and every number in the report is recomputed
> from the data, never typed.

## Business question it answers

> "What do my customers actually think?"

A store owner who only watches the average star rating cannot tell
whether customers are happy with the product and angry about the
delivery, or the other way round. This delivery answers it from the
words customers wrote: how sentiment splits overall, which category,
channel and product draws the complaints, what the complaints are
about (counted from the text), whether the stars agree with the
words — and what to fix first, with the numbers attached to each
answer.

## The method (plainly stated)

Sentiment is scored by a **transparent lexicon** in
`src/sentiment.py` — two plain word lists, no API, no machine-learning
model. Every word in a review is looked up; a sentiment word after a
negation ("not good", "never happy") counts the other way round.
Score = positive hits − negative hits: ≥ 1 Positive, ≤ −1 Negative,
0 Neutral. The lists are in the open, so a client can read, argue
with and edit them.

**Limits, stated upfront:** the lexicon cannot read sarcasm; it
misses sentiment carried only by a phrase that is not in the lists;
a review that praises one thing and complains about another scores
near zero (Neutral) even though it contains both. Stars and text
disagree in about 10% of reviews — that is a finding, not an error,
and the report counts those reviews instead of hiding them.

## What is inside

| File | What it does |
|---|---|
| `outputs/sentiment_report.pdf` | The deliverable: 2-page client report — headline, category + channel tables, monthly trend, sentiment-vs-stars cross-tab, complaint themes, 3 recommendations |
| `outputs/customer_review_sentiment_report_SAMPLE.xlsx` | The working report: Dashboard (KPIs + monthly trend, live formulas) + Sentiment by Category + Sentiment by Channel + Monthly Trend + Themes + Reviews + Method sheets |
| `outputs/sentiment_report.md` | Findings report: headline numbers, all tables, the reasoning |
| `outputs/summary.json` | Machine-readable summary (mix + categories + channels + months + products + themes + cross-tab + actions) |
| `outputs/monthly_sentiment.png` | Monthly positive vs negative % chart (render of the same data) |
| `data/raw/reviews_SAMPLE.csv` | The review file: 780 reviews, date + product + category + channel + stars + review text |
| `data/processed/reviews_scored.csv` | All 780 reviews with the lexicon score and sentiment attached |
| `data/processed/category_summary.csv` | 5-category summary produced by `src/analyze.py` |
| `data/processed/channel_summary.csv` | 3-channel summary produced by `src/analyze.py` |
| `data/processed/monthly_summary.csv` | 6-month summary produced by `src/analyze.py` |
| `data/processed/product_summary.csv` | 15-product summary produced by `src/analyze.py` |
| `data/processed/theme_summary.csv` | 8-theme summary produced by `src/analyze.py` |
| `data/processed/reviews.db` | SQLite: dim_product + dim_channel + fact_reviews (NOT uploaded — rebuildable) |
| `data/README.md` | Data dictionary + known quirks |
| `sql/schema.sql` | Schema for the review fact table (stars 1–5, sentiment label enforced) |
| `sql/analysis_queries.sql` | The whole report in SQL — 7 queries that must agree with the workbook |
| `src/sentiment.py` | The lexicon: word lists, negation handling, scoring, complaint themes |
| `src/generate_data.py` | Makes the demo file (seeded; NOT run on a real client file) |
| `src/analyze.py` | Recomputes every headline number from the raw CSV |
| `src/build_sqlite.py` | Loads the reviews into SQLite, scoring each one with the lexicon |
| `src/build_workbook.py` | Builds the workbook: 7 sheets, live formulas |
| `src/build_report.py` | Builds the 2-page PDF + chart from `outputs/summary.json` |
| `src/checks.py` | Data-quality + reconciliation checks as code — 169 checks, all passing |
| `requirements.txt` | Pinned: `openpyxl==3.1.2`, `reportlab==5.0.1`, `matplotlib==3.6.3` (Python 3.12) |

## How it fits together

```
Client review export (same columns) ──▶ src/analyze.py ──▶ summary.json
        (780 rows in the demo)                + sentiment_report.md
                                                 ▼
                                       src/build_sqlite.py ──▶ data/processed/reviews.db
                                                 │              (NOT uploaded: rebuildable)
                                                 ▼
                                       src/build_workbook.py ──▶ customer_review_sentiment_report_SAMPLE.xlsx
                                                 │              (7 sheets, live formulas)
                                                 ▼
                                       src/build_report.py ──▶ sentiment_report.pdf (2 pages)
                                                 ▲ src/checks.py verifies all of it (169 checks)
```

## Headline numbers (SAMPLE — BazaarHub.pk, 6 months)

- **780 reviews at an average of 3.37 stars** ·
  **Positive: 408 (52.31%)** · **Neutral:
  155 (19.87%)** · **Negative:
  217 (27.82%)** · average sentiment score
  1.48
- **Worst category: Electronics (39.18% negative)**;
  best: Grocery (22.86%)
- **Worst channel: Daraz (32.96% negative)**;
  best: WhatsApp / Instagram (20.65%)
- **Worst product: AirBuds Pro (46.27% negative,
  31 of 67 reviews)**; best:
  Basmati Rice 5kg (15.0%)
- **Stars and text agree in 89.87% of reviews**
  (701 of 780) — and
  **5 five-star reviews carry negative text** while
  **5 one-star reviews carry positive text**
- **Negative sentiment fell -8.82 points from
  January (33.98%) to June (25.16%)** —
  the store's delivery fixes are showing up in what customers write
- **Top complaint: Damaged product (121 reviews,
  15.51% of all reviews, 55.76% of
  negative ones)**; 203 reviews
  (26.03%)
  mention at least one complaint theme

## Sentiment by product category

| Category | Reviews | Positive | Neutral | Negative | Negative % | Avg stars |
|---|---|---|---|---|---|---|
| Electronics | 194 | 83 | 35 | 76 | 39.18% | 3.09 |
| Fashion | 207 | 121 | 37 | 49 | 23.67% | 3.51 |
| Home & Kitchen | 146 | 78 | 33 | 35 | 23.97% | 3.44 |
| Beauty | 128 | 71 | 24 | 33 | 25.78% | 3.48 |
| Grocery | 105 | 55 | 26 | 24 | 22.86% | 3.43 |

## Sentiment by channel

| Channel | Reviews | Positive | Neutral | Negative | Negative % | Avg stars |
|---|---|---|---|---|---|---|
| Website | 358 | 195 | 66 | 97 | 27.09% | 3.4 |
| Daraz | 267 | 126 | 53 | 88 | 32.96% | 3.2 |
| WhatsApp / Instagram | 155 | 87 | 36 | 32 | 20.65% | 3.61 |

## Month by month

| Month | Reviews | Positive % | Negative % | Avg stars |
|---|---|---|---|---|
| 2026-01 | 103 | 46.6% | 33.98% | 3.33 |
| 2026-02 | 112 | 48.21% | 32.14% | 3.2 |
| 2026-03 | 125 | 48.8% | 27.2% | 3.31 |
| 2026-04 | 154 | 53.25% | 22.73% | 3.37 |
| 2026-05 | 127 | 51.18% | 29.13% | 3.35 |
| 2026-06 | 159 | 61.64% | 25.16% | 3.6 |

Negative sentiment moved **-8.82 points
from January to June**. April is the best month
(22.73% negative); January the worst
(33.98%).

## Sentiment vs stars — where they disagree

| Sentiment | 1–2 stars | 3 stars | 4–5 stars | Total |
|---|---|---|---|---|
| Positive | 16 | 0 | 392 | 408 |
| Neutral | 27 | 102 | 26 | 155 |
| Negative | 207 | 0 | 10 | 217 |

The disagreements are the finding, not noise: the 5
five-star reviews with negative text are usually customers who liked
the product but hated the delivery; the 5 one-star
reviews with positive text are usually a wrong-star click or one bad
moment with an otherwise good product. Read those reviews before
acting on the average rating.

## Worst products

| Product | Category | Reviews | Negative | Negative % | Avg stars |
|---|---|---|---|---|---|
| AirBuds Pro | Electronics | 67 | 31 | 46.27% | 3.0 |
| Power Bank 10000mAh | Electronics | 71 | 26 | 36.62% | 3.2 |
| Smart Watch X2 | Electronics | 56 | 19 | 33.93% | 3.05 |
| Green Tea Pack | Grocery | 33 | 11 | 33.33% | 3.15 |
| Storage Organizer Box | Home & Kitchen | 60 | 18 | 30.0% | 3.2 |

## What customers complain about (counted from the text)

| Theme | Reviews | % of all | % of negative |
|---|---|---|---|
| Damaged product | 121 | 15.51% | 55.76% |
| Price | 79 | 10.13% | 36.41% |
| Poor quality | 59 | 7.56% | 27.19% |
| Customer service | 46 | 5.9% | 21.2% |
| Late delivery | 33 | 4.23% | 15.21% |
| Size / fit | 23 | 2.95% | 10.6% |
| Packaging | 19 | 2.44% | 8.76% |
| Wrong item | 18 | 2.31% | 8.29% |

A review can mention more than one theme, so the column does not sum
to the total. Every themed review in this file is a negative review —
the theme phrases are complaint phrases, so a review that mentions
one is, by the lexicon, a negative review.

## The three recommendations (from the data, not from a template)

1. **Fix AirBuds Pro first.** 31 of its 67 reviews are negative (46.27%) — the worst of all 15 products and 18.5 points above the store average. Check the batch for defects before the next restock, and pause paid promotion for it until the complaint rate falls.
2. **Fix damaged product — the top complaint.** Damaged product appears in 121 reviews (15.51% of all reviews, 55.76% of negative ones). It is the single biggest driver of bad sentiment; every review that mentions it is a customer the store is close to losing.
3. **Fix delivery on Daraz.** Daraz is the most negative channel at 32.96% negative (88 of 267 reviews), against 20.65% on WhatsApp / Instagram. Renegotiate the courier or switch the Daraz fulfilment option before spending more on marketplace ads.

## Same logic, three ways — and they must agree

The sentiment mix, category, channel, monthly, cross-tab, theme and
product totals exist in three forms: the SQL in
`sql/analysis_queries.sql`, the Python in `src/analyze.py`, and this
workbook's formulas. `src/checks.py` runs all three against the raw
file and compares them — a mistake in any one of them shows up as a
failure. The workbook's formulas were also recalculated in
LibreOffice (including the `_xlfn.MAXIFS` / `_xlfn.MINIFS` best/worst
month cells): every total matches the recompute exactly, with zero
error values.

## Reproduce it (2 minutes)

```bash
python3 src/generate_data.py   # rebuild the SAMPLE file (seed 20261114)
python3 src/analyze.py         # summary.json + sentiment_report.md
python3 src/build_sqlite.py    # data/processed/reviews.db
python3 src/build_workbook.py  # outputs/customer_review_sentiment_report_SAMPLE.xlsx
python3 src/build_report.py    # outputs/sentiment_report.pdf (2 pages)
python3 src/checks.py          # 169 checks — expect all passing
```

On a real client file, replace `data/raw/reviews_SAMPLE.csv` with the
review export (same columns) and skip `generate_data.py` — everything
downstream runs unchanged.
