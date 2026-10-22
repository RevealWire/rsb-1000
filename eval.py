#!/usr/bin/env python3
"""eval.py — score scam/legitimate predictions against the RSB-1000 benchmark.

Usage:
    python eval.py --dataset data/rsb-1000-v1.jsonl --predictions predictions.jsonl
    python eval.py --dataset data/rsb-1000-v1.jsonl --predictions predictions.jsonl --by-category
    python eval.py --dataset data/rsb-1000-v1.jsonl --predictions predictions.jsonl --output results.json

The predictions file is JSONL, one object per line:
    {"id": "RSB-0001", "prediction": "scam"}

`prediction` must be "scam" or "legitimate" (case-insensitive). Lines are matched
to the dataset by `id`; order does not matter. Duplicate or unknown ids are errors.

Metrics (scam = positive class):
    recall      = TP / (TP + FN)   — share of scam messages correctly flagged
    fpr         = FP / (FP + TN)   — share of legitimate messages wrongly flagged
    accuracy    = (TP + TN) / total
Only the standard library is required.
"""

import argparse
import json
import sys
from collections import defaultdict

VALID = {"scam", "legitimate"}


def load_jsonl(path, key_field=None):
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                sys.exit(f"error: {path}:{n}: invalid JSON: {e}")
    if key_field:
        seen = set()
        for r in rows:
            if r.get(key_field) in seen:
                sys.exit(f"error: {path}: duplicate {key_field} {r.get(key_field)!r}")
            seen.add(r.get(key_field))
    return rows


def pct(num, den):
    return 100.0 * num / den if den else 0.0


def main():
    ap = argparse.ArgumentParser(description="Score predictions against RSB-1000.")
    ap.add_argument("--dataset", required=True, help="path to rsb-1000-v1.jsonl")
    ap.add_argument("--predictions", required=True, help="path to predictions.jsonl")
    ap.add_argument("--by-category", action="store_true",
                    help="also print recall/FPR per category")
    ap.add_argument("--output", help="write metrics as JSON to this path")
    args = ap.parse_args()

    dataset = load_jsonl(args.dataset, key_field="id")
    truth = {}
    cats = {}
    for r in dataset:
        if r.get("ground_truth") not in VALID:
            sys.exit(f"error: dataset record {r.get('id')}: bad ground_truth")
        truth[r["id"]] = r["ground_truth"]
        cats[r["id"]] = r.get("category", "unknown")

    preds = load_jsonl(args.predictions, key_field="id")
    pred_map = {}
    for n, r in enumerate(preds, 1):
        p = str(r.get("prediction", "")).strip().lower()
        if p not in VALID:
            sys.exit(f"error: predictions line {n} (id={r.get('id')!r}): "
                     f"prediction must be 'scam' or 'legitimate', got {r.get('prediction')!r}")
        pred_map[r.get("id")] = p

    unknown = [i for i in pred_map if i not in truth]
    if unknown:
        sys.exit(f"error: {len(unknown)} prediction id(s) not in dataset, e.g. {unknown[:3]}")
    missing = [i for i in truth if i not in pred_map]
    if missing:
        sys.exit(f"error: {len(missing)} dataset id(s) have no prediction, e.g. {missing[:3]}")

    tp = fp = tn = fn = 0
    per_cat = defaultdict(lambda: [0, 0, 0, 0])  # tp, fp, tn, fn
    for i, t in truth.items():
        p = pred_map[i]
        if t == "scam" and p == "scam":
            tp += 1; per_cat[cats[i]][0] += 1
        elif t == "scam":
            fn += 1; per_cat[cats[i]][3] += 1
        elif p == "scam":
            fp += 1; per_cat[cats[i]][1] += 1
        else:
            tn += 1; per_cat[cats[i]][2] += 1

    metrics = {
        "n_total": len(truth),
        "n_scam": tp + fn,
        "n_legitimate": fp + tn,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "recall": round(pct(tp, tp + fn), 2),
        "false_positive_rate": round(pct(fp, fp + tn), 2),
        "accuracy": round(pct(tp + tn, len(truth)), 2),
    }

    print(f"Scored {metrics['n_total']} records "
          f"({metrics['n_scam']} scam / {metrics['n_legitimate']} legitimate)")
    print(f"Scam recall (sensitivity):  {metrics['recall']:5.1f}%  ({tp}/{tp + fn})")
    print(f"False-positive rate:        {metrics['false_positive_rate']:5.1f}%  ({fp}/{fp + tn})")
    print(f"Accuracy:                   {metrics['accuracy']:5.1f}%")

    if args.by_category:
        metrics["by_category"] = {}
        print("\nPer-category (recall on scam cats / FPR on legitimate cats):")
        for cat in sorted(per_cat):
            ctp, cfp, ctn, cfn = per_cat[cat]
            if ctp + cfn > 0:  # scam-majority category
                r = pct(ctp, ctp + cfn)
                print(f"  {cat:15s} recall {r:5.1f}%  ({ctp}/{ctp + cfn})")
                metrics["by_category"][cat] = {"recall": round(r, 2)}
            else:
                f = pct(cfp, cfp + ctn)
                print(f"  {cat:15s} FPR    {f:5.1f}%  ({cfp}/{cfp + ctn})")
                metrics["by_category"][cat] = {"false_positive_rate": round(f, 2)}

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nMetrics written to {args.output}")


if __name__ == "__main__":
    main()
