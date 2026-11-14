#!/usr/bin/env python3
"""P18 — the sentiment method, shared by generate/analyse/workbook/checks.

Transparent lexicon scoring (no API, no ML model claim): every word in
a review is looked up in two plain word lists. A sentiment word that
follows a negation within two words ("not good", "never happy") counts
the other way round. Score = positive hits - negative hits after the
negation flip. Score >= 1 -> Positive, <= -1 -> Negative, 0 -> Neutral.

The lists live here in the open so a client can read, argue with and
edit them — that is the point of the method. Its limits are stated in
the README and in the workbook's Method sheet: it cannot read sarcasm,
it misses sentiment carried only by a phrase that is not in the lists,
and a review that praises one thing and complains about another scores
near zero (Neutral) even though it contains both.
"""
import re

POSITIVE = {
    "excellent", "great", "amazing", "awesome", "wonderful", "fantastic",
    "superb", "brilliant", "perfect", "best", "good", "nice", "lovely",
    "beautiful", "love", "loved", "happy", "satisfied", "pleased",
    "impressed", "impressive", "recommend", "recommended", "fast", "quick",
    "prompt", "timely", "easy", "smooth", "helpful", "friendly", "polite",
    "fresh", "durable", "reliable", "genuine", "original", "affordable",
    "comfortable", "soft", "stylish", "neat", "clean",
    "worth", "super", "fine", "enjoyed", "glad", "thank",
    "thanks", "outstanding", "delightful", "pleasant",
    "solid", "strong", "bright", "rich", "tasty",
    "fragrant", "effective", "works", "working", "perfectly",
}

NEGATIVE = {
    "bad", "terrible", "awful", "horrible", "worst", "poor", "disappointed",
    "disappointing", "disappointment", "waste", "useless", "fake",
    "broken", "damaged", "defective", "defect", "faulty", "wrong",
    "missing", "late", "delayed", "slow", "rude", "unhelpful", "dirty",
    "torn", "scratched", "expired", "stale", "smelly", "small", "tight",
    "loose", "faded", "cheap", "expensive", "overpriced", "hard",
    "rough", "weak", "dull", "bland", "bitter", "sour", "leaking",
    "cracked", "bent", "stained", "unhappy", "angry", "frustrated",
    "annoyed", "regret", "refund", "return", "returned", "complaint",
    "problem", "issue", "issues", "never", "avoid", "worse", "horrible",
    "pathetic", "useless", "junk", "trash", "ripoff", "scam", "cheated",
}

# Words that flip the next sentiment word ("not good", "never happy",
# "not bad" -> the "bad" counts as positive). "never" is also a
# negative word on its own; as a negator it wins when it precedes a
# sentiment word within two tokens.
NEGATIONS = {
    "not", "no", "never", "didnt", "didn't", "dont", "don't", "doesnt",
    "doesn't", "wasnt", "wasn't", "isnt", "isn't", "cant", "can't",
    "couldnt", "couldn't", "wont", "won't", "hardly", "barely",
}

WORD_RE = re.compile(r"[a-z']+")


def score_text(text):
    """Return (score, positive_hits, negative_hits) for one review."""
    tokens = WORD_RE.findall(text.lower())
    pos = neg = 0
    for i, tok in enumerate(tokens):
        if tok in POSITIVE or tok in NEGATIVE:
            flipped = any(t in NEGATIONS
                          for t in tokens[max(0, i - 2):i])
            if tok in POSITIVE:
                if flipped:
                    neg += 1
                else:
                    pos += 1
            else:
                if flipped:
                    pos += 1
                else:
                    neg += 1
    return pos - neg, pos, neg


def classify(score):
    """Score -> Positive / Neutral / Negative."""
    if score >= 1:
        return "Positive"
    if score <= -1:
        return "Negative"
    return "Neutral"


def score_and_classify(text):
    """Return (score, sentiment) for one review."""
    score, _, _ = score_text(text)
    return score, classify(score)


# Complaint themes: a review counts once per theme if any of its
# phrases appears in the text (case-insensitive substring). Counted,
# never invented — the counts in the report are these matches.
THEMES = {
    "Late delivery": ["late delivery", "delivery was late",
                      "arrived late", "took too long", "delayed delivery",
                      "very late", "days late"],
    "Damaged product": ["damaged", "broken", "cracked", "torn", "scratched",
                        "bent", "leaking", "defective", "faulty"],
    "Size / fit": ["too small", "too big", "wrong size", "size issue",
                   "did not fit", "does not fit", "too tight",
                   "too loose"],
    "Price": ["overpriced", "too expensive", "not worth", "waste of money",
              "price is high", "too costly", "expensive for"],
    "Poor quality": ["poor quality", "bad quality", "low quality",
                     "cheap quality", "quality is bad", "quality is poor"],
    "Packaging": ["bad packaging", "poor packaging", "packaging was bad",
                  "no packaging", "packaging torn", "packing was bad"],
    "Customer service": ["customer service", "no reply", "no response",
                         "rude staff", "nobody answered", "support did not",
                         "support was rude"],
    "Wrong item": ["wrong item", "wrong product", "wrong colour",
                   "wrong color", "different item", "not what i ordered"],
}


def themes_in(text):
    """Return the list of theme names found in one review's text."""
    low = text.lower()
    return [name for name, phrases in THEMES.items()
            if any(p in low for p in phrases)]
