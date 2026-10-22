# RSB-1000 — RevealWire Scam Benchmark

A labeled, **fully synthetic** 1,000-message benchmark for testing how well AI models detect scams.
Built for the [Reveal Wire](https://www.youtube.com/@RevealWire) investigation
*"We Tested 2 Open AIs Against 200 Phishing Attacks"* (EP03, October 2026).

**Why it exists:** when we researched the episode, we found *zero* published scam/phishing-detection
scores for the models we wanted to test. So we built the benchmark ourselves — 1,000 messages,
labeled before any model ran, frozen before the first inference — and we're publishing it so anyone
can reproduce our numbers or test their own models.

## What's in the dataset

`data/rsb-1000-v1.jsonl` — 1,000 records, one JSON object per line.
SHA256: `200ad4cfcb6e7c7a1e1d7344376ec0926ea63d1cfd7a86db7c28f28f03953100`

| Label | Count |
|---|---|
| `scam` | 780 |
| `legitimate` | 220 |

Categories: legitimate control (200) · phishing (200, incl. **60 AiTM** adversary-in-the-middle) ·
fake job (150) · invoice fraud (150) · impersonation (100) · investment fraud (100) ·
romance (50) · ambiguous hard cases (50, 30 scam / 20 legitimate).

Fields per record: `id` (`RSB-0001`…`RSB-1000`), `category`, `subcategory`, `difficulty`
(`easy`/`medium`/`hard`), `text`, `ground_truth`, `tells` (scam indicators, for grading
explanations), `safe_action` (correct user advice, for grading action quality).

**100% synthetic.** Every message was written as a test fixture. No real victim messages, no real
personal data. Brand names, domains, phone numbers, email addresses, and personal names are
fictional; scam lookalike domains are invented examples, not real domains.

## Our measured results (EP03, October 2026)

Our measurements on this dataset under our protocol (zero-shot classifier prompt, temperature 0,
identical system prompt per model) — not universal claims about the models:

| Model | Scam recall | False-positive rate |
|---|---|---|
| Qwen 3.8-27B | 98.9% | 11.6% |
| GPT-OSS 20B | 94.0% | 23.1% |

## How to run an evaluation

1. Run your model/classifier over `data/rsb-1000-v1.jsonl` and write one prediction per line to
   `predictions.jsonl`:
   ```json
   {"id": "RSB-0001", "prediction": "scam"}
   ```
   `prediction` must be `scam` or `legitimate` (case-insensitive). Order doesn't matter; records are
   matched by `id`.
2. Score it:
   ```bash
   python eval.py --dataset data/rsb-1000-v1.jsonl --predictions predictions.jsonl
   ```
   This prints scam recall, false-positive rate, accuracy, and a per-category breakdown, e.g.:
   ```
   Scam recall (sensitivity):  98.9%  (771/780)
   False-positive rate:        11.6%  (26/220)
   Accuracy:                   97.7%
   ```
   Optional: `--by-category` prints recall/FPR per category; `--output results.json` saves the
   metrics as JSON.

## Limitations

- Synthetic by design — not real-world traffic; scores here don't guarantee live-inbox performance.
- English, India-context flavored (UPI, Aadhaar-linking lures, etc.); not a global sample.
- Frozen October 2026; scam tactics evolve. The ambiguous tier (50 records) is judgment-based —
  ground truth there is the *safer* interpretation.

## How to cite

```bibtex
@dataset{revealwire_rsb1000_2026,
  title  = {RSB-1000: RevealWire Scam Benchmark v1},
  author = {Reveal Wire},
  year   = {2026},
  url    = {https://www.youtube.com/@RevealWire},
  note   = {1,000 synthetic labeled messages for scam/phishing detection benchmarking, CC-BY-4.0}
}
```

## Contributing

Found a mislabeled record or a broken fixture? Open an issue with the record `id` and your reasoning.
The frozen v1 file will not be edited (reproducibility); accepted corrections go into the v2 draft.

## License

Data: CC-BY-4.0 (attribution to Reveal Wire). Code (`eval.py`): MIT.
