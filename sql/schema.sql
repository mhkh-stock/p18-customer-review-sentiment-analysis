-- P18 — schema for the BazaarHub.pk review sentiment report (SAMPLE data).
-- Grain: one row per review in fact_reviews. The sentiment score and
-- label are stored with the review (scored by the open lexicon in
-- src/sentiment.py when the file is loaded), so the SQL, the Python
-- and the workbook all read the same scored rows — checked as code.
-- Loaded by src/build_sqlite.py.

CREATE TABLE IF NOT EXISTS dim_product (
    product  TEXT PRIMARY KEY,
    category TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_channel (
    channel TEXT PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS fact_reviews (
    review_id       TEXT PRIMARY KEY,
    review_date     TEXT NOT NULL,   -- yyyy-mm-dd
    month           TEXT NOT NULL,   -- yyyy-mm
    product         TEXT NOT NULL REFERENCES dim_product(product),
    category        TEXT NOT NULL,
    channel         TEXT NOT NULL REFERENCES dim_channel(channel),
    stars           INTEGER NOT NULL CHECK (stars BETWEEN 1 AND 5),
    review_text     TEXT NOT NULL CHECK (length(review_text) > 0),
    sentiment_score INTEGER NOT NULL,
    sentiment       TEXT NOT NULL
                    CHECK (sentiment IN ('Positive', 'Neutral', 'Negative'))
);

CREATE INDEX IF NOT EXISTS idx_reviews_month
    ON fact_reviews (month);
CREATE INDEX IF NOT EXISTS idx_reviews_category
    ON fact_reviews (category);
CREATE INDEX IF NOT EXISTS idx_reviews_channel
    ON fact_reviews (channel);
CREATE INDEX IF NOT EXISTS idx_reviews_product
    ON fact_reviews (product);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment
    ON fact_reviews (sentiment);
