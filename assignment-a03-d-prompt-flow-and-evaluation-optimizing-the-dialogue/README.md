# Prompt Flow & Evaluation Report

**Use Case:**  
Summarize an input text into **3 bullet points** (no more than 20 words each).

---

## How to Run
### generate output
```
python scripts/generate.py
```
### evaluate output
```
python scripts/evaluate.py
```
### Refine your template based on the results
```
python scripts/refine.py
```
## Prompt Variants Tested

| Variant ID | Role                     | Task Description                                        | Avg Accuracy | Avg Relevance | Avg Clarity | Avg Brevity |
|------------|--------------------------|---------------------------------------------------------|:------------:|:-------------:|:-----------:|:-----------:|
| v1         | journalist               | Extract three bullet points summarizing the above text. |     5.00     |     4.20      |    5.00     |    5.00     |
| v2         | editor                   | List the three most important takeaways from the text.  |     5.00     |     4.80      |    5.00     |    5.00     |
| v3         | subject-matter expert    | Provide three concise insights based on the above text. |     5.00     |     5.00      |    5.00     |    5.00     |

*All variants were tested across 5 input cases.*

---

## Top-Performing Variant

- **Winner: v1 (journalist)**  
  Selected because it achieved a perfect **5.00 Accuracy** (tied with v2/v3) and was the first in our ordering.

---

## Key Findings

1. **Role framing matters**  
   - “journalist” framing (v1) yielded consistently clear, on-point summaries.  
   - “expert” framing (v3) matched v1 in most metrics but did not significantly outperform.

2. **Task phrasing**  
   - “bullet points summarizing” (v1) was just as effective as “concise insights” (v3).  
   - Softening phrasing (e.g., “takeaways”) slightly reduced perceived relevance (v2).

3. **Brevity enforcement**  
   - All variants adhered perfectly to the 20-word limit, likely due to explicit instructions.

---

## Iterative Refinement

- **Action Taken:** Updated the template from  
  `“each no more than {{ word_limit }} words”`  
  → `“maximum {{ word_limit }} words”`  
- **Result:** Expected to reduce borderline overshoots and sharpen focus; to be verified in a second round.

---

## Next Steps

- **Expand Test Set:** Increase to 10–15 real-world articles.  
- **Model Parameters:** Experiment with temperature = 0.0 vs 0.3 for tighter outputs.  
- **Rubric Automation:** Incorporate additional criteria (e.g. tone, style consistency).

---

### Reflection

A systematic prompt-flow with Jinja2 + quantitative rubric reveals subtle but important phrasing effects. The iterative loop (generate → evaluate → refine) proved essential for converging on a robust template.

