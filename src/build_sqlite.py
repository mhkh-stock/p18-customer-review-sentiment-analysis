#!/usr/bin/env python3
"""P18 — load the SAMPLE review file into SQLite (sql/schema.sql).
Each review is scored with the lexicon in src/sentiment.py as it is
loaded, so the database carries the same scored rows the Python
analysis and the workbook use.

    python3 src/build_sqlite.py

The .db is NOT uploaded to GitHub (rebuildable from the pushed
scripts) — same rule as every other project in this portfolio.
"""
import csv
import sqlite3
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
DB = PROJECT / "data" / "processed" / "reviews.db"
sys.path.insert(0, str(PROJECT / "src"))
from sentiment import score_and_classify  # noqa: E402


def main():
    reviews = list(csv.DictReader(
        open(RAW / "reviews_SAMPLE.csv", encoding="utf-8")))
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    con.executescript((PROJECT / "sql" / "schema.sql").read_text())
    products = sorted({(r["product"], r["category"]) for r in reviews})
    con.executemany("INSERT INTO dim_product VALUES (?, ?)", products)
    channels = sorted({r["channel"] for r in reviews})
    con.executemany("INSERT INTO dim_channel VALUES (?)",
                    [(c,) for c in channels])
    rows = []
    for r in reviews:
        score, sentiment = score_and_classify(r["review_text"])
        rows.append((r["review_id"], r["date"], r["month"], r["product"],
                     r["category"], r["channel"], int(r["stars"]),
                     r["review_text"], score, sentiment))
    con.executemany(
        "INSERT INTO fact_reviews (review_id, review_date, month, "
        "product, category, channel, stars, review_text, "
        "sentiment_score, sentiment) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
    con.commit()
    n = con.execute("SELECT COUNT(*) FROM fact_reviews").fetchone()[0]
    neg = con.execute("SELECT COUNT(*) FROM fact_reviews "
                      "WHERE sentiment = 'Negative'").fetchone()[0]
    con.close()
    print(f"loaded {n} reviews "
          f"({len(products)} products, {len(channels)} channels), "
          f"{neg} negative")


if __name__ == "__main__":
    main()
