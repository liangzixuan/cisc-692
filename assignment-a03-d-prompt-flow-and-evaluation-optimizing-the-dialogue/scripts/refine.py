import csv
import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
EVAL_CSV  = os.path.join(DATA_DIR, 'evaluations.csv')
TEMPLATE  = os.path.join(os.path.dirname(__file__), '..', 'prompts', 'template.j2')

# 1. Compute average scores per variant
scores = {}
counts = {}
with open(EVAL_CSV) as f:
    reader = csv.DictReader(f)
    for r in reader:
        vid = r['variant_id']
        acc = float(r['Accuracy'])
        scores[vid] = scores.get(vid, 0) + acc
        counts[vid] = counts.get(vid, 0) + 1

avgs = {vid: scores[vid]/counts[vid] for vid in scores}
winner = max(avgs, key=lambda v: avgs[v])
print(f"Top variant: {winner} (avg Accuracy={avgs[winner]:.2f})")

# 2. Rewrite template.j2 to bake in better word phrasing
with open(TEMPLATE) as f:
    text = f.read()
# Example: replace 'no more than {{ word_limit }} words' with 'maximum {{ word_limit }} words'
refined = text.replace('no more than {{ word_limit }} words', 'maximum {{ word_limit }} words')

with open(TEMPLATE, 'w') as f:
    f.write(refined)
print("Template refined based on evaluation.")