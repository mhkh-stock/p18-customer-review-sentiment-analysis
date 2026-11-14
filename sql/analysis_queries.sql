-- P18 — analysis queries: the whole report in SQL. Each query is run
-- against data/processed/reviews.db by src/checks.py and must agree
-- with the same numbers recomputed from the raw CSV.
-- Run one query at a time (sqlite3 CLI: .read sql/analysis_queries.sql
-- only runs the first statement — use the Python sqlite3 module or
-- split on the "-- Q" markers).

-- Q1: overall sentiment mix
SELECT
    sentiment,
    COUNT(*) AS reviews,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_reviews), 2)
        AS share_pct,
    ROUND(AVG(stars), 2) AS avg_stars,
    ROUND(AVG(sentiment_score), 2) AS avg_score
FROM fact_reviews
GROUP BY sentiment
ORDER BY reviews DESC;

-- Q2: sentiment by product category
SELECT
    category,
    COUNT(*) AS reviews,
    SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) AS positive,
    SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) AS neutral,
    SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative,
    ROUND(100.0 * SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS negative_pct,
    ROUND(AVG(stars), 2) AS avg_stars
FROM fact_reviews
GROUP BY category
ORDER BY reviews DESC;

-- Q3: sentiment by channel
SELECT
    channel,
    COUNT(*) AS reviews,
    SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) AS positive,
    SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) AS neutral,
    SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative,
    ROUND(100.0 * SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS negative_pct,
    ROUND(AVG(stars), 2) AS avg_stars
FROM fact_reviews
GROUP BY channel
ORDER BY reviews DESC;

-- Q4: monthly sentiment trend
SELECT
    month,
    COUNT(*) AS reviews,
    SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END) AS positive,
    SUM(CASE WHEN sentiment = 'Neutral' THEN 1 ELSE 0 END) AS neutral,
    SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative,
    ROUND(100.0 * SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS positive_pct,
    ROUND(100.0 * SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS negative_pct,
    ROUND(AVG(stars), 2) AS avg_stars
FROM fact_reviews
GROUP BY month
ORDER BY month;

-- Q5: sentiment vs stars cross-tab (the agreement check) — all 9
-- cells, including the two that are zero
WITH sentiments(s) AS (
    SELECT 'Positive' UNION ALL SELECT 'Neutral' UNION ALL
    SELECT 'Negative'
),
bands(b) AS (
    SELECT '1-2 stars' UNION ALL SELECT '3 stars' UNION ALL
    SELECT '4-5 stars'
)
SELECT
    s.s AS sentiment,
    b.b AS star_band,
    COUNT(f.review_id) AS reviews
FROM sentiments s
CROSS JOIN bands b
LEFT JOIN fact_reviews f
    ON f.sentiment = s.s
    AND CASE WHEN f.stars <= 2 THEN '1-2 stars'
             WHEN f.stars = 3 THEN '3 stars'
             ELSE '4-5 stars' END = b.b
GROUP BY s.s, b.b
ORDER BY s.s, b.b;

-- Q6: complaint themes, counted from the review text (same phrases
-- as src/sentiment.py THEMES — a review counts once per theme)
SELECT 'Late delivery' AS theme,
    SUM(CASE WHEN lower(review_text) LIKE '%late delivery%'
              OR lower(review_text) LIKE '%delivery was late%'
              OR lower(review_text) LIKE '%arrived late%'
              OR lower(review_text) LIKE '%took too long%'
              OR lower(review_text) LIKE '%delayed delivery%'
              OR lower(review_text) LIKE '%very late%'
              OR lower(review_text) LIKE '%days late%'
             THEN 1 ELSE 0 END) AS reviews
FROM fact_reviews
UNION ALL
SELECT 'Damaged product',
    SUM(CASE WHEN lower(review_text) LIKE '%damaged%'
              OR lower(review_text) LIKE '%broken%'
              OR lower(review_text) LIKE '%cracked%'
              OR lower(review_text) LIKE '%torn%'
              OR lower(review_text) LIKE '%scratched%'
              OR lower(review_text) LIKE '%bent%'
              OR lower(review_text) LIKE '%leaking%'
              OR lower(review_text) LIKE '%defective%'
              OR lower(review_text) LIKE '%faulty%'
             THEN 1 ELSE 0 END)
FROM fact_reviews
UNION ALL
SELECT 'Size / fit',
    SUM(CASE WHEN lower(review_text) LIKE '%too small%'
              OR lower(review_text) LIKE '%too big%'
              OR lower(review_text) LIKE '%wrong size%'
              OR lower(review_text) LIKE '%size issue%'
              OR lower(review_text) LIKE '%did not fit%'
              OR lower(review_text) LIKE '%does not fit%'
              OR lower(review_text) LIKE '%too tight%'
              OR lower(review_text) LIKE '%too loose%'
             THEN 1 ELSE 0 END)
FROM fact_reviews
UNION ALL
SELECT 'Price',
    SUM(CASE WHEN lower(review_text) LIKE '%overpriced%'
              OR lower(review_text) LIKE '%too expensive%'
              OR lower(review_text) LIKE '%not worth%'
              OR lower(review_text) LIKE '%waste of money%'
              OR lower(review_text) LIKE '%price is high%'
              OR lower(review_text) LIKE '%too costly%'
              OR lower(review_text) LIKE '%expensive for%'
             THEN 1 ELSE 0 END)
FROM fact_reviews
UNION ALL
SELECT 'Poor quality',
    SUM(CASE WHEN lower(review_text) LIKE '%poor quality%'
              OR lower(review_text) LIKE '%bad quality%'
              OR lower(review_text) LIKE '%low quality%'
              OR lower(review_text) LIKE '%cheap quality%'
              OR lower(review_text) LIKE '%quality is bad%'
              OR lower(review_text) LIKE '%quality is poor%'
             THEN 1 ELSE 0 END)
FROM fact_reviews
UNION ALL
SELECT 'Packaging',
    SUM(CASE WHEN lower(review_text) LIKE '%bad packaging%'
              OR lower(review_text) LIKE '%poor packaging%'
              OR lower(review_text) LIKE '%packaging was bad%'
              OR lower(review_text) LIKE '%no packaging%'
              OR lower(review_text) LIKE '%packaging torn%'
              OR lower(review_text) LIKE '%packing was bad%'
             THEN 1 ELSE 0 END)
FROM fact_reviews
UNION ALL
SELECT 'Customer service',
    SUM(CASE WHEN lower(review_text) LIKE '%customer service%'
              OR lower(review_text) LIKE '%no reply%'
              OR lower(review_text) LIKE '%no response%'
              OR lower(review_text) LIKE '%rude staff%'
              OR lower(review_text) LIKE '%nobody answered%'
              OR lower(review_text) LIKE '%support did not%'
              OR lower(review_text) LIKE '%support was rude%'
             THEN 1 ELSE 0 END)
FROM fact_reviews
UNION ALL
SELECT 'Wrong item',
    SUM(CASE WHEN lower(review_text) LIKE '%wrong item%'
              OR lower(review_text) LIKE '%wrong product%'
              OR lower(review_text) LIKE '%wrong colour%'
              OR lower(review_text) LIKE '%wrong color%'
              OR lower(review_text) LIKE '%different item%'
              OR lower(review_text) LIKE '%not what i ordered%'
             THEN 1 ELSE 0 END)
FROM fact_reviews;

-- Q7: worst products by negative share (all 15 products)
SELECT
    product,
    category,
    COUNT(*) AS reviews,
    SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END) AS negative,
    ROUND(100.0 * SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END)
        / COUNT(*), 2) AS negative_pct,
    ROUND(AVG(stars), 2) AS avg_stars
FROM fact_reviews
GROUP BY product, category
ORDER BY negative_pct DESC;
