"""
Turns the raw Enron maildir corpus into a heuristically keep/skip-labeled
dataset, using the folder each message was filed into as a proxy for
priority — Enron itself has no priority labels, so this is the foundation
the whole Enron-pretrained prior is built on (see METHOD_DISCUSSION.md).

Heuristic (folder name = immediate child directory of the employee's mailbox):
  - skip:     deleted_items, trash, junk, spam, all_documents, discussion_threads
  - keep:     sent, sent_items, sent_mail, _sent_mail
  - excluded: inbox (unsorted/mixed — too ambiguous either way), calendar,
              contacts, notes_inbox, tasks, and (by default) custom-named
              folders — see --custom-folders below.

--custom-folders {keep, exclude} (default: exclude). Originally custom-named
folders (anything the employee named themselves) were treated as "keep" —
filed away on purpose. Empirically this hurt generalization: the top
predictive terms it produced were dominated by per-employee idiosyncratic
vocabulary (a specific coworker's or project's name) rather than reusable
priority signal, and held-out TF-IDF accuracy was ~10 points lower than the
sent-vs-deleted/bulk-only heuristic (0.578 vs 0.680 on the real Enron
corpus — see METHOD_DISCUSSION.md). "exclude" is now the default; "keep" is
left available for comparison.

Usage:
    venv/bin/python enron/label_from_folders.py \
        --maildir enron/raw/maildir \
        --out enron/enron_labeled.json
"""
import argparse
import email
import json
import os
import random
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from email_parsing import decode_mime_words, extract_snippet
from email_parsing import has_attachment as msg_has_attachment
from app import _addresses, _is_bulk_header, _sent_hour

SKIP_FOLDERS = {"deleted_items", "trash", "junk", "spam", "all_documents", "discussion_threads"}
KEEP_FOLDERS = {"sent", "sent_items", "sent_mail", "_sent_mail"}
EXCLUDED_FOLDERS = {"inbox", "calendar", "contacts", "notes_inbox", "tasks"}

# Stop collecting a class once it hits this many examples — bounds runtime
# regardless of corpus size; plenty for TF-IDF + logistic regression.
TARGET_PER_CLASS = 15000
# Cap the majority class relative to the minority one before writing out,
# per the proposal's class-imbalance-handling plan (resampling).
MAX_IMBALANCE_RATIO = 3


def classify_folder(folder_name: str, custom_folders: str = "exclude"):
    name = folder_name.lower()
    if name in SKIP_FOLDERS:
        return False
    if name in KEEP_FOLDERS:
        return True
    if name in EXCLUDED_FOLDERS:
        return None
    # custom-named folder — employee filed it away on purpose. Configurable:
    # "keep" (default) treats that as a positive signal; "exclude" drops it,
    # for comparing against a purely sent-vs-deleted/bulk heuristic (custom
    # folder names are often per-employee vocabulary — people/project names —
    # which may not generalize as a priority signal across employees).
    return True if custom_folders == "keep" else None


def iter_messages(maildir_root: str):
    for user in sorted(os.listdir(maildir_root)):
        user_path = os.path.join(maildir_root, user)
        if not os.path.isdir(user_path):
            continue
        for folder_name in sorted(os.listdir(user_path)):
            folder_path = os.path.join(user_path, folder_name)
            if not os.path.isdir(folder_path):
                continue
            for root, _dirs, files in os.walk(folder_path):
                for fname in files:
                    yield user, folder_name, os.path.join(root, fname)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maildir", default=os.path.join(os.path.dirname(__file__), "raw", "maildir"))
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "enron_labeled.json"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--custom-folders", choices=["keep", "exclude"], default="exclude")
    args = ap.parse_args()

    if not os.path.isdir(args.maildir):
        print(f"Maildir not found at {args.maildir} — download+extract the Enron tarball first.", file=sys.stderr)
        sys.exit(1)

    random.seed(args.seed)
    folder_counts = Counter()
    bucket_counts = Counter()
    rows = []
    class_counts = {True: 0, False: 0}

    for user, folder_name, path in iter_messages(args.maildir):
        folder_counts[folder_name.lower()] += 1
        label = classify_folder(folder_name, args.custom_folders)
        if label is None:
            bucket_counts["excluded"] += 1
            continue
        if class_counts[label] >= TARGET_PER_CLASS:
            bucket_counts["skipped_over_cap"] += 1
            if all(class_counts[c] >= TARGET_PER_CLASS for c in (True, False)):
                break
            continue
        try:
            with open(path, "rb") as f:
                msg = email.message_from_bytes(f.read())
        except Exception:
            continue
        subject = decode_mime_words(msg.get("Subject", ""))
        sender = decode_mime_words(msg.get("From", ""))
        snippet = extract_snippet(msg)
        if not subject and not snippet:
            continue
        # Structural fields for evaluating the live 18-feature prior against
        # Enron as a test set (not training — see evaluate_prior.py). Note:
        # in_to/reciprocal are deliberately NOT computed here — they require
        # a notion of "my own address" that doesn't map cleanly onto a
        # multi-mailbox corpus, and "sent" (keep-class) messages have the
        # employee as sender rather than recipient, so those two features
        # don't have a well-defined meaning for half the dataset anyway.
        rows.append({
            "from": sender, "subject": subject, "snippet": snippet,
            "label": label, "folder": folder_name, "user": user,
            "to_count": len(_addresses(msg, "To")),
            "cc_count": len(_addresses(msg, "Cc")),
            "has_attachment": msg_has_attachment(msg),
            "is_bulk_header": _is_bulk_header(msg),
            "is_reply_thread": bool(msg.get("In-Reply-To") or msg.get("References")),
            "sent_hour": _sent_hour(msg),
        })
        class_counts[label] += 1
        bucket_counts["keep" if label else "skip"] += 1

    # Cap the majority class so the training set isn't wildly imbalanced.
    keep_rows = [r for r in rows if r["label"]]
    skip_rows = [r for r in rows if not r["label"]]
    minority = min(len(keep_rows), len(skip_rows))
    cap = minority * MAX_IMBALANCE_RATIO
    random.shuffle(keep_rows)
    random.shuffle(skip_rows)
    keep_rows = keep_rows[:cap]
    skip_rows = skip_rows[:cap]
    final_rows = keep_rows + skip_rows
    random.shuffle(final_rows)

    print("Distinct folder names seen (top 30 by count):")
    for name, count in folder_counts.most_common(30):
        bucket = classify_folder(name, args.custom_folders)
        bucket_str = "excluded" if bucket is None else ("keep" if bucket else "skip")
        print(f"  {name:<25} {count:>7}  -> {bucket_str}")
    print(f"\nCollected before capping: keep={class_counts[True]}, skip={class_counts[False]}")
    print(f"After {MAX_IMBALANCE_RATIO}:1 imbalance cap: keep={len(keep_rows)}, skip={len(skip_rows)}, total={len(final_rows)}")

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump({"format": "enron-labeled-v1", "emails": final_rows}, f, ensure_ascii=False)
    print(f"Wrote {len(final_rows)} labeled emails to {args.out}")


if __name__ == "__main__":
    main()
