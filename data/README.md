# P18 — Data dictionary + known quirks

## The review file — `data/raw/reviews_SAMPLE.csv`

SAMPLE customer reviews for the fictional store **BazaarHub.pk**,
Thu 2026-01-01 → Tue 2026-06-30 (6 months, 181 days). 780 reviews,
408 positive (52.31%), 155 neutral (19.87%), 217 negative (27.82%)
by the lexicon in `src/sentiment.py`, average 3.37 stars. Generated
by `src/generate_data.py` (seed 20261114) with deliberately different
sentiment by product (AirBuds Pro is the problem product at 46.27%
negative, Basmati Rice 5kg the best-liked at 15.0%), by channel
(Daraz carries more delivery complaints at 32.96% negative,
WhatsApp / Instagram the least at 20.65%) and by month (negative
sentiment falls from 33.98% in January to 25.16% in June) — so the
report has a real product story, a real channel story and a real
trend to surface. About 5% of reviews carry stars that contradict
their text on purpose (5 five-star reviews with negative text,
5 one-star reviews with positive text): on a real file those are
the first reviews a client should read.

| Column | Type | Meaning |
|---|---|---|
| review_id | text | `RB-0001` … `RB-0780`; the review key |
| date | text | `yyyy-mm-dd`; the review day |
| month | text | `yyyy-mm`; the report's month key |
| product | text | One of 15 products across 5 categories |
| category | text | One of 5: Electronics, Fashion, Home & Kitchen, Beauty, Grocery |
| channel | text | Where the review was left: Website, Daraz, WhatsApp / Instagram |
| stars | integer | 1–5, as the customer left it |
| review_text | text | The review itself (2 sentences from the sentiment pools in `src/generate_data.py`) |

## The processed files — `data/processed/`

- `reviews_scored.csv` — all 780 reviews with the lexicon score and
  sentiment attached, produced by `src/analyze.py`.
- `category_summary.csv` — one row per category (5 rows): reviews,
  positive/neutral/negative counts and shares, average stars and
  average score.
- `channel_summary.csv` — one row per channel (3 rows), same columns.
- `monthly_summary.csv` — one row per month (6 rows), same columns
  plus the month-on-month change in negative share (blank for January).
- `product_summary.csv` — one row per product (15 rows), same columns,
  sorted worst-first by negative share.
- `theme_summary.csv` — one row per complaint theme (8 rows): reviews
  mentioning it, share of all reviews, share of negative reviews.
- `reviews.db` — SQLite (schema in `sql/schema.sql`). NOT uploaded:
  rebuildable from `src/build_sqlite.py` + the raw CSV.

## The sentiment method — `src/sentiment.py`

Score = positive word hits − negative word hits, with a negation
("not", "never", "don't", …) flipping the next sentiment word within
two words. Score ≥ 1 → Positive, ≤ −1 → Negative, 0 → Neutral.
Complaint themes are keyword phrases counted from the text — a
review counts once per theme no matter how many of its phrases it
mentions. 203 reviews mention at least one theme, and every one of
them is a negative review (the theme phrases are complaint phrases).

## Known quirks

- **Neutral reviews carry 2- and 4-star ratings too.** A neutral
  text ("Product is okay, nothing special") was mostly left with
  3 stars, but 15% got 4 stars and 15% got 2 — the agreement rate
  (89.87%) counts only the exact band match (positive with 4–5,
  neutral with 3, negative with 1–2), so those mild cases count as
  disagreement. The report states the definition next to the number.
- **May breaks the improving trend.** Negative sentiment falls from
  33.98% (January) to 22.73% (April), then jumps to 29.13% in May
  before falling again to 25.16% in June. The report shows the
  measured months, never a smoothed trend line.
- **Green Tea Pack looks bad on a small base.** 33.33% negative, but
  only 33 reviews — the report ranks it 4th worst, and on a real
  file the call would also weigh volume, which the workbook shows
  next to every share.
- **The .db is not uploaded.** `data/processed/reviews.db` is
  rebuildable from `src/build_sqlite.py` + the raw CSV, so it stays
  out of the repo — same rule as every other project here.
