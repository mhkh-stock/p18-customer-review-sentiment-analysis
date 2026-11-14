#!/usr/bin/env python3
"""Build the P18 deliverables from the SAMPLE review data.

Recomputes every number from outputs/summary.json (itself recomputed
from the raw CSV by src/analyze.py — nothing is typed in by hand)
and produces:
  * outputs/monthly_sentiment.png — monthly positive vs negative %
    chart (matplotlib)
  * outputs/sentiment_report.pdf — 2-page client report (headline,
    sentiment mix, category + channel tables, monthly trend,
    sentiment-vs-stars cross-tab, complaint themes, 3 recommendations)

Run:  python3 src/build_report.py
"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
SUMMARY = ROOT / "outputs" / "summary.json"
CHART = ROOT / "outputs" / "monthly_sentiment.png"
PDF = ROOT / "outputs" / "sentiment_report.pdf"

s = json.loads(SUMMARY.read_text(encoding="utf-8"))
MIX = s["sentiment_mix"]
TOT = s["total_reviews"]
CATS = s["categories"]
CHS = s["channels"]
MO = s["months"]
CT = s["crosstab"]
THEMES = s["themes"]
ACTS = s["actions"]

# monthly sentiment chart: positive % vs negative % per month
months = [m["month"] for m in MO]
pos = [m["positive_pct"] for m in MO]
neg = [m["negative_pct"] for m in MO]
x = range(len(months))
plt.figure(figsize=(8, 3.2))
plt.bar([i - 0.2 for i in x], pos, width=0.4, label="Positive %",
        color="#2E7D32")
plt.bar([i + 0.2 for i in x], neg, width=0.4, label="Negative %",
        color="#C62828")
plt.xticks(list(x), months)
plt.ylabel("% of reviews")
plt.title("Monthly sentiment — BazaarHub.pk (SAMPLE, Jan–Jun 2026)")
plt.legend()
plt.tight_layout()
plt.savefig(CHART, dpi=150)
plt.close()

styles = getSampleStyleSheet()
hdr = colors.HexColor("#1F4E79")


def table(rows, widths, size=9):
    t = Table(rows, colWidths=widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), hdr),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE", (0, 0), (-1, -1), size),
    ]))
    return t


story = [
    Paragraph("BazaarHub.pk — Customer Review Sentiment Report",
              styles["Title"]),
    Paragraph("Review text analysed with an open lexicon · "
              "1 Jan – 30 Jun 2026 (6 months, 181 days) · SAMPLE data — "
              "fictional online store, generated for this delivery "
              "(seed 20261114)", styles["Normal"]),
    Spacer(1, 0.25 * cm),
    Paragraph(
        f"Headline: <b>{TOT:,} reviews</b> at an average of "
        f"<b>{s['avg_stars']} stars</b>. "
        f"<b>{MIX['positive']:,} are positive ({MIX['positive_pct']}%)</b>, "
        f"<b>{MIX['neutral']:,} neutral ({MIX['neutral_pct']}%)</b> and "
        f"<b>{MIX['negative']:,} negative ({MIX['negative_pct']}%)</b>. "
        f"Stars and text agree in <b>{s['agreement_pct']}%</b> of reviews — "
        f"the {s['disagreement']} where they disagree are the finding, "
        f"not noise.",
        styles["Normal"]),
    Spacer(1, 0.25 * cm),
    Paragraph("<b>Sentiment by product category</b>", styles["Heading2"]),
]
cat_rows = [["Category", "Reviews", "Positive", "Neutral", "Negative",
             "Negative %", "Avg stars"]]
for c in CATS:
    cat_rows.append([c["category"], f"{c['reviews']:,}",
                     f"{c['positive']:,}", f"{c['neutral']:,}",
                     f"{c['negative']:,}", f"{c['negative_pct']}%",
                     f"{c['avg_stars']}"])
story.append(table(cat_rows, [3.6 * cm, 2.0 * cm, 2.2 * cm, 2.2 * cm,
                             2.2 * cm, 2.4 * cm, 2.2 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph(
    f"<b>{s['worst_category']}</b> is the worst category at "
    f"<b>{s['worst_category_negative_pct']}% negative</b>; "
    f"<b>{s['best_category']}</b> is the best at "
    f"<b>{s['best_category_negative_pct']}%</b>. Worst product: "
    f"<b>{s['worst_product']} ({s['worst_product_negative_pct']}% "
    f"negative)</b>; best: {s['best_product']} "
    f"({s['best_product_negative_pct']}%).",
    styles["Normal"]))
story.append(Spacer(1, 0.25 * cm))
story.append(Paragraph("<b>Sentiment by channel</b>", styles["Heading2"]))
ch_rows = [["Channel", "Reviews", "Positive", "Neutral", "Negative",
            "Negative %", "Avg stars"]]
for c in CHS:
    ch_rows.append([c["channel"], f"{c['reviews']:,}",
                    f"{c['positive']:,}", f"{c['neutral']:,}",
                    f"{c['negative']:,}", f"{c['negative_pct']}%",
                    f"{c['avg_stars']}"])
story.append(table(ch_rows, [4.4 * cm, 2.0 * cm, 2.2 * cm, 2.2 * cm,
                            2.2 * cm, 2.4 * cm, 2.2 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph(
    f"<b>{s['worst_channel']}</b> is the most negative channel at "
    f"<b>{s['worst_channel_negative_pct']}% negative</b>, against "
    f"<b>{s['best_channel_negative_pct']}%</b> on "
    f"<b>{s['best_channel']}</b> — the gap is a delivery problem, "
    "not a product problem.",
    styles["Normal"]))
story.append(Spacer(1, 0.25 * cm))
story.append(Paragraph("<b>Month by month — sentiment is improving</b>",
                       styles["Heading2"]))
mo_rows = [["Month", "Reviews", "Positive %", "Negative %", "Avg stars"]]
for m in MO:
    mo_rows.append([m["month"], f"{m['reviews']:,}",
                    f"{m['positive_pct']}%", f"{m['negative_pct']}%",
                    f"{m['avg_stars']}"])
story.append(table(mo_rows, [3.0 * cm, 2.6 * cm, 3.2 * cm, 3.2 * cm,
                            3.0 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(Image(str(CHART), width=15.5 * cm, height=4.2 * cm))
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph(
    f"Negative sentiment moved "
    f"<b>{s['negative_trend_jan_to_jun_points']:+.2f} points from January "
    f"({MO[0]['negative_pct']}%) to June ({MO[-1]['negative_pct']}%)</b> — "
    "the store's delivery fixes are showing up in what customers write.",
    styles["Normal"]))
story.append(Spacer(1, 0.25 * cm))
story.append(Paragraph("<b>Sentiment vs stars — where they disagree</b>",
                       styles["Heading2"]))
ct_rows = [["Sentiment", "1–2 stars", "3 stars", "4–5 stars", "Total"]]
for sent in ["Positive", "Neutral", "Negative"]:
    row = CT[sent]
    ct_rows.append([sent, f"{row['1-2 stars']:,}", f"{row['3 stars']:,}",
                    f"{row['4-5 stars']:,}",
                    f"{sum(row.values()):,}"])
story.append(table(ct_rows, [3.4 * cm, 2.6 * cm, 2.6 * cm, 2.6 * cm,
                            2.6 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph(
    f"<b>{s['five_star_negative']} five-star reviews carry negative "
    f"text</b> and <b>{s['one_star_positive']} one-star reviews carry "
    f"positive text</b>. The first group is usually a customer who "
    "liked the product but hated the delivery — read those reviews "
    "before judging the product.",
    styles["Normal"]))
story.append(Spacer(1, 0.25 * cm))
story.append(Paragraph("<b>What customers complain about</b>",
                       styles["Heading2"]))
th_rows = [["Complaint theme", "Reviews", "% of all",
            "% of negative"]]
for t in THEMES:
    th_rows.append([t["theme"], f"{t['reviews']:,}",
                    f"{t['pct_of_all']}%", f"{t['pct_of_negative']}%"])
story.append(table(th_rows, [5.0 * cm, 2.6 * cm, 3.4 * cm, 4.0 * cm]))
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph(
    f"Top complaint: <b>{s['top_theme']}</b> "
    f"({THEMES[0]['reviews']} reviews). "
    f"{s['reviews_with_a_theme']} reviews mention at least one "
    "complaint theme — counted from the text, not guessed.",
    styles["Normal"]))
story.append(Spacer(1, 0.25 * cm))
story.append(Paragraph("<b>3 recommendations</b>", styles["Heading2"]))
for i, a in enumerate(ACTS, 1):
    story.append(Paragraph(
        f"{i}. <b>{a['title']}.</b> {a['detail']}", styles["Normal"]))
    story.append(Spacer(1, 0.15 * cm))
story.append(Spacer(1, 0.2 * cm))
story.append(Paragraph(
    "Method: every number above is recomputed from "
    "data/raw/reviews_SAMPLE.csv by src/analyze.py using the open "
    "lexicon in src/sentiment.py and verified by src/checks.py. The "
    "workbook carries the same numbers as live formulas. Limits: the "
    "lexicon cannot read sarcasm and misses sentiment in phrases "
    "outside its word lists.",
    styles["Normal"]))
SimpleDocTemplate(str(PDF), pagesize=A4,
                  title="BazaarHub.pk — Customer Review Sentiment "
                        "Report (SAMPLE)",
                  author="Muhammad Hashir",
                  topMargin=1.4 * cm, bottomMargin=1.4 * cm).build(story)
print(f"chart: {CHART}")
print(f"report: {PDF}")
