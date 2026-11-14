#!/usr/bin/env python3
"""Checks as code for P18. Recomputes every headline number from the
raw CSV (scoring each review with the lexicon in src/sentiment.py)
and verifies the JSON, the processed CSVs, the SQL analysis, the
workbook formulas and the LibreOffice recalc against it — four
independent paths that must agree.

    python3 src/checks.py        (after the full pipeline + recalc:
    soffice --headless --calc --convert-to xlsx --outdir outputs/.recalc
    outputs/customer_review_sentiment_report_SAMPLE.xlsx)

Exit code 0 when every check passes, 1 otherwise.
"""
import csv
import json
import re
import sqlite3
import subprocess
import sys
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
SUMMARY = PROJECT / "outputs" / "summary.json"
WORKBOOK = PROJECT / "outputs" / "customer_review_sentiment_report_SAMPLE.xlsx"
RECALC = PROJECT / "outputs" / ".recalc" / "customer_review_sentiment_report_SAMPLE.xlsx"
PDF = PROJECT / "outputs" / "sentiment_report.pdf"
SCHEMA = PROJECT / "sql" / "schema.sql"
QUERIES = PROJECT / "sql" / "analysis_queries.sql"
DB = PROJECT / "data" / "processed" / "reviews.db"
sys.path.insert(0, str(PROJECT / "src"))
from sentiment import THEMES, score_and_classify, themes_in  # noqa: E402

CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Beauty",
              "Grocery"]
CHANNELS = ["Website", "Daraz", "WhatsApp / Instagram"]
MONTHS = [f"2026-{m:02d}" for m in range(1, 7)]
SENTIMENTS = ["Positive", "Neutral", "Negative"]
fails = []
ran = []


def check(name, cond, detail=""):
    ran.append(name)
    print(("PASS " if cond else "FAIL ") + name +
          (f" — {detail}" if detail else ""))
    if not cond:
        fails.append(name)


def pct(n, d):
    return round(100.0 * n / d, 2) if d else 0.0


def breakdown(rows):
    n = len(rows)
    c = Counter(r["sentiment"] for r in rows)
    return {"reviews": n, "positive": c["Positive"],
            "neutral": c["Neutral"], "negative": c["Negative"],
            "positive_pct": pct(c["Positive"], n),
            "neutral_pct": pct(c["Neutral"], n),
            "negative_pct": pct(c["Negative"], n),
            "avg_stars": round(sum(r["stars"] for r in rows) / n, 2)
            if n else 0,
            "avg_score": round(sum(r["score"] for r in rows) / n, 2)
            if n else 0}


raw = list(csv.DictReader(open(RAW / "reviews_SAMPLE.csv", encoding="utf-8")))
reviews = []
for r in raw:
    score, sentiment = score_and_classify(r["review_text"])
    reviews.append({**r, "stars": int(r["stars"]), "score": score,
                    "sentiment": sentiment,
                    "themes": themes_in(r["review_text"])})
total = len(reviews)
mix = breakdown(reviews)
by_cat = {c: breakdown([r for r in reviews if r["category"] == c])
          for c in CATEGORIES}
by_ch = {c: breakdown([r for r in reviews if r["channel"] == c])
         for c in CHANNELS}
by_month = {m: breakdown([r for r in reviews if r["month"] == m])
            for m in MONTHS}
by_prod = {}
for p in sorted({r["product"] for r in reviews}):
    rs = [r for r in reviews if r["product"] == p]
    by_prod[p] = {"category": rs[0]["category"], **breakdown(rs)}
worst_prod = max(by_prod, key=lambda p: by_prod[p]["negative_pct"])
best_prod = min(by_prod, key=lambda p: by_prod[p]["negative_pct"])
theme_counts = {name: sum(1 for r in reviews if name in r["themes"])
                for name in THEMES}
top_theme = max(theme_counts, key=theme_counts.get)
neg_reviews = [r for r in reviews if r["sentiment"] == "Negative"]
themed = sum(1 for r in reviews if r["themes"])
themed_neg = sum(1 for r in neg_reviews if r["themes"])


def band(stars):
    return "1-2 stars" if stars <= 2 else (
        "3 stars" if stars == 3 else "4-5 stars")


crosstab = {s: {b: sum(1 for r in reviews
                       if r["sentiment"] == s and band(r["stars"]) == b)
                for b in ["1-2 stars", "3 stars", "4-5 stars"]}
            for s in SENTIMENTS}
agree = (crosstab["Positive"]["4-5 stars"]
         + crosstab["Neutral"]["3 stars"]
         + crosstab["Negative"]["1-2 stars"])
agreement_pct = pct(agree, total)
five_neg = sum(1 for r in reviews
               if r["stars"] == 5 and r["sentiment"] == "Negative")
one_pos = sum(1 for r in reviews
              if r["stars"] == 1 and r["sentiment"] == "Positive")

# ── raw file ───────────────────────────────────────────────────────────
check("review rows = 780", total == 780, str(total))
check("dates span 2026-01-01..2026-06-30",
      min(r["date"] for r in reviews) == "2026-01-01" and
      max(r["date"] for r in reviews) == "2026-06-30")
check("6 distinct months",
      sorted({r["month"] for r in reviews}) == MONTHS)
check("5 categories only",
      {r["category"] for r in reviews} == set(CATEGORIES))
check("3 channels only",
      {r["channel"] for r in reviews} == set(CHANNELS))
check("15 products only", len({r["product"] for r in reviews}) == 15)
check("stars all in 1..5",
      all(1 <= r["stars"] <= 5 for r in reviews))
check("no empty review text",
      all(r["review_text"].strip() for r in reviews))
check("review_ids unique",
      len({r["review_id"] for r in reviews}) == total)
check("review_ids are RB-####",
      all(re.fullmatch(r"RB-\d{4}", r["review_id"]) for r in reviews))
check("each product maps to exactly one category",
      all(len({r["category"] for r in reviews if r["product"] == p}) == 1
          for p in by_prod))
check("month matches the date prefix",
      all(r["month"] == r["date"][:7] for r in reviews))
check("every product has >= 20 reviews",
      min(v["reviews"] for v in by_prod.values()) >= 20,
      str(min(v["reviews"] for v in by_prod.values())))
check("every channel has >= 100 reviews",
      min(v["reviews"] for v in by_ch.values()) >= 100,
      str(min(v["reviews"] for v in by_ch.values())))
check("every month has >= 90 reviews",
      min(v["reviews"] for v in by_month.values()) >= 90,
      str(min(v["reviews"] for v in by_month.values())))

# ── recompute: the mix, the trend, the cross-tab ───────────────────────
check("positive + neutral + negative = total",
      mix["positive"] + mix["neutral"] + mix["negative"] == total)
check("positive share is 52.31%",
      mix["positive_pct"] == 52.31, str(mix["positive_pct"]))
check("negative share is 27.82%",
      mix["negative_pct"] == 27.82, str(mix["negative_pct"]))
check("average stars = 3.37", mix["avg_stars"] == 3.37,
      str(mix["avg_stars"]))
check("average sentiment score = 1.48", mix["avg_score"] == 1.48,
      str(mix["avg_score"]))
for c in CATEGORIES:
    check(f"category {c}: negative % recomputes",
          by_cat[c]["negative_pct"] == pct(by_cat[c]["negative"],
                                           by_cat[c]["reviews"]),
          str(by_cat[c]["negative_pct"]))
check("worst category = Electronics",
      max(by_cat, key=lambda c: by_cat[c]["negative_pct"]) == "Electronics")
check("best category = Grocery",
      min(by_cat, key=lambda c: by_cat[c]["negative_pct"]) == "Grocery")
for c in CHANNELS:
    check(f"channel {c}: negative % recomputes",
          by_ch[c]["negative_pct"] == pct(by_ch[c]["negative"],
                                          by_ch[c]["reviews"]),
          str(by_ch[c]["negative_pct"]))
check("worst channel = Daraz",
      max(by_ch, key=lambda c: by_ch[c]["negative_pct"]) == "Daraz")
check("best channel = WhatsApp / Instagram",
      min(by_ch, key=lambda c: by_ch[c]["negative_pct"])
      == "WhatsApp / Instagram")
for m in MONTHS:
    check(f"month {m}: negative % recomputes",
          by_month[m]["negative_pct"] == pct(by_month[m]["negative"],
                                             by_month[m]["reviews"]),
          str(by_month[m]["negative_pct"]))
check("negative trend Jan->Jun = -8.82 points",
      round(by_month["2026-06"]["negative_pct"]
            - by_month["2026-01"]["negative_pct"], 2) == -8.82)
check("worst product = AirBuds Pro at 46.27%",
      worst_prod == "AirBuds Pro" and
      by_prod[worst_prod]["negative_pct"] == 46.27,
      str(by_prod[worst_prod]["negative_pct"]))
check("best product = Basmati Rice 5kg at 15.0%",
      best_prod == "Basmati Rice 5kg" and
      by_prod[best_prod]["negative_pct"] == 15.0,
      str(by_prod[best_prod]["negative_pct"]))
check("agreement = 89.87%", agreement_pct == 89.87,
      str(agreement_pct))
check("five-star reviews with negative text = 5", five_neg == 5,
      str(five_neg))
check("one-star reviews with positive text = 5", one_pos == 5,
      str(one_pos))
check("crosstab rows sum to the mix",
      all(sum(crosstab[s].values()) == mix[s.lower()] for s in SENTIMENTS))
for name in THEMES:
    check(f"theme {name}: count recomputes from text",
          theme_counts[name] == sum(
              1 for r in reviews
              if any(p in r["review_text"].lower()
                     for p in THEMES[name])),
          str(theme_counts[name]))
check("top theme = Damaged product (121)",
      top_theme == "Damaged product" and theme_counts[top_theme] == 121)
check("themed reviews counted once per review",
      themed == sum(1 for r in reviews if r["themes"]), str(themed))
check("negative reviews with a theme = 203",
      themed_neg == 203, str(themed_neg))
check("every themed review is a negative review (themes are "
      "complaint phrases)", themed_neg == themed, str(themed_neg))

# ── summary JSON + processed CSVs ──────────────────────────────────────
s = json.loads(SUMMARY.read_text(encoding="utf-8"))
check("JSON total reviews = 780", s["total_reviews"] == total)
check("JSON mix matches recompute",
      s["sentiment_mix"]["positive"] == mix["positive"] and
      s["sentiment_mix"]["negative"] == mix["negative"])
check("JSON avg stars = 3.37", s["avg_stars"] == 3.37)
check("JSON worst product = AirBuds Pro",
      s["worst_product"] == "AirBuds Pro")
check("JSON best product = Basmati Rice 5kg",
      s["best_product"] == "Basmati Rice 5kg")
check("JSON worst category = Electronics",
      s["worst_category"] == "Electronics")
check("JSON worst channel = Daraz", s["worst_channel"] == "Daraz")
check("JSON agreement = 89.87%", s["agreement_pct"] == 89.87)
check("JSON five-star-negative = 5", s["five_star_negative"] == 5)
check("JSON one-star-positive = 5", s["one_star_positive"] == 5)
check("JSON top theme = Damaged product",
      s["top_theme"] == "Damaged product")
check("JSON categories match recompute",
      all(c["negative"] == by_cat[c["category"]]["negative"]
          and c["negative_pct"] == by_cat[c["category"]]["negative_pct"]
          for c in s["categories"]))
check("JSON channels match recompute",
      all(c["negative"] == by_ch[c["channel"]]["negative"]
          for c in s["channels"]))
check("JSON months match recompute",
      all(m["negative"] == by_month[m["month"]]["negative"]
          and m["negative_pct"] == by_month[m["month"]]["negative_pct"]
          for m in s["months"]))
check("JSON themes match recompute",
      all(t["reviews"] == theme_counts[t["theme"]] for t in s["themes"]))
check("JSON crosstab matches recompute",
      s["crosstab"] == crosstab, str(s["crosstab"]))
check("JSON has 3 actions", len(s["actions"]) == 3)
check("JSON action 1 names the worst product",
      worst_prod in s["actions"][0]["title"])
check("JSON action 2 names the top theme",
      top_theme.lower() in s["actions"][1]["title"].lower())


def read_csv(name):
    return list(csv.DictReader(open(
        PROJECT / "data" / "processed" / name, encoding="utf-8")))


scored = read_csv("reviews_scored.csv")
check("reviews_scored.csv has 780 rows", len(scored) == 780)
check("reviews_scored first row score matches lexicon",
      int(scored[0]["sentiment_score"]) ==
      score_and_classify(scored[0]["review_text"])[0])
check("reviews_scored sentiments match lexicon throughout",
      all(r["sentiment"] == score_and_classify(r["review_text"])[1]
          for r in scored))
ccsv = read_csv("category_summary.csv")
check("category CSV has 5 rows", len(ccsv) == 5)
check("category CSV negative counts match recompute",
      all(int(r["negative"]) == by_cat[r["category"]]["negative"]
          for r in ccsv))
chcsv = read_csv("channel_summary.csv")
check("channel CSV has 3 rows", len(chcsv) == 3)
check("channel CSV negative counts match recompute",
      all(int(r["negative"]) == by_ch[r["channel"]]["negative"]
          for r in chcsv))
mcsv = read_csv("monthly_summary.csv")
check("monthly CSV has 6 rows", len(mcsv) == 6)
check("monthly CSV negative counts match recompute",
      all(int(r["negative"]) == by_month[r["month"]]["negative"]
          for r in mcsv))
pcsv = read_csv("product_summary.csv")
check("product CSV has 15 rows", len(pcsv) == 15)
check("product CSV worst row = AirBuds Pro",
      pcsv[0]["product"] == "AirBuds Pro")
tcsv = read_csv("theme_summary.csv")
check("theme CSV has 8 rows", len(tcsv) == 8)
check("theme CSV counts match recompute",
      all(int(r["reviews"]) == theme_counts[r["theme"]] for r in tcsv))

# ── SQL analysis (in-memory, same schema + same CSVs) ──────────────────
con = sqlite3.connect(":memory:")
con.executescript(SCHEMA.read_text())
con.executemany("INSERT INTO dim_product VALUES (?, ?)",
                sorted({(r["product"], r["category"]) for r in reviews}))
con.executemany("INSERT INTO dim_channel VALUES (?)",
                [(c,) for c in sorted({r["channel"] for r in reviews})])
con.executemany(
    "INSERT INTO fact_reviews (review_id, review_date, month, product, "
    "category, channel, stars, review_text, sentiment_score, sentiment) "
    "VALUES (?,?,?,?,?,?,?,?,?,?)",
    [(r["review_id"], r["date"], r["month"], r["product"], r["category"],
      r["channel"], r["stars"], r["review_text"], r["score"],
      r["sentiment"]) for r in reviews])
blocks = re.split(r"^-- Q\d+:.*$", QUERIES.read_text(),
                  flags=re.MULTILINE)
queries = []
for b in blocks:
    lines = [ln for ln in b.splitlines()
             if not ln.strip().startswith("--")]
    body = "\n".join(lines).strip()
    if body.startswith("SELECT") or body.startswith("WITH"):
        queries.append(body)
check("analysis_queries.sql has 7 queries", len(queries) == 7,
      str(len(queries)))
q1 = con.execute(queries[0]).fetchall()
check("SQL Q1: 3 sentiment rows", len(q1) == 3)
check("SQL Q1 counts match recompute",
      {row[0]: row[1] for row in q1} ==
      {"Positive": mix["positive"], "Neutral": mix["neutral"],
       "Negative": mix["negative"]}, str(q1))
q2 = con.execute(queries[1]).fetchall()
check("SQL Q2: 5 categories", len(q2) == 5)
check("SQL Q2 negative % matches recompute",
      all(row[5] == by_cat[row[0]]["negative_pct"] for row in q2))
q3 = con.execute(queries[2]).fetchall()
check("SQL Q3: 3 channels", len(q3) == 3)
check("SQL Q3 negative % matches recompute",
      all(row[5] == by_ch[row[0]]["negative_pct"] for row in q3))
q4 = con.execute(queries[3]).fetchall()
check("SQL Q4: 6 months", len(q4) == 6)
check("SQL Q4 negative % matches recompute",
      all(row[6] == by_month[row[0]]["negative_pct"] for row in q4))
q5 = con.execute(queries[4]).fetchall()
check("SQL Q5: 9 cross-tab cells", len(q5) == 9, str(len(q5)))
check("SQL Q5 cells match recompute",
      all(row[2] == crosstab[row[0]][row[1]] for row in q5))
q6 = con.execute(queries[5]).fetchall()
check("SQL Q6: 8 themes", len(q6) == 8, str(len(q6)))
check("SQL Q6 theme counts match recompute",
      all(row[1] == theme_counts[row[0]] for row in q6), str(q6))
q7 = con.execute(queries[6]).fetchall()
check("SQL Q7: 15 products, worst = AirBuds Pro",
      len(q7) == 15 and q7[0][0] == "AirBuds Pro", str(len(q7)))
check("SQL Q7 negative % matches recompute",
      all(row[4] == by_prod[row[0]]["negative_pct"] for row in q7))
con.close()

# ── on-disk SQLite db ──────────────────────────────────────────────────
check("reviews.db exists", DB.exists())
if DB.exists():
    con = sqlite3.connect(DB)
    check("db review rows = 780",
          con.execute("SELECT COUNT(*) FROM fact_reviews")
          .fetchone()[0] == 780)
    check("db negative reviews = 217",
          con.execute("SELECT COUNT(*) FROM fact_reviews "
                      "WHERE sentiment = 'Negative'").fetchone()[0] == 217)
    check("db avg stars = 3.37",
          round(con.execute("SELECT AVG(stars) FROM fact_reviews")
                .fetchone()[0], 2) == 3.37)
    con.close()

# ── workbook (formulas) ────────────────────────────────────────────────
wb = load_workbook(WORKBOOK)
check("sheets = Dashboard, Reviews, Sentiment by Category, "
      "Sentiment by Channel, Monthly Trend, Themes, Method",
      wb.sheetnames == ["Dashboard", "Reviews", "Sentiment by Category",
                        "Sentiment by Channel", "Monthly Trend", "Themes",
                        "Method"], str(wb.sheetnames))
rv = wb["Reviews"]
check("Reviews rows = 781 incl header", rv.max_row == 781,
      str(rv.max_row))
check("Reviews header has 19 columns", rv.max_column == 19,
      str(rv.max_column))
check("Reviews A2 = RB-0001", rv["A2"].value == "RB-0001",
      str(rv["A2"].value))
check("Reviews I2/J2 match the lexicon for row 2",
      rv["I2"].value == score_and_classify(rv["H2"].value)[0] and
      rv["J2"].value == score_and_classify(rv["H2"].value)[1],
      f"{rv['I2'].value}/{rv['J2'].value}")
check("Reviews K2 is a SEARCH theme-flag formula",
      isinstance(rv["K2"].value, str) and
      rv["K2"].value.startswith("=--OR(ISNUMBER(SEARCH("),
      str(rv["K2"].value))
check("Reviews S2 flags a themed review",
      rv["S2"].value == "=--(SUM(K2:R2)>0)", str(rv["S2"].value))
check("Reviews sentiment values are Positive/Neutral/Negative only",
      {rv.cell(row=r, column=10).value for r in range(2, 782)}
      <= {"Positive", "Neutral", "Negative"})
dash = wb["Dashboard"]
check("Dashboard B5 is a COUNTA formula over Reviews",
      dash["B5"].value == f"=COUNTA(Reviews!A2:A{total + 1})",
      str(dash["B5"].value))
check("Dashboard B6 is a COUNTIF for Positive",
      dash["B6"].value == f'=COUNTIF(Reviews!J2:J{total + 1},"Positive")',
      str(dash["B6"].value))
check("Dashboard B9 is the negative % formula",
      dash["B9"].value == "=B8/B5", str(dash["B9"].value))
check("Dashboard B13 is the agreement formula (3 COUNTIFS)",
      isinstance(dash["B13"].value, str) and
      dash["B13"].value.count("COUNTIFS") == 3, str(dash["B13"].value))
check("Dashboard B14 counts 5-star negative reviews",
      isinstance(dash["B14"].value, str) and
      "COUNTIFS" in dash["B14"].value and ",5," in dash["B14"].value,
      str(dash["B14"].value))
check("Dashboard B18 is a COUNTIFS over Reviews month",
      isinstance(dash["B18"].value, str) and
      dash["B18"].value.startswith("=COUNTIFS(Reviews!$C$"),
      str(dash["B18"].value))
check("Dashboard B26 uses _xlfn.MAXIFS",
      isinstance(dash["B26"].value, str) and
      dash["B26"].value.startswith("=_xlfn.MAXIFS("),
      str(dash["B26"].value))
check("Dashboard B27 uses _xlfn.MINIFS",
      isinstance(dash["B27"].value, str) and
      dash["B27"].value.startswith("=_xlfn.MINIFS("),
      str(dash["B27"].value))
check("Dashboard has a chart", len(dash._charts) >= 1)
cat = wb["Sentiment by Category"]
check("Category B4 is a COUNTIFS over Reviews category",
      isinstance(cat["B4"].value, str) and
      cat["B4"].value.startswith("=COUNTIFS(Reviews!$E$"),
      str(cat["B4"].value))
check("Category total row uses SUM",
      cat["B9"].value == "=SUM(B4:B8)", str(cat["B9"].value))
ch_ws = wb["Sentiment by Channel"]
check("Channel B4 is a COUNTIFS over Reviews channel",
      isinstance(ch_ws["B4"].value, str) and
      ch_ws["B4"].value.startswith("=COUNTIFS(Reviews!$F$"),
      str(ch_ws["B4"].value))
check("Channel total row uses SUM",
      ch_ws["B7"].value == "=SUM(B4:B6)", str(ch_ws["B7"].value))
mo_ws = wb["Monthly Trend"]
check("Monthly B4 is a COUNTIFS over Reviews month",
      isinstance(mo_ws["B4"].value, str) and
      mo_ws["B4"].value.startswith("=COUNTIFS(Reviews!$C$"),
      str(mo_ws["B4"].value))
check("Monthly total row uses SUM",
      mo_ws["B10"].value == "=SUM(B4:B9)", str(mo_ws["B10"].value))
th_ws = wb["Themes"]
check("Themes B4 is a SUM over the Reviews flag column",
      th_ws["B4"].value == f"=SUM(Reviews!K2:K{total + 1})",
      str(th_ws["B4"].value))
check("Themes D4 is a SUMIFS for negative reviews",
      isinstance(th_ws["D4"].value, str) and
      th_ws["D4"].value.startswith("=SUMIFS(Reviews!K2:"),
      str(th_ws["D4"].value))
check("Themes B13 sums the has_theme flag",
      th_ws["B13"].value == f"=SUM(Reviews!S2:S{total + 1})",
      str(th_ws["B13"].value))
check("Method sheet mentions _xlfn.",
      any("_xlfn." in (wb["Method"].cell(row=r, column=2).value or "")
          for r in range(3, 12)))

# ── LibreOffice recalculated values ────────────────────────────────────
if RECALC.exists():
    wb2 = load_workbook(RECALC, data_only=True)
    d2 = wb2["Dashboard"]
    check("recalc Dashboard total reviews = 780",
          d2["B5"].value == 780, str(d2["B5"].value))
    check("recalc Dashboard positive = 408",
          d2["B6"].value == 408, str(d2["B6"].value))
    check("recalc Dashboard neutral = 155",
          d2["B7"].value == 155, str(d2["B7"].value))
    check("recalc Dashboard negative = 217",
          d2["B8"].value == 217, str(d2["B8"].value))
    check("recalc Dashboard negative % ≈ 27.82%",
          abs(d2["B9"].value - 0.2782) < 0.0005, str(d2["B9"].value))
    check("recalc Dashboard avg stars ≈ 3.37",
          abs(d2["B11"].value - 3.37) < 0.005, str(d2["B11"].value))
    check("recalc Dashboard agreement ≈ 89.87%",
          abs(d2["B13"].value - 0.8987) < 0.0005, str(d2["B13"].value))
    check("recalc Dashboard five-star-negative = 5",
          d2["B14"].value == 5, str(d2["B14"].value))
    check("recalc monthly Jan negative ≈ 33.98%",
          abs(d2["F18"].value - 0.3398) < 0.0005, str(d2["F18"].value))
    check("recalc monthly Jun negative ≈ 25.16%",
          abs(d2["F23"].value - 0.2516) < 0.0005, str(d2["F23"].value))
    check("recalc monthly TOTAL reviews = 780",
          d2["B24"].value == 780, str(d2["B24"].value))
    check("recalc worst month negative % ≈ 33.98%",
          abs(d2["B26"].value - 0.3398) < 0.0005, str(d2["B26"].value))
    check("recalc worst month = 2026-01",
          d2["C26"].value == "2026-01", str(d2["C26"].value))
    check("recalc best month negative % ≈ 22.73%",
          abs(d2["B27"].value - 0.2273) < 0.0005, str(d2["B27"].value))
    check("recalc best month = 2026-04",
          d2["C27"].value == "2026-04", str(d2["C27"].value))
    c2 = wb2["Sentiment by Category"]
    check("recalc Category TOTAL reviews = 780",
          c2["B9"].value == 780, str(c2["B9"].value))
    check("recalc Category TOTAL negative = 217",
          c2["E9"].value == 217, str(c2["E9"].value))
    check("recalc Electronics negative % ≈ 39.18%",
          abs(c2["F4"].value - 0.3918) < 0.0005, str(c2["F4"].value))
    check("recalc Grocery negative % ≈ 22.86%",
          abs(c2["F8"].value - 0.2286) < 0.0005, str(c2["F8"].value))
    h2 = wb2["Sentiment by Channel"]
    check("recalc Channel TOTAL reviews = 780",
          h2["B7"].value == 780, str(h2["B7"].value))
    check("recalc Daraz negative % ≈ 32.96%",
          abs(h2["F5"].value - 0.3296) < 0.0005, str(h2["F5"].value))
    m2 = wb2["Monthly Trend"]
    check("recalc Monthly TOTAL reviews = 780",
          m2["B10"].value == 780, str(m2["B10"].value))
    check("recalc Monthly TOTAL negative = 217",
          m2["E10"].value == 217, str(m2["E10"].value))
    t2 = wb2["Themes"]
    check("recalc Themes Damaged product = 121",
          t2["B5"].value == 121, str(t2["B5"].value))
    check("recalc Themes Late delivery = 33",
          t2["B4"].value == 33, str(t2["B4"].value))
    check("recalc Themes Price = 79",
          t2["B7"].value == 79, str(t2["B7"].value))
    check("recalc Themes themed reviews = 203",
          t2["B13"].value == 203, str(t2["B13"].value))
    r2 = wb2["Reviews"]
    check("recalc Reviews has_theme flags sum to 203",
          sum(r2.cell(row=r, column=19).value or 0 for r in range(2, 782))
          == 203)
    errors = []
    for ws in wb2.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith("#"):
                    errors.append(f"{ws.title}!{cell.coordinate}={cell.value}")
    check("recalc workbook has no error values (#NAME?, #VALUE!, ...)",
          not errors, "; ".join(errors[:5]))
else:
    print(f"  NOTE: no LibreOffice recalc copy found at {RECALC} — "
          "recalc checks skipped")

# ── PDF ────────────────────────────────────────────────────────────────
check("sentiment_report.pdf exists", PDF.exists())
if PDF.exists():
    info = subprocess.run(["pdfinfo", str(PDF)], capture_output=True,
                          text=True)
    pages = re.search(r"Pages:\s+(\d+)", info.stdout)
    check("PDF has exactly 2 pages",
          pages is not None and int(pages.group(1)) == 2,
          info.stdout.splitlines()[0] if info.stdout else "pdfinfo failed")
    text = subprocess.run(["pdftotext", str(PDF), "-"], capture_output=True,
                          text=True).stdout
    check("PDF text contains total reviews",
          "780" in text)
    check("PDF text contains worst product",
          "AirBuds Pro" in text)
    check("PDF text contains top theme",
          "Damaged product" in text)

print(f"\n{len(ran) - len(fails)}/{len(ran)} checks passed")
if fails:
    print("FAILURES:", fails)
    sys.exit(1)
