#!/usr/bin/env python3
"""Turn swing scores into normalized weights.

A swing is the improvement from an objective's threshold to its goal. Give the most valuable swing
100 and score the others relative to it; the weights are the scores divided by their sum.

Usage: python scripts/swing_weights.py 100 60 30
Output: JSON list of weights rounded to 3 decimals that sum to exactly 1.
Exit codes: 0 ok | 2 bad input
"""
import json
import sys


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if args else 2)
    try:
        scores = [float(x) for x in args]
    except ValueError:
        sys.stderr.write("error: scores must be numbers, e.g. 100 60 30\n")
        sys.exit(2)
    if any(s <= 0 for s in scores):
        sys.stderr.write("error: scores must be greater than 0 (drop objectives that add no value)\n")
        sys.exit(2)
    total = sum(scores)
    w = [round(s / total, 3) for s in scores]
    w[w.index(max(w))] = round(w[w.index(max(w))] + (1 - sum(w)), 3)  # absorb rounding in the largest weight
    print(json.dumps({"scores": scores, "weights": w, "sum": round(sum(w), 3)}))


if __name__ == "__main__":
    main()
