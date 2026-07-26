"""
Calls the real Claude API (Haiku 4.5) to test the "LLM + natural-language
preference profile" approach against the existing hand-crafted logistic
regression model (PRIOR_WEIGHTS + train_weights() in backend/app.py), on the
same train/test split of one teammate's real labeled Gmail export.

This replaces an earlier ad-hoc version of this experiment where a
conversational assistant read the training labels and predicted the test
labels directly in-context (zero cost, zero latency, since no API was
actually called). This script makes a real API call so the latency/cost
numbers are real deployment numbers, not stand-ins.

Two-stage approach (same methodology as the ad-hoc version):
  1. One API call summarizes the training examples into a natural-language
     user preference profile.
  2. One batched API call classifies all test emails against that profile
     in a single request, using a forced tool call for reliable structured
     output (mirrors how a production /classify-style batch call would work
     — one call for the whole target batch, not one call per email).

Prints latency and token cost for both calls (Haiku 4.5 pricing: $1/$5 per
1M input/output tokens), alongside accuracy/precision/recall for both the
LLM and the hand-crafted baseline, scored on the identical split.

Note: this uses a fresh deterministic 70/30 split (seed=42) of the given
export, not necessarily byte-identical to any earlier ad-hoc split of the
same file — same methodology and ratio, not guaranteed the same rows.

Usage:
    venv/bin/python llm_eval/claude_classify.py --labeled ~/Downloads/labeled_Zhidian_200.json
"""
import argparse
import json
import os
import random
import sys
import time

import anthropic
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import (
    Email,
    LabeledEmail,
    PRIOR_WEIGHTS,
    build_sender_stats,
    dot,
    feature_vector,
    sigmoid,
    train_weights,
)

load_dotenv()

MODEL = "claude-haiku-4-5"
# Haiku 4.5 pricing, per 1M tokens.
INPUT_PRICE_PER_M = 1.00
OUTPUT_PRICE_PER_M = 5.00

SEED = 42
TEST_FRACTION = 0.3


def load_rows(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw = data["emails"]
    # Same convention as backend/enron/evaluate_prior.py: privacy_skip rows
    # are excluded from scoring entirely, same as email_priority_test.html.
    return [r for r in raw if r["label"] is True or r["label"] is False]


def split_rows(rows):
    shuffled = list(rows)
    random.Random(SEED).shuffle(shuffled)
    n_test = round(len(shuffled) * TEST_FRACTION)
    return shuffled[n_test:], shuffled[:n_test]  # train, test


def to_email(r, keep_field=False):
    kwargs = dict(
        id=r.get("id"), **{"from": r["from"]}, subject=r["subject"], snippet=r["snippet"],
        to_count=r.get("to_count", 1), cc_count=r.get("cc_count", 0),
        in_to=r.get("in_to", True), has_attachment=r.get("has_attachment", False),
        is_bulk_header=r.get("is_bulk_header", False), is_reply_thread=r.get("is_reply_thread", False),
        sent_hour=r.get("sent_hour"), reciprocal=r.get("reciprocal", False),
    )
    if keep_field:
        return LabeledEmail(keep=r["label"], **kwargs)
    return Email(**kwargs)


def score(preds, truth):
    tp = fp = tn = fn = 0
    for pred, true in zip(preds, truth):
        if pred and true:
            tp += 1
        elif pred and not true:
            fp += 1
        elif not pred and not true:
            tn += 1
        else:
            fn += 1
    n = len(truth)
    accuracy = (tp + tn) / n if n else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    return {"n": n, "accuracy": accuracy, "precision": precision, "recall": recall, "tp": tp, "fp": fp, "tn": tn, "fn": fn}


def run_baseline(train_rows, test_rows):
    train_examples = [to_email(r, keep_field=True) for r in train_rows]
    sender_stats = build_sender_stats(train_examples)
    weights = train_weights(train_examples, sender_stats)
    preds = []
    for r in test_rows:
        target = to_email(r)
        x = feature_vector(target, sender_stats)
        preds.append(sigmoid(dot(weights, x)) > 0.5)
    truth = [r["label"] for r in test_rows]
    return score(preds, truth)


def build_profile(client, train_rows):
    lines = []
    for r in train_rows:
        label = "KEEP" if r["label"] else "SKIP"
        lines.append(f'[{label}] From: {r["from"]} | Subject: {r["subject"]} | Snippet: {r["snippet"][:200]}')
    listing = "\n".join(lines)

    prompt = (
        "以下是一位用户对自己收件箱里若干邮件标注的 Keep(留)/Skip(跳过) 结果，"
        "总结出一段简洁的自然语言“用户偏好画像”，描述这个人倾向于保留什么类型的邮件、跳过什么类型的邮件。"
        "指出具体的发件人模式、主题关键词、邮件类型等规律，包括你观察到的任何前后不一致的边界案例。"
        "不要逐条复述邮件，只给出总结。\n\n" + listing
    )

    start = time.monotonic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.monotonic() - start
    if response.stop_reason == "max_tokens":
        print("WARNING: profile generation hit max_tokens and was truncated")
    profile_text = next(b.text for b in response.content if b.type == "text")
    return profile_text, elapsed, response.usage


CLASSIFY_TOOL = {
    "name": "classify_emails",
    "description": "Return a keep/skip decision for every email in the batch, in the same order given.",
    "input_schema": {
        "type": "object",
        "properties": {
            "decisions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "keep": {"type": "boolean"},
                    },
                    "required": ["id", "keep"],
                },
            },
        },
        "required": ["decisions"],
    },
}


def classify_batch(client, profile_text, test_rows):
    lines = [
        f'id={r["id"]} | From: {r["from"]} | Subject: {r["subject"]} | Snippet: {r["snippet"][:200]}'
        for r in test_rows
    ]
    listing = "\n".join(lines)

    prompt = (
        f"这是根据这位用户的历史标注总结出的偏好画像：\n{profile_text}\n\n"
        "现在请你根据这段画像，判断下面这批邮件里哪些该 Keep（留），哪些该 Skip（跳过）。"
        "只根据画像和邮件内容判断，不要假设你见过这些具体邮件的真实标签。"
        "对每一封邮件都给出判断，调用 classify_emails 工具，保持顺序和输入一致。\n\n" + listing
    )

    start = time.monotonic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_emails"},
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.monotonic() - start

    tool_use = next(b for b in response.content if b.type == "tool_use")
    decisions = {d["id"]: d["keep"] for d in tool_use.input["decisions"]}
    return decisions, elapsed, response.usage


def cost(usage_list):
    input_tokens = sum(u.input_tokens for u in usage_list)
    output_tokens = sum(u.output_tokens for u in usage_list)
    total = (input_tokens / 1_000_000 * INPUT_PRICE_PER_M) + (output_tokens / 1_000_000 * OUTPUT_PRICE_PER_M)
    return total, input_tokens, output_tokens


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled", default=os.path.expanduser("~/Downloads/labeled_Zhidian_200.json"))
    args = ap.parse_args()

    rows = load_rows(args.labeled)
    train_rows, test_rows = split_rows(rows)
    print(f"n={len(rows)}  train={len(train_rows)}  test={len(test_rows)}  (seed={SEED}, test_fraction={TEST_FRACTION})")

    print("\n=== Hand-crafted feature model (existing PRIOR_WEIGHTS + train_weights) ===")
    baseline = run_baseline(train_rows, test_rows)
    print(baseline)

    print(f"\n=== Claude API ({MODEL}): profile + batch classify ===")
    client = anthropic.Anthropic()

    profile_text, profile_time, profile_usage = build_profile(client, train_rows)
    print(f"\n--- Preference profile (generated in {profile_time:.2f}s) ---\n{profile_text}\n")

    decisions, classify_time, classify_usage = classify_batch(client, profile_text, test_rows)
    preds_raw = [decisions.get(r["id"]) for r in test_rows]
    missing = [r["id"] for r, p in zip(test_rows, preds_raw) if p is None]
    if missing:
        print(f"WARNING: model didn't return a decision for {len(missing)} emails: {missing}")
    truth = [r["label"] for r in test_rows]
    # Treat any missing decision as a Skip prediction (worst case), so a
    # partial response doesn't just get silently excluded from scoring.
    preds = [p if p is not None else False for p in preds_raw]
    llm_score = score(preds, truth)
    print(llm_score)

    total_cost, in_tok, out_tok = cost([profile_usage, classify_usage])
    total_time = profile_time + classify_time
    print(f"\n=== Cost & latency (real API calls, {MODEL}) ===")
    print(f"input_tokens={in_tok}  output_tokens={out_tok}  cost=${total_cost:.5f}")
    print(f"latency: profile={profile_time:.2f}s  classify={classify_time:.2f}s  total={total_time:.2f}s")
    print(f"(2 API calls total for this whole {len(test_rows)}-email test batch — not per-email)")

    print("\n=== Summary ===")
    print(f"{'Method':<45}{'Accuracy':>10}{'Precision':>11}{'Recall':>9}")
    print(f"{'Hand-crafted (PRIOR_WEIGHTS+train_weights)':<45}{baseline['accuracy']:>10.3f}{baseline['precision']:>11.3f}{baseline['recall']:>9.3f}")
    print(f"{'Claude Haiku 4.5 (profile+batch classify)':<45}{llm_score['accuracy']:>10.3f}{llm_score['precision']:>11.3f}{llm_score['recall']:>9.3f}")


if __name__ == "__main__":
    main()
