"""
Samples a stratified subset of the folder-heuristic-labeled Enron data for
manual review, withholding the heuristic label so whoever labels it in
enron_spotcheck.html isn't biased by it. The tool merges the withheld label
back in afterward to compute heuristic-vs-human agreement.

Usage:
    venv/bin/python enron/sample_spotcheck.py \
        --labeled enron/enron_labeled.json \
        --out ../enron_spotcheck_sample.json --n 50
"""
import argparse
import json
import os
import random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled", default=os.path.join(os.path.dirname(__file__), "enron_labeled.json"))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ap.add_argument("--out", default=os.path.join(project_root, "enron_spotcheck_sample.json"))
    ap.add_argument("--n", type=int, default=50, help="per class (so total sample size is 2n)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    with open(args.labeled, encoding="utf-8") as f:
        data = json.load(f)
    emails = data["emails"]
    keep_rows = [e for e in emails if e["label"]]
    skip_rows = [e for e in emails if not e["label"]]

    random.seed(args.seed)
    sample = random.sample(keep_rows, min(args.n, len(keep_rows))) + \
        random.sample(skip_rows, min(args.n, len(skip_rows)))
    random.shuffle(sample)

    out_emails = []
    heuristic_labels = {}
    for i, e in enumerate(sample):
        eid = str(i)
        out_emails.append({"id": eid, "from": e["from"], "subject": e["subject"], "snippet": e["snippet"]})
        heuristic_labels[eid] = e["label"]

    payload = {
        "format": "enron-spotcheck-sample-v1",
        "emails": out_emails,
        "heuristic_labels": heuristic_labels,
    }
    out_path = os.path.normpath(args.out)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(out_emails)} spot-check emails ({args.n} keep + {args.n} skip, heuristic labels withheld) to {out_path}")


if __name__ == "__main__":
    main()
