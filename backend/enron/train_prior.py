"""
Trains the Enron-pretrained cold-start prior: TF-IDF + logistic regression
picks the ~15 most predictive terms, then a combined model (those terms +
the existing 7 hand-crafted features) is refit to produce the weight vector
app.py loads as PRIOR_WEIGHTS. This is the "well-tuned general-purpose
baseline" step the proposal calls for, using backend/enron/enron_labeled.json
(folder-heuristic labels — see label_from_folders.py) as training data.

sender_hist is excluded from Enron retraining: it's a per-request feature
computed from live feedback, not something a cross-sectional pretraining
corpus can inform, so its hand-tuned prior weight is carried over unchanged.

Usage:
    venv/bin/python enron/train_prior.py \
        --labeled enron/enron_labeled.json \
        --out ../enron_prior.json \
        [--spotcheck-result path/to/enron_spotcheck_labeled_x.json]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import (
    AUTHORITY_HINTS,
    DEFAULT_PRIOR_WEIGHTS,
    HAND_CRAFTED_FEATURE_ORDER,
    PROMO_KEYWORDS,
    SYSTEM_SENDER_HINTS,
    URGENT_KEYWORDS,
)

N_TERMS = 15


def hand_crafted_features(subject: str, snippet: str, sender: str) -> list[float]:
    """Mirrors app.feature_vector()'s 6 non-bias/non-sender_hist features —
    kept as an inline copy (not imported) so this script's output doesn't
    depend on whatever enron_prior.json/TERM_VOCAB happens to already exist
    on disk from a previous training run."""
    text_lower = f"{subject} {snippet}".lower()
    sender_lower = sender.lower()
    exclaim_count = text_lower.count("!")
    return [
        1.0 if any(k in text_lower for k in URGENT_KEYWORDS) else 0.0,
        1.0 if any(k in text_lower for k in PROMO_KEYWORDS) else 0.0,
        1.0 if any(k in sender_lower for k in AUTHORITY_HINTS) else 0.0,
        1.0 if any(k in sender_lower for k in SYSTEM_SENDER_HINTS) else 0.0,
        1.0 if exclaim_count >= 2 else 0.0,
    ]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled", default=os.path.join(os.path.dirname(__file__), "enron_labeled.json"))
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--out", default=os.path.join(project_root, "enron_prior.json"))
    ap.add_argument("--spotcheck-result", default=None)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    with open(args.labeled, encoding="utf-8") as f:
        rows = json.load(f)["emails"]

    texts = [f'{r["subject"]} {r["snippet"]}' for r in rows]
    y = np.array([1.0 if r["label"] else 0.0 for r in rows])
    idx_train, idx_test = train_test_split(
        np.arange(len(rows)), test_size=0.15, random_state=args.seed, stratify=y
    )

    # Step 1: TF-IDF + LR purely to *discover* which terms are predictive.
    vectorizer = TfidfVectorizer(max_features=3000, stop_words="english", min_df=3)
    X_tfidf_train = vectorizer.fit_transform([texts[i] for i in idx_train])
    X_tfidf_test = vectorizer.transform([texts[i] for i in idx_test])
    tfidf_lr = LogisticRegression(class_weight="balanced", max_iter=1000)
    tfidf_lr.fit(X_tfidf_train, y[idx_train])
    tfidf_heldout_acc = tfidf_lr.score(X_tfidf_test, y[idx_test])

    vocab = vectorizer.get_feature_names_out()
    coefs = tfidf_lr.coef_[0]
    order = np.argsort(coefs)
    top_positive = order[::-1][: (N_TERMS + 1) // 2]
    top_negative = order[: N_TERMS // 2]
    chosen_idx = list(top_positive) + list(top_negative)
    chosen_terms = [vocab[i] for i in chosen_idx]

    # Step 2: rebuild features the same way app.py will compute them at
    # runtime — plain substring presence, not continuous TF-IDF weight — and
    # refit a combined model over hand-crafted + term features together.
    hand_X = np.array([hand_crafted_features(r["subject"], r["snippet"], r["from"]) for r in rows])
    term_X = np.array([[1.0 if term in t.lower() else 0.0 for term in chosen_terms] for t in texts])
    combined_X = np.hstack([hand_X, term_X])

    combined_lr = LogisticRegression(class_weight="balanced", max_iter=2000)
    combined_lr.fit(combined_X[idx_train], y[idx_train])
    heldout_acc = combined_lr.score(combined_X[idx_test], y[idx_test])

    term_feature_names = [f"term_{i}" for i in range(len(chosen_terms))]
    feature_order = list(HAND_CRAFTED_FEATURE_ORDER) + term_feature_names
    prior_weights = {"bias": float(combined_lr.intercept_[0])}
    hand_names = [n for n in HAND_CRAFTED_FEATURE_ORDER if n not in ("bias", "sender_hist")]
    for name, w in zip(hand_names, combined_lr.coef_[0][: len(hand_names)]):
        prior_weights[name] = float(w)
    prior_weights["sender_hist"] = DEFAULT_PRIOR_WEIGHTS["sender_hist"]
    for name, w in zip(term_feature_names, combined_lr.coef_[0][len(hand_names):]):
        prior_weights[name] = float(w)
    term_vocab = dict(zip(term_feature_names, chosen_terms))

    spotcheck_agreement_pct = None
    if args.spotcheck_result:
        with open(args.spotcheck_result, encoding="utf-8") as f:
            spotcheck_agreement_pct = json.load(f)["agreement_pct"]

    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "train_size": len(idx_train),
        "heldout_size": len(idx_test),
        "class_balance": {"keep": int(y.sum()), "skip": int(len(y) - y.sum())},
        "heldout_accuracy": round(heldout_acc, 4),
        "tfidf_only_heldout_accuracy": round(tfidf_heldout_acc, 4),
        "spotcheck_agreement_pct": spotcheck_agreement_pct,
    }

    payload = {
        "feature_order": feature_order,
        "prior_weights": prior_weights,
        "term_vocab": term_vocab,
        "metadata": metadata,
    }
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Trained on {len(idx_train)} emails, held out {len(idx_test)}.")
    print(f"TF-IDF-only heldout accuracy (discovery step): {tfidf_heldout_acc:.3f}")
    print(f"Combined ({len(feature_order)}-feature) heldout accuracy: {heldout_acc:.3f}")
    print(f"Chosen terms: {chosen_terms}")
    if spotcheck_agreement_pct is not None:
        print(f"Spot-check agreement: {spotcheck_agreement_pct}%")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
