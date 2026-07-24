"""
Scores the live hand-tuned PRIOR_WEIGHTS (backend/app.py, 18 features) against
the Enron heuristic-labeled set as a pure TEST set — no training, no gradient
descent, just the cold-start prior's raw predictions vs. the folder-heuristic
labels. This is deliberately NOT re-introducing Enron as a training source
(see METHOD_DISCUSSION.md for why that was dropped) — it's a sanity check on
whether the hand-designed features have any real signal at all, using data we
already have, before the team collects real Gmail data.

Caveat baked into the read of these results (see printed note): the Enron
"keep" class is the employee's own SENT mail (they are the sender, not the
recipient), while several new features (has_attachment, is_bulk_header,
is_reply_thread, many_recipients, business_hours) are structurally about
receiving mail. So this test set is not a clean like-for-like comparison for
those features the way real inbox data would be — the "skip" class (received
deleted/bulk mail) is the fairer test bed for them.

Usage:
    venv/bin/python enron/evaluate_prior.py --labeled enron/enron_labeled.json
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import Email, FEATURE_ORDER, PRIOR_WEIGHTS, dot, feature_vector, sigmoid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled", default=os.path.join(os.path.dirname(__file__), "enron_labeled.json"))
    args = ap.parse_args()

    with open(args.labeled, encoding="utf-8") as f:
        rows = json.load(f)["emails"]

    correct = 0
    tp = fp = tn = fn = 0
    feature_sums = {"keep": dict.fromkeys(FEATURE_ORDER, 0.0), "skip": dict.fromkeys(FEATURE_ORDER, 0.0)}
    class_counts = {"keep": 0, "skip": 0}

    for r in rows:
        email_obj = Email(
            id=None, **{"from": r["from"]}, subject=r["subject"], snippet=r["snippet"],
            to_count=r.get("to_count", 1), cc_count=r.get("cc_count", 0),
            has_attachment=r.get("has_attachment", False),
            is_bulk_header=r.get("is_bulk_header", False),
            is_reply_thread=r.get("is_reply_thread", False),
            sent_hour=r.get("sent_hour"),
        )
        x = feature_vector(email_obj, {})  # {} sender_stats = true cold start, sender_hist=0
        score = sigmoid(dot(PRIOR_WEIGHTS, x))
        pred = score > 0.5
        true = r["label"]

        bucket = "keep" if true else "skip"
        class_counts[bucket] += 1
        for k in FEATURE_ORDER:
            feature_sums[bucket][k] += x[k]

        if pred == true:
            correct += 1
        if pred and true:
            tp += 1
        elif pred and not true:
            fp += 1
        elif not pred and not true:
            tn += 1
        else:
            fn += 1

    n = len(rows)
    accuracy = correct / n
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    print(f"n={n}  accuracy={accuracy:.3f}")
    print(f"keep(sent)-class precision={precision:.3f} recall={recall:.3f}")
    print(f"confusion: tp={tp} fp={fp} tn={tn} fn={fn}")
    print()
    print("Per-feature mean activation, keep(sent) vs skip(deleted/bulk) class:")
    print(f"{'feature':<22}{'keep':>8}{'skip':>8}")
    for k in FEATURE_ORDER:
        if k == "bias":
            continue
        keep_mean = feature_sums["keep"][k] / class_counts["keep"] if class_counts["keep"] else 0.0
        skip_mean = feature_sums["skip"][k] / class_counts["skip"] if class_counts["skip"] else 0.0
        print(f"{k:<22}{keep_mean:>8.3f}{skip_mean:>8.3f}")

    print()
    print("Caveat: 'keep' class = employee's own SENT mail (they're the sender, not")
    print("recipient) — has_attachment/is_bulk_header/is_reply_thread/many_recipients/")
    print("business_hours are structurally about RECEIVING mail, so 'skip' (received")
    print("deleted/bulk mail) is the fairer test bed for those specific features.")


if __name__ == "__main__":
    main()
