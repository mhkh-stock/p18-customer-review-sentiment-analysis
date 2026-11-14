#!/usr/bin/env python3
"""P18 — build the deliverable workbook for BazaarHub.pk:

  Dashboard              — KPIs + monthly sentiment trend, all live
                           formulas over Reviews; best/worst month
                           negative % via MAXIFS/MINIFS (written with
                           the _xlfn. prefix so LibreOffice and Excel
                           calculate them)
  Sentiment by Category  — 5 categories, live COUNTIFS over Reviews
  Sentiment by Channel   — 3 channels, live COUNTIFS over Reviews
  Monthly Trend          — 6 months, live COUNTIFS over Reviews
  Themes                 — 8 complaint themes, live SUMs over the
                           theme-flag formulas on Reviews
  Reviews                — all 780 reviews (values for the scored
                           columns, live SEARCH formulas for the
                           per-theme flags)
  Method                 — how to read it, the lexicon and its limits,
                           how to re-verify

    python3 src/build_workbook.py
"""
import csv
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Font, PatternFill

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
OUT = PROJECT / "outputs" / "customer_review_sentiment_report_SAMPLE.xlsx"
sys.path.insert(0, str(PROJECT / "src"))
from sentiment import THEMES, score_and_classify  # noqa: E402

CATEGORIES = ["Electronics", "Fashion", "Home & Kitchen", "Beauty",
              "Grocery"]
CHANNELS = ["Website", "Daraz", "WhatsApp / Instagram"]
MONTHS = [f"2026-{m:02d}" for m in range(1, 7)]
THEME_NAMES = list(THEMES)
HDR_FILL = PatternFill("solid", fgColor="1F4E79")
HDR_FONT = Font(bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(bold=True, size=14, color="1F4E79")
COUNT_FMT = "#,##0"
PCT_FMT = "0.00%"
AVG_FMT = "0.00"


def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT


def theme_flag_formula(col_letter, row, phrases):
    """Live 0/1 flag: does this review's text contain any phrase of
    the theme? One flag per review per theme, so a review that
    mentions 'damaged' twice still counts once."""
    parts = ",".join(
        f'ISNUMBER(SEARCH("{p}",$H{row}))' for p in phrases)
    return f"=--OR({parts})"


def main():
    raw = list(csv.DictReader(
        open(RAW / "reviews_SAMPLE.csv", encoding="utf-8")))
    n = len(raw)
    last = n + 1  # last data row on Reviews (row 1 = header)
    theme_cols = [chr(ord("K") + i) for i in range(len(THEME_NAMES))]

    wb = Workbook()

    # ── Reviews (values for scored columns, formulas for theme flags) ──
    rev = wb.active
    rev.title = "Reviews"
    rev.append(["review_id", "date", "month", "product", "category",
                "channel", "stars", "review_text", "sentiment_score",
                "sentiment"] + THEME_NAMES + ["has_theme"])
    for r in raw:
        score, sentiment = score_and_classify(r["review_text"])
        rev.append([r["review_id"], r["date"], r["month"], r["product"],
                    r["category"], r["channel"], int(r["stars"]),
                    r["review_text"], score, sentiment])
    for i, r in enumerate(raw, start=2):
        for j, name in enumerate(THEME_NAMES):
            col = theme_cols[j]
            rev.cell(row=i, column=11 + j).value = theme_flag_formula(
                col, i, THEMES[name])
        rev.cell(row=i, column=19).value = f"=--(SUM(K{i}:R{i})>0)"
    style_header(rev, 19)
    rev.freeze_panes = "A2"
    widths = {"A": 11, "B": 12, "C": 9, "D": 24, "E": 15, "F": 20,
              "G": 8, "H": 80, "I": 15, "J": 11}
    for col, w in widths.items():
        rev.column_dimensions[col].width = w
    for col in theme_cols + ["S"]:
        rev.column_dimensions[col].width = 10
    for r in range(2, last + 1):
        rev.cell(row=r, column=8).alignment = Alignment(
            wrap_text=True, vertical="top")
        rev.cell(row=r, column=7).number_format = COUNT_FMT
        rev.cell(row=r, column=9).number_format = COUNT_FMT

    # ── Dashboard ──────────────────────────────────────────────────────
    dash = wb.create_sheet("Dashboard", 0)
    dash["A1"] = "Customer Review Sentiment — BazaarHub.pk (SAMPLE)"
    dash["A1"].font = TITLE_FONT
    dash["A2"] = ("6 months, 2026-01-01 → 2026-06-30 · every number below "
                  "is a live formula over the Reviews sheet — change the "
                  "data and the report rebuilds itself. Sentiment is "
                  "scored by the open lexicon in src/sentiment.py.")
    dash["A2"].font = Font(italic=True, size=10, color="595959")
    dash["A4"] = "Key metrics"
    dash["A4"].font = Font(bold=True, size=12, color="1F4E79")
    kpis = [
        ("Total reviews", f"=COUNTA(Reviews!A2:A{last})", COUNT_FMT),
        ("Positive reviews",
         f'=COUNTIF(Reviews!J2:J{last},"Positive")', COUNT_FMT),
        ("Neutral reviews",
         f'=COUNTIF(Reviews!J2:J{last},"Neutral")', COUNT_FMT),
        ("Negative reviews",
         f'=COUNTIF(Reviews!J2:J{last},"Negative")', COUNT_FMT),
        ("Negative %", "=B8/B5", PCT_FMT),
        ("Positive %", "=B6/B5", PCT_FMT),
        ("Average stars", f"=AVERAGE(Reviews!G2:G{last})", AVG_FMT),
        ("Average sentiment score",
         f"=AVERAGE(Reviews!I2:I{last})", AVG_FMT),
        ("Star / sentiment agreement",
         f'=(COUNTIFS(Reviews!J2:J{last},"Positive",Reviews!G2:G{last},'
         f'">=4")+COUNTIFS(Reviews!J2:J{last},"Neutral",Reviews!G2:G{last},'
         f'3)+COUNTIFS(Reviews!J2:J{last},"Negative",Reviews!G2:G{last},'
         f'"<=2"))/B5', PCT_FMT),
        ("Five-star reviews with negative text",
         f'=COUNTIFS(Reviews!G2:G{last},5,Reviews!J2:J{last},"Negative")',
         COUNT_FMT),
    ]
    for i, (label, formula, fmt) in enumerate(kpis):
        r = 5 + i
        dash.cell(row=r, column=1, value=label)
        c = dash.cell(row=r, column=2, value=formula)
        c.number_format = fmt
        c.font = Font(bold=True)
    # KPI rows: 5 total, 6 positive, 7 neutral, 8 negative, 9 neg %,
    # 10 pos %, 11 avg stars, 12 avg score, 13 agreement, 14 five-star-neg
    dash.column_dimensions["A"].width = 38
    dash.column_dimensions["B"].width = 18
    dash.column_dimensions["C"].width = 44
    dash["C5"] = "One row per customer review on the Reviews sheet."
    dash["C9"] = "Share of reviews whose text scores Negative."
    dash["C13"] = ("Positive text with 4–5 stars, neutral with 3, "
                   "negative with 1–2 — the rest is the finding.")
    dash["C14"] = "Customers who liked the product, hated the delivery."

    tr = 16  # monthly trend title row
    dash.cell(row=tr, column=1, value="Monthly sentiment trend").font = Font(
        bold=True, size=12, color="1F4E79")
    headers = ["Month", "Reviews", "Positive", "Neutral", "Negative",
               "Negative %", "Avg stars"]
    for c, h in enumerate(headers, start=1):
        dash.cell(row=tr + 1, column=c, value=h)
    style_header(dash, 7, row=tr + 1)
    dash.freeze_panes = "A18"
    for i, m in enumerate(MONTHS):
        r = tr + 2 + i  # rows 18..23
        dash.cell(row=r, column=1, value=m)
        dash.cell(row=r, column=2).value = (
            f"=COUNTIFS(Reviews!$C$2:$C${last},$A{r})")
        dash.cell(row=r, column=3).value = (
            f"=COUNTIFS(Reviews!$C$2:$C${last},$A{r},"
            f'Reviews!$J$2:$J${last},"Positive")')
        dash.cell(row=r, column=4).value = (
            f"=COUNTIFS(Reviews!$C$2:$C${last},$A{r},"
            f'Reviews!$J$2:$J${last},"Neutral")')
        dash.cell(row=r, column=5).value = (
            f"=COUNTIFS(Reviews!$C$2:$C${last},$A{r},"
            f'Reviews!$J$2:$J${last},"Negative")')
        dash.cell(row=r, column=6).value = f"=IF(B{r}=0,0,E{r}/B{r})"
        dash.cell(row=r, column=6).number_format = PCT_FMT
        dash.cell(row=r, column=7).value = (
            f"=AVERAGEIFS(Reviews!$G$2:$G${last},"
            f"Reviews!$C$2:$C${last},$A{r})")
        dash.cell(row=r, column=7).number_format = AVG_FMT
    t = tr + 2 + len(MONTHS)  # total row = 24
    dash.cell(row=t, column=1, value="TOTAL (6 months)").font = Font(bold=True)
    for col, letter in [(2, "B"), (3, "C"), (4, "D"), (5, "E")]:
        dash.cell(row=t, column=col).value = (
            f"=SUM({letter}{tr+2}:{letter}{t-1})")
    dash.cell(row=t, column=6).value = f"=E{t}/B{t}"
    dash.cell(row=t, column=6).number_format = PCT_FMT
    dash.cell(row=t, column=7).value = f"=AVERAGE(Reviews!G2:G{last})"
    dash.cell(row=t, column=7).number_format = AVG_FMT

    # best / worst month by negative % via MAXIFS / MINIFS
    bw = t + 2  # row 26
    dash.cell(row=bw, column=1,
             value="Worst month negative %").font = Font(bold=True)
    dash.cell(row=bw, column=2).value = (
        f"=_xlfn.MAXIFS(F{tr+2}:F{t-1},B{tr+2}:B{t-1},\">0\")")
    dash.cell(row=bw, column=2).number_format = PCT_FMT
    dash.cell(row=bw, column=3).value = (
        f"=INDEX(A{tr+2}:A{t-1},MATCH(B{bw},F{tr+2}:F{t-1},0))")
    dash.cell(row=bw + 1, column=1,
             value="Best month negative %").font = Font(bold=True)
    dash.cell(row=bw + 1, column=2).value = (
        f"=_xlfn.MINIFS(F{tr+2}:F{t-1},B{tr+2}:B{t-1},\">0\")")
    dash.cell(row=bw + 1, column=2).number_format = PCT_FMT
    dash.cell(row=bw + 1, column=3).value = (
        f"=INDEX(A{tr+2}:A{t-1},MATCH(B{bw+1},F{tr+2}:F{t-1},0))")
    for col, w in zip("ABCDEFG", [14, 13, 12, 12, 12, 12, 12]):
        dash.column_dimensions[col].width = w

    chart = BarChart()
    chart.type = "col"
    chart.title = "Negative % of reviews by month"
    chart.y_axis.title = "% negative"
    chart.x_axis.title = "Month"
    chart.data = Reference(dash, min_col=6, min_row=tr + 1, max_row=t - 1)
    chart.categories = Reference(dash, min_col=1, min_row=tr + 2,
                                 max_row=t - 1)
    chart.height, chart.width = 7.5, 15
    dash.add_chart(chart, f"A{bw + 3}")

    # ── shared summary-sheet builder (category / channel / month) ──────
    def summary_sheet(name, title, labels, key_col, key_letter, nrows):
        ws = wb.create_sheet(name)
        ws["A1"] = title
        ws["A1"].font = TITLE_FONT
        for c, h in enumerate(["Label", "Reviews", "Positive", "Neutral",
                               "Negative", "Negative %", "Positive %",
                               "Avg stars", "Avg score"], start=1):
            ws.cell(row=3, column=c, value=h)
        style_header(ws, 9, row=3)
        ws.freeze_panes = "A4"
        for i, label in enumerate(labels):
            r = 4 + i
            ws.cell(row=r, column=1, value=label)
            ws.cell(row=r, column=2).value = (
                f"=COUNTIFS(Reviews!${key_letter}$2:${key_letter}${last},"
                f"$A{r})")
            for col, sent in [(3, "Positive"), (4, "Neutral"),
                              (5, "Negative")]:
                ws.cell(row=r, column=col).value = (
                    f"=COUNTIFS(Reviews!${key_letter}$2:${key_letter}${last},"
                    f'$A{r},Reviews!$J$2:$J${last},"{sent}")')
            ws.cell(row=r, column=6).value = f"=IF(B{r}=0,0,E{r}/B{r})"
            ws.cell(row=r, column=6).number_format = PCT_FMT
            ws.cell(row=r, column=7).value = f"=IF(B{r}=0,0,C{r}/B{r})"
            ws.cell(row=r, column=7).number_format = PCT_FMT
            ws.cell(row=r, column=8).value = (
                f"=AVERAGEIFS(Reviews!$G$2:$G${last},"
                f"Reviews!${key_letter}$2:${key_letter}${last},$A{r})")
            ws.cell(row=r, column=8).number_format = AVG_FMT
            ws.cell(row=r, column=9).value = (
                f"=AVERAGEIFS(Reviews!$I$2:$I${last},"
                f"Reviews!${key_letter}$2:${key_letter}${last},$A{r})")
            ws.cell(row=r, column=9).number_format = AVG_FMT
        t = 4 + nrows  # total row
        ws.cell(row=t, column=1, value="TOTAL").font = Font(bold=True)
        for col, letter in [(2, "B"), (3, "C"), (4, "D"), (5, "E")]:
            ws.cell(row=t, column=col).value = (
                f"=SUM({letter}4:{letter}{t-1})")
        ws.cell(row=t, column=6).value = f"=E{t}/B{t}"
        ws.cell(row=t, column=6).number_format = PCT_FMT
        ws.cell(row=t, column=7).value = f"=C{t}/B{t}"
        ws.cell(row=t, column=7).number_format = PCT_FMT
        ws.cell(row=t, column=8).value = f"=AVERAGE(Reviews!G2:G{last})"
        ws.cell(row=t, column=8).number_format = AVG_FMT
        ws.cell(row=t, column=9).value = f"=AVERAGE(Reviews!I2:I{last})"
        ws.cell(row=t, column=9).number_format = AVG_FMT
        for col, w in zip("ABCDEFGHI", [22, 10, 10, 10, 10, 12, 11, 11,
                                        11]):
            ws.column_dimensions[col].width = w
        return ws

    summary_sheet("Sentiment by Category",
                  "Sentiment by product category — live COUNTIFS over Reviews",
                  CATEGORIES, "category", "E", len(CATEGORIES))
    summary_sheet("Sentiment by Channel",
                  "Sentiment by channel — live COUNTIFS over Reviews",
                  CHANNELS, "channel", "F", len(CHANNELS))
    summary_sheet("Monthly Trend",
                  "Monthly sentiment trend — live COUNTIFS over Reviews",
                  MONTHS, "month", "C", len(MONTHS))

    # ── Themes ─────────────────────────────────────────────────────────
    th = wb.create_sheet("Themes")
    th["A1"] = "What customers complain about — counted from the text"
    th["A1"].font = TITLE_FONT
    for c, h in enumerate(["Complaint theme", "Reviews mentioning",
                           "% of all reviews", "% of negative reviews"],
                          start=1):
        th.cell(row=3, column=c, value=h)
    style_header(th, 4, row=3)
    th.freeze_panes = "A4"
    for i, name in enumerate(THEME_NAMES):
        r = 4 + i
        col = theme_cols[i]
        th.cell(row=r, column=1, value=name)
        th.cell(row=r, column=2).value = f"=SUM(Reviews!{col}2:{col}{last})"
        th.cell(row=r, column=3).value = f"=B{r}/Dashboard!$B$5"
        th.cell(row=r, column=3).number_format = PCT_FMT
        th.cell(row=r, column=4).value = (
            f"=SUMIFS(Reviews!{col}2:{col}{last},"
            f"Reviews!J2:J{last},\"Negative\")/Dashboard!$B$8")
        th.cell(row=r, column=4).number_format = PCT_FMT
    r = 4 + len(THEME_NAMES) + 1  # row 13
    th.cell(row=r, column=1,
           value="Reviews mentioning at least one theme").font = Font(
        bold=True)
    th.cell(row=r, column=2).value = f"=SUM(Reviews!S2:S{last})"
    th.cell(row=r, column=3).value = f"=B{r}/Dashboard!$B$5"
    th.cell(row=r, column=3).number_format = PCT_FMT
    th["A15"] = ("A review can mention more than one theme, so the "
                 "column above does not sum to the total reviews — "
                 "the row above counts each review once.")
    th["A15"].alignment = Alignment(wrap_text=True, vertical="top")
    th.merge_cells("A15:D16")
    for col, w in zip("ABCD", [20, 18, 16, 20]):
        th.column_dimensions[col].width = w

    # ── Method ─────────────────────────────────────────────────────────
    m = wb.create_sheet("Method")
    m["A1"] = "How this report is built"
    m["A1"].font = TITLE_FONT
    lines = [
        ("What this is", "A customer-review sentiment report for "
         "BazaarHub.pk, a fictional Pakistani online store. 6 months, "
         "2026-01-01 → 2026-06-30, 181 days, 780 reviews, 5 categories, "
         "15 products, 3 channels."),
        ("Data", f"SAMPLE: {n:,} reviews. Generated by "
         "src/generate_data.py (seed 20261114). Demo data, never claimed "
         "as real client work."),
        ("The method", "Transparent lexicon scoring (src/sentiment.py): "
         "every word in a review is looked up in two plain word lists. "
         "A sentiment word after a negation ('not good', 'never happy') "
         "counts the other way round. Score = positive hits - negative "
         "hits; >= 1 Positive, <= -1 Negative, 0 Neutral. No API, no "
         "machine-learning model — the lists are in the open and a "
         "client can read and edit them."),
        ("Limits", "The lexicon cannot read sarcasm; it misses "
         "sentiment carried only by a phrase that is not in the lists; "
         "a review that praises one thing and complains about another "
         "scores near zero (Neutral) even though it contains both. "
         "Stars and text disagree in about 10% of reviews — that is a "
         "finding, not an error: read those reviews before acting."),
        ("Themes", "Complaint themes are counted from the text with "
         "keyword phrases (src/sentiment.py THEMES). On the Reviews "
         "sheet each theme is a live 0/1 SEARCH formula, so a review "
         "that mentions 'damaged' twice still counts once."),
        ("Live formulas", "Every KPI, category, channel, month and "
         "theme number is a live COUNTIFS / SUMIFS / AVERAGEIFS formula "
         "over the Reviews sheet — paste a real review export in the "
         "same columns, score it with src/sentiment.py, and the report "
         "rebuilds itself."),
        ("MAXIFS / MINIFS", "Best/worst month negative % on the "
         "Dashboard use MAXIFS/MINIFS, written with the _xlfn. prefix "
         "(=_xlfn.MAXIFS(...)) so LibreOffice and Excel calculate "
         "them — the plain form shows #NAME? in LibreOffice."),
        ("Check it", "Every number here is recomputed from the raw CSV "
         "by src/analyze.py and verified by src/checks.py — run it: "
         "python3 src/checks.py"),
        ("Same logic, three ways", "The sentiment mix, category, "
         "channel, monthly, cross-tab, theme and product totals exist "
         "in three forms that must agree: the SQL in "
         "sql/analysis_queries.sql, the Python in src/analyze.py, and "
         "this workbook's formulas. src/checks.py verifies all three "
         "against the raw file, including a LibreOffice recalc."),
    ]
    r = 3
    for title, text in lines:
        m.cell(row=r, column=1, value=title).font = Font(bold=True)
        m.cell(row=r, column=2, value=text)
        m.cell(row=r, column=2).alignment = Alignment(wrap_text=True,
                                                      vertical="top")
        r += 1
    m.column_dimensions["A"].width = 22
    m.column_dimensions["B"].width = 110

    wb.save(OUT)
    print(f"wrote {OUT.name}: sheets {wb.sheetnames}")


if __name__ == "__main__":
    main()
