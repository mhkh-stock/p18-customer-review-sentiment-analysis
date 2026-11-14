#!/usr/bin/env python3
"""P18 — generate the SAMPLE review file for BazaarHub.pk.

Fictional Pakistani online store, 6 months of customer reviews:
Thu 2026-01-01 -> Tue 2026-06-30 (181 days). Seeded, so the file is
reproducible. One file, one row per review:

  data/raw/reviews_SAMPLE.csv — grain: one review
      (review_id, date, month, product, category, channel, stars,
       review_text)

How the demo data is built (and why the report can still find real
things in it): each review is written from an intended sentiment
(positive / neutral / negative) using sentence pools whose words are
in the lexicon in src/sentiment.py, so the lexicon scores the text
the way a reader would. Sentiment differs by product on purpose
(AirBuds Pro is the problem product, Glow Face Serum the best-liked),
by channel (Daraz carries more delivery complaints, WhatsApp /
Instagram more praise) and by month (complaints fall over the half
year as the store fixes delivery). Stars follow the sentiment of
the text — except for a deliberate ~5% of reviews whose stars
contradict their text (a 5-star review with an angry text, a 1-star
review with a happy text). Those are not generator bugs: on a real
file they are the first thing a client should look at, and the
cross-tab in the report counts them.

    python3 src/generate_data.py
"""
import csv
import random
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
RAW = PROJECT / "data" / "raw"
sys.path.insert(0, str(PROJECT / "src"))
from sentiment import score_and_classify  # noqa: E402

SEED = 20261114
START = date(2026, 1, 1)
END = date(2026, 6, 30)
N_REVIEWS = 780

CHANNELS = ["Website", "Daraz", "WhatsApp / Instagram"]
CHANNEL_WEIGHTS = [0.45, 0.35, 0.20]
# negativity shift per channel (added to the negative share)
CHANNEL_NEG_SHIFT = {"Website": 0.0, "Daraz": 0.08,
                     "WhatsApp / Instagram": -0.08}

CATEGORIES = {
    "Electronics": ["AirBuds Pro", "Smart Watch X2",
                    "Power Bank 10000mAh"],
    "Fashion": ["Cotton Lawn Suit", "Men's Kurta", "Classic Sneakers"],
    "Home & Kitchen": ["Non-Stick Cookware Set", "LED Table Lamp",
                       "Storage Organizer Box"],
    "Beauty": ["Glow Face Serum", "Herbal Shampoo",
               "Matte Lipstick Set"],
    "Grocery": ["Basmati Rice 5kg", "Desi Ghee 1kg", "Green Tea Pack"],
}
CATEGORY_WEIGHTS = {"Electronics": 0.24, "Fashion": 0.24,
                    "Home & Kitchen": 0.20, "Beauty": 0.17, "Grocery": 0.15}
# negativity shift per product (added to the negative share)
PRODUCT_NEG_SHIFT = {"AirBuds Pro": 0.22, "Smart Watch X2": 0.06,
                     "Glow Face Serum": -0.10, "Basmati Rice 5kg": -0.05}

# month weights (review volume grows through the half year) and the
# month trend: the negative share falls 2 points a month as the
# store fixes its delivery problems.
MONTH_WEIGHTS = [0.13, 0.14, 0.16, 0.18, 0.19, 0.20]

POSITIVE_SENTENCES = [
    "Excellent product, I loved it.",
    "Great quality and fast delivery.",
    "Amazing, highly recommend it to everyone.",
    "Perfect packing, neat and clean.",
    "Very happy with this purchase, works perfectly.",
    "Good product at an affordable price.",
    "Beautiful and comfortable, exactly as shown.",
    "Best purchase so far, genuine product.",
    "Wonderful experience, polite and helpful seller.",
    "Superb, fresh and nicely packed.",
    "Not bad at all, in fact very good.",
    "Quick delivery and smooth ordering, very satisfied.",
    "Love the soft fabric and stylish look.",
    "I am very pleased, worth every rupee.",
    "The taste is rich and fresh, I enjoyed it.",
    "Strong and durable, works as expected.",
    "Easy to use and very effective.",
    "Thank you, brilliant service and prompt delivery.",
]

NEGATIVE_SENTENCES = [
    "Very disappointed, the product arrived damaged.",
    "Terrible experience, delivery was late.",
    "Poor quality and not worth the money.",
    "The item was broken and the packaging was bad.",
    "Worst purchase, waste of money.",
    "Not good at all, the size was wrong.",
    "Awful product, fake item, not what I ordered.",
    "Delivery took too long and the product was dirty.",
    "Bad quality, overpriced and the colour faded.",
    "Never buying again, rude staff and no reply.",
    "The product is not good and support gave no response.",
    "Expensive for this quality, and it arrived torn.",
    "Defective piece, I want a refund.",
    "Cheap quality, cracked on the first day.",
    "The size did not fit, too small for me.",
    "Stale and smelly, I had to return it.",
    "Slow delivery and unhelpful support.",
    "The colour is dull and the material feels rough.",
    "Bitter taste, not fresh at all.",
    "Leaking bottle and missing parts.",
]

NEUTRAL_SENTENCES = [
    "Product is okay, nothing special about it.",
    "It is average, does what it says on the box.",
    "Received on time and looks like the picture.",
    "Average product, I have used it for a week.",
    "It is okay for daily use, nothing extra.",
    "Delivery was on time and the item matches the photo.",
    "As expected, nothing extra to say.",
    "Decent enough for the price, I will keep it.",
    "The item is as shown, no more and no less.",
    "Used it a few times, it is okay so far.",
    "Same as the picture, delivery took two days.",
    "It is what it is, an ordinary product.",
]

POOLS = {"Positive": POSITIVE_SENTENCES, "Negative": NEGATIVE_SENTENCES,
         "Neutral": NEUTRAL_SENTENCES}


def pick_stars(rng, intent, mismatch):
    """Stars follow the text's sentiment — unless this is one of the
    deliberate mismatches, where the stars contradict the text."""
    if mismatch:
        if intent == "Positive":
            return rng.choice([1, 2])
        if intent == "Negative":
            return rng.choice([4, 5])
        return rng.choice([1, 5])
    if intent == "Positive":
        return 5 if rng.random() < 0.60 else 4
    if intent == "Negative":
        return 1 if rng.random() < 0.55 else 2
    r = rng.random()
    if r < 0.70:
        return 3
    return 4 if r < 0.85 else 2


def main():
    rng = random.Random(SEED)
    months = [(2026, m) for m in range(1, 7)]
    month_days = {}
    for y, m in months:
        first = date(y, m, 1)
        nxt = date(y, m + 1, 1) if m < 6 else date(y, 7, 1)
        month_days[f"{y}-{m:02d}"] = (first, (nxt - first).days)

    rows = []
    for i in range(N_REVIEWS):
        mi = rng.choices(range(6), weights=MONTH_WEIGHTS)[0]
        mkey = f"2026-{mi + 1:02d}"
        first, ndays = month_days[mkey]
        day = first + timedelta(days=rng.randrange(ndays))
        category = rng.choices(list(CATEGORIES),
                               weights=[CATEGORY_WEIGHTS[c]
                                        for c in CATEGORIES])[0]
        product = rng.choice(CATEGORIES[category])
        channel = rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]

        # intended sentiment: base mix, shifted by product, channel
        # and the month trend (complaints fall 2 points a month).
        neg = 0.30 + PRODUCT_NEG_SHIFT.get(product, 0.0) \
            + CHANNEL_NEG_SHIFT[channel] - 0.02 * mi
        neg = max(0.08, min(0.55, neg))
        pos = 0.52 + (0.30 - neg)  # neutral share stays 0.18
        r = rng.random()
        if r < pos:
            intent = "Positive"
        elif r < pos + 0.18:
            intent = "Neutral"
        else:
            intent = "Negative"

        s1, s2 = rng.sample(POOLS[intent], 2)
        text = f"{s1} {s2}"
        # the lexicon is the arbiter: check the text scores as intended
        _, scored = score_and_classify(text)
        if scored != intent:  # pragma: no cover - safety net
            text = f"{rng.choice(POOLS[intent])} " \
                   f"{rng.choice(POOLS[intent])}"
            _, scored = score_and_classify(text)
        mismatch = rng.random() < 0.05
        stars = pick_stars(rng, intent, mismatch)
        rows.append({
            "review_id": f"RB-{i + 1:04d}",
            "date": day.isoformat(), "month": mkey,
            "product": product, "category": category,
            "channel": channel, "stars": stars,
            "review_text": text,
        })

    rows.sort(key=lambda r: (r["date"], r["review_id"]))
    for i, r in enumerate(rows):
        r["review_id"] = f"RB-{i + 1:04d}"
    with open(RAW / "reviews_SAMPLE.csv", "w", newline="",
              encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "review_id", "date", "month", "product", "category",
            "channel", "stars", "review_text"])
        w.writeheader()
        w.writerows(rows)

    n_pos = sum(1 for r in rows
                if score_and_classify(r["review_text"])[1] == "Positive")
    n_neg = sum(1 for r in rows
                if score_and_classify(r["review_text"])[1] == "Negative")
    agree = sum(1 for r in rows
                if (r["stars"] >= 4 and
                    score_and_classify(r["review_text"])[1] == "Positive")
                or (r["stars"] <= 2 and
                    score_and_classify(r["review_text"])[1] == "Negative")
                or (r["stars"] == 3 and
                    score_and_classify(r["review_text"])[1] == "Neutral"))
    print(f"wrote {len(rows)} reviews "
          f"({rows[0]['date']}..{rows[-1]['date']}), "
          f"positive {n_pos}, neutral {len(rows) - n_pos - n_neg}, "
          f"negative {n_neg}, star/sentiment agreement "
          f"{round(100.0 * agree / len(rows), 1)}%")


if __name__ == "__main__":
    main()
