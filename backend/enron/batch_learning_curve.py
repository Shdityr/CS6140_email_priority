"""
Replays the exact same batch/round methodology as email_priority_test.html's
runExperiment() — split into batches, accumulate labeled examples round by
round, refit from the prior each round (train_weights() in app.py), compare
against a frozen cold-start baseline (examples=[]) — but against 500 Enron
rows instead of real collected Gmail data, and calling app.py's real
functions directly instead of going through HTTP. This is a quick empirical
answer to "does batch-accumulate-and-refit actually help, round over round,
on data we already have" while the team collects real inbox data.

Usage:
    venv/bin/python enron/batch_learning_curve.py \
        --labeled enron/enron_labeled.json --n 500 --batch-size 50 --trials 8
"""
import argparse
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import Email, LabeledEmail, build_sender_stats, dot, feature_vector, sigmoid, train_weights


def to_email(row, cls):
    kwargs = dict(
        id=None, **{"from": row["from"]}, subject=row["subject"], snippet=row["snippet"],
        to_count=row.get("to_count", 1), cc_count=row.get("cc_count", 0),
        in_to=row.get("in_to", True),
        has_attachment=row.get("has_attachment", False),
        is_bulk_header=row.get("is_bulk_header", False),
        is_reply_thread=row.get("is_reply_thread", False),
        sent_hour=row.get("sent_hour"),
        reciprocal=row.get("reciprocal", False),
    )
    if cls is LabeledEmail:
        kwargs["keep"] = row["label"]
    return cls(**kwargs)


def usable_rows(rows):
    # Real extractor exports can contain label == "privacy_skip" entries —
    # exclude those from scoring, same as email_priority_test.html does.
    return [r for r in rows if r["label"] is True or r["label"] is False]


def score(examples, targets_with_labels):
    sender_stats = build_sender_stats(examples)
    weights = train_weights(examples, sender_stats)
    correct = 0
    for target, true_label in targets_with_labels:
        x = feature_vector(target, sender_stats)
        pred = sigmoid(dot(weights, x)) > 0.5
        if pred == true_label:
            correct += 1
    return correct / len(targets_with_labels) if targets_with_labels else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled", default=os.path.join(os.path.dirname(__file__), "enron_labeled.json"))
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--batch-size", type=int, default=50)
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    with open(args.labeled, encoding="utf-8") as f:
        rows = usable_rows(json.load(f)["emails"])

    random.seed(args.seed)
    keep_rows = [r for r in rows if r["label"]]
    skip_rows = [r for r in rows if not r["label"]]
    half = min(args.n // 2, len(keep_rows), len(skip_rows))
    if half * 2 < args.n:
        print(f"Note: only {len(keep_rows)} keep / {len(skip_rows)} skip usable rows available; "
              f"using a balanced {half*2} instead of the requested {args.n}.")
    sample = random.sample(keep_rows, half) + random.sample(skip_rows, half)

    num_rounds = len(sample) // args.batch_size - 1
    personalized_by_round = [[] for _ in range(num_rounds)]
    baseline_by_round = [[] for _ in range(num_rounds)]

    for _trial in range(args.trials):
        shuffled = sample[:]
        random.shuffle(shuffled)
        batches = [shuffled[i * args.batch_size:(i + 1) * args.batch_size] for i in range(num_rounds + 1)]

        examples = [to_email(r, LabeledEmail) for r in batches[0]]
        for r in range(1, num_rounds + 1):
            target_rows = batches[r]
            targets = [(to_email(row, Email), row["label"]) for row in target_rows]

            personalized_by_round[r - 1].append(score(examples, targets))
            baseline_by_round[r - 1].append(score([], targets))

            examples = examples + [to_email(row, LabeledEmail) for row in target_rows]

    print(f"n={len(sample)} batch_size={args.batch_size} trials={args.trials} rounds={num_rounds}")
    print(f"{'round':<8}{'personalized':>14}{'baseline':>12}{'lift':>10}")
    for r in range(num_rounds):
        p = sum(personalized_by_round[r]) / len(personalized_by_round[r])
        b = sum(baseline_by_round[r]) / len(baseline_by_round[r])
        print(f"{r + 1:<8}{p * 100:>13.1f}%{b * 100:>11.1f}%{(p - b) * 100:>9.1f}pp")


if __name__ == "__main__":
    main()
