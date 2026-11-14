# P18 — Customer Review Sentiment Analysis: BazaarHub.pk (SAMPLE)

**Period:** Thu 2026-01-01 → Tue 2026-06-30 (6 months, 181 days)
**Reviews:** 780 · **Average stars:** 3.37 · **Positive:** 408 (52.31%) · **Neutral:** 155 (19.87%) · **Negative:** 217 (27.82%)

## 1. The headline — what customers actually think

Just over half of all reviews are positive (52.31%), but more than one in four is negative (27.82%). The average review is 3.37 stars, which looks healthier than the text: the stars and the words disagree in 79 reviews (10.1%).

## 2. Sentiment by product category

| Category | Reviews | Positive | Neutral | Negative | Negative % | Avg stars |
|---|---|---|---|---|---|---|
| Electronics | 194 | 83 | 35 | 76 | 39.18% | 3.09 |
| Fashion | 207 | 121 | 37 | 49 | 23.67% | 3.51 |
| Home & Kitchen | 146 | 78 | 33 | 35 | 23.97% | 3.44 |
| Beauty | 128 | 71 | 24 | 33 | 25.78% | 3.48 |
| Grocery | 105 | 55 | 26 | 24 | 22.86% | 3.43 |

**Worst category: Electronics (39.18% negative)**; best: Grocery (22.86% negative).

## 3. Sentiment by channel

| Channel | Reviews | Positive | Neutral | Negative | Negative % | Avg stars |
|---|---|---|---|---|---|---|
| Website | 358 | 195 | 66 | 97 | 27.09% | 3.4 |
| Daraz | 267 | 126 | 53 | 88 | 32.96% | 3.2 |
| WhatsApp / Instagram | 155 | 87 | 36 | 32 | 20.65% | 3.61 |

**Most negative channel: Daraz (32.96% negative)**; least negative: WhatsApp / Instagram (20.65%).

## 4. Sentiment vs stars — where they disagree

| Sentiment | 1–2 stars | 3 stars | 4–5 stars | Total |
|---|---|---|---|---|
| Positive | 16 | 0 | 392 | 408 |
| Neutral | 27 | 102 | 26 | 155 |
| Negative | 207 | 0 | 10 | 217 |

Agreement (positive text with 4–5 stars, neutral with 3, negative with 1–2): **89.87%** (701 of 780 reviews). The disagreements are the finding, not noise: **5 five-star reviews carry negative text** and **5 one-star reviews carry positive text** — the first group is usually a customer who liked the product but hated the delivery, the second a customer who clicked the wrong star or had one bad moment with an otherwise good product.

## 5. Month by month

| Month | Reviews | Positive % | Negative % | Avg stars | Neg. change (pts) |
|---|---|---|---|---|---|
| 2026-01 | 103 | 46.6% | 33.98% | 3.33 | — |
| 2026-02 | 112 | 48.21% | 32.14% | 3.2 | -1.84 |
| 2026-03 | 125 | 48.8% | 27.2% | 3.31 | -4.94 |
| 2026-04 | 154 | 53.25% | 22.73% | 3.37 | -4.47 |
| 2026-05 | 127 | 51.18% | 29.13% | 3.35 | +6.40 |
| 2026-06 | 159 | 61.64% | 25.16% | 3.6 | -3.97 |

Negative sentiment moved **-8.82 points from January (33.98%) to June (25.16%)** — the store's delivery fixes are showing up in what customers write, not just in what they star.

## 6. Worst products

| Product | Category | Reviews | Negative | Negative % | Avg stars |
|---|---|---|---|---|---|
| AirBuds Pro | Electronics | 67 | 31 | 46.27% | 3.0 |
| Power Bank 10000mAh | Electronics | 71 | 26 | 36.62% | 3.2 |
| Smart Watch X2 | Electronics | 56 | 19 | 33.93% | 3.05 |
| Green Tea Pack | Grocery | 33 | 11 | 33.33% | 3.15 |
| Storage Organizer Box | Home & Kitchen | 60 | 18 | 30.0% | 3.2 |

**Worst product: AirBuds Pro (46.27% negative, 31 of 67 reviews)**; best: Basmati Rice 5kg (15.0% negative).

## 7. What customers complain about (counted from the text)

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

203 reviews (26.03%) mention at least one complaint theme; among negative reviews it is 203 of 217 (93.55%). Top theme: **Damaged product** (121 reviews).

## 8. Three recommendations

1. **Fix AirBuds Pro first.** 31 of its 67 reviews are negative (46.27%) — the worst of all 15 products and 18.5 points above the store average. Check the batch for defects before the next restock, and pause paid promotion for it until the complaint rate falls.
2. **Fix damaged product — the top complaint.** Damaged product appears in 121 reviews (15.51% of all reviews, 55.76% of negative ones). It is the single biggest driver of bad sentiment; every review that mentions it is a customer the store is close to losing.
3. **Fix delivery on Daraz.** Daraz is the most negative channel at 32.96% negative (88 of 267 reviews), against 20.65% on WhatsApp / Instagram. Renegotiate the courier or switch the Daraz fulfilment option before spending more on marketplace ads.

> Every number in this report is recomputed from `data/raw/reviews_SAMPLE.csv` by `src/analyze.py` using the open lexicon in `src/sentiment.py` — nothing is typed by hand. Run `python3 src/checks.py` to re-verify.
