"""
Generates the two figures used in the report's Data Analysis / Results
sections directly from real data — no browser or running server needed.

1. figures/feature_activation.png — mean activation of each of the 17
   non-bias features, keep(sent) vs skip(deleted/bulk), on the Enron
   cold-start sanity check (Section 5.2), reusing evaluate_prior.py's logic.
2. figures/personalization_curve.png — the personalization-vs-baseline
   learning curve (Section 5.1) for Zhidian's and Vignesh's real datasets,
   mean +/- std across 5 random seeds, reusing gmail_eval/batch_learning_curve.py's logic.

Usage:
    venv/bin/python gmail_eval/make_figures.py
"""
import json
import os
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import (
    Email, FEATURE_ORDER, LabeledEmail, PRIOR_WEIGHTS, build_sender_stats,
    dot, feature_vector, sigmoid, train_weights,
)

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))
FIG_DIR = os.path.join(PROJECT_ROOT, "figures")
os.makedirs(FIG_DIR, exist_ok=True)


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


def figure_feature_activation():
    with open(os.path.join(HERE, "..", "enron", "enron_labeled.json"), encoding="utf-8") as f:
        rows = usable_rows(json.load(f)["emails"])

    sums = {"keep": dict.fromkeys(FEATURE_ORDER, 0.0), "skip": dict.fromkeys(FEATURE_ORDER, 0.0)}
    counts = {"keep": 0, "skip": 0}
    for r in rows:
        email_obj = to_email(r, Email)
        x = feature_vector(email_obj, {})
        bucket = "keep" if r["label"] else "skip"
        counts[bucket] += 1
        for k in FEATURE_ORDER:
            sums[bucket][k] += x[k]

    feats = [f for f in FEATURE_ORDER if f != "bias"]
    keep_means = [sums["keep"][f] / counts["keep"] for f in feats]
    skip_means = [sums["skip"][f] / counts["skip"] for f in feats]

    y = np.arange(len(feats))
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh(y - 0.2, keep_means, height=0.4, label="keep (sent)", color="#0E7C6F")
    ax.barh(y + 0.2, skip_means, height=0.4, label="skip (deleted/bulk)", color="#C85A3A")
    ax.set_yticks(y)
    ax.set_yticklabels(feats, fontsize=9)
    ax.set_xlabel("Mean feature activation")
    ax.set_title("Enron cold-start sanity check: feature activation by class\n(n=30,000, PRIOR_WEIGHTS, no training)")
    ax.legend()
    ax.invert_yaxis()
    fig.tight_layout()
    out = os.path.join(FIG_DIR, "feature_activation.png")
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"wrote {out}")


def learning_curve(labeled_path, batch_size=10, trials=8, seeds=(0, 1, 2, 3, 4)):
    with open(os.path.expanduser(labeled_path), encoding="utf-8") as f:
        data = json.load(f)
        rows = usable_rows(data["emails"])

    num_rounds = len(rows) // batch_size - 1
    all_seed_personalized = []
    all_seed_baseline = []

    for seed in seeds:
        random.seed(seed)
        # Round 0 is the genuine zero-feedback point: the untrained prior
        # scored on batch 0 itself, before it has been used for anything.
        # personalized and baseline are identical here by construction
        # (train_weights([]) just returns the untrained prior) -- this makes
        # that shared starting point explicit in the figure instead of
        # leaving it implicit.
        personalized_by_round = [[] for _ in range(num_rounds + 1)]
        baseline_by_round = [[] for _ in range(num_rounds + 1)]
        for _trial in range(trials):
            shuffled = rows[:]
            random.shuffle(shuffled)
            batches = [shuffled[i * batch_size:(i + 1) * batch_size] for i in range(num_rounds + 1)]

            batch0_targets = [(to_email(row, Email), row["label"]) for row in batches[0]]
            zero_shot = score([], batch0_targets)
            personalized_by_round[0].append(zero_shot)
            baseline_by_round[0].append(zero_shot)

            examples = [to_email(r, LabeledEmail) for r in batches[0]]
            for r in range(1, num_rounds + 1):
                target_rows = batches[r]
                targets = [(to_email(row, Email), row["label"]) for row in target_rows]
                personalized_by_round[r].append(score(examples, targets))
                baseline_by_round[r].append(score([], targets))
                examples = examples + [to_email(row, LabeledEmail) for row in target_rows]
        all_seed_personalized.append([sum(rr) / len(rr) for rr in personalized_by_round])
        all_seed_baseline.append([sum(rr) / len(rr) for rr in baseline_by_round])

    p = np.array(all_seed_personalized) * 100  # seeds x rounds
    b = np.array(all_seed_baseline) * 100
    return {
        "tester": data.get("tester"),
        "rounds": list(range(0, num_rounds + 1)),
        "personalized_mean": p.mean(axis=0), "personalized_std": p.std(axis=0),
        "baseline_mean": b.mean(axis=0), "baseline_std": b.std(axis=0),
    }


def _plot_panel(ax, d):
    rounds = d["rounds"]
    ax.plot(rounds, d["personalized_mean"], color="#2F6FED", marker="o", label="Personalized")
    ax.plot(rounds, d["baseline_mean"], color="#9B8F5C", marker="o", label="Cold-start baseline")
    ax.set_title(f"{d['tester']} ({len(rounds) - 1} feedback rounds)")
    ax.set_xlabel("Round (0 = untrained prior, shared starting point)")
    ax.set_ylabel("Accuracy (%)")
    # Zoom the y-axis to the data's actual range (with padding) rather than a
    # fixed 0-100, so the round-over-round trend is visible instead of being
    # visually flattened by a full-scale axis.
    lo = min(d["personalized_mean"].min(), d["baseline_mean"].min())
    hi = max(d["personalized_mean"].max(), d["baseline_mean"].max())
    pad = max(3.0, (hi - lo) * 0.12)
    ax.set_ylim(max(0, lo - pad), min(100, hi + pad))
    ax.legend(fontsize=8)


def figure_personalization_curve():
    zhidian = learning_curve(os.path.expanduser("~/Downloads/labeled_Zhidian_200.json"))
    vignesh = learning_curve(os.path.expanduser("~/Downloads/labeled_Vignesh_60.json"))
    sathvik = learning_curve(os.path.expanduser("~/Downloads/labeled_Sathvik_100.json"))

    # Figure A: the two datasets where personalization helped (Zhidian, Sathvik).
    fig_good, axes_good = plt.subplots(1, 2, figsize=(10, 4.5))
    for ax, d in zip(axes_good, [zhidian, sathvik]):
        _plot_panel(ax, d)
    fig_good.suptitle("Where personalization helped (mean across 5 random seeds)")
    fig_good.tight_layout()
    out_good = os.path.join(FIG_DIR, "personalization_curve_good.png")
    fig_good.savefig(out_good, dpi=150)
    plt.close(fig_good)
    print(f"wrote {out_good}")

    # Figure B: Vignesh alone (personalization hurt here).
    fig_bad, ax_bad = plt.subplots(1, 1, figsize=(5.5, 4.5))
    _plot_panel(ax_bad, vignesh)
    fig_bad.suptitle("Where personalization hurt (mean across 5 random seeds)")
    fig_bad.tight_layout()
    out_bad = os.path.join(FIG_DIR, "personalization_curve_vignesh.png")
    fig_bad.savefig(out_bad, dpi=150)
    plt.close(fig_bad)
    print(f"wrote {out_bad}")

    # Print the exact aggregated numbers so the report text can cite them precisely.
    for d in (zhidian, vignesh, sathvik):
        # Exclude round 0 (the shared, untrained starting point, where lift is
        # 0 by construction) so it doesn't dilute the average over actual
        # feedback rounds.
        lift = (d["personalized_mean"][1:] - d["baseline_mean"][1:]).mean()
        print(f"{d['tester']}: final personalized={d['personalized_mean'][-1]:.1f}% "
              f"final baseline={d['baseline_mean'][-1]:.1f}% mean_lift={lift:.1f}pp")


if __name__ == "__main__":
    figure_feature_activation()
    figure_personalization_curve()
