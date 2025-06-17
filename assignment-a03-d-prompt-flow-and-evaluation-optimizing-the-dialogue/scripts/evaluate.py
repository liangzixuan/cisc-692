#!/usr/bin/env python3
import os, csv, json
from textwrap import dedent
from openai import OpenAI

# ─── CONFIG ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL          = "gpt-4"
THIS_DIR       = os.path.dirname(__file__)
OUTPUT_CSV     = os.path.join(THIS_DIR, "..", "data", "outputs.csv")
EVAL_CSV       = os.path.join(THIS_DIR, "..", "data", "evaluations.csv")
RUBRIC_FILE    = os.path.join(THIS_DIR, "..", "rubric.md")

client = OpenAI(api_key=OPENAI_API_KEY)


def load_rubric():
    with open(RUBRIC_FILE, "r", encoding="utf-8") as f:
        return f.read()


def call_evaluator(response: str, rubric: str):
    prompt = dedent(f"""
    You are an impartial evaluator.  Using this rubric:
    {rubric}

    Rate the following response on each criterion (1–5):

    Response:
    \"\"\"
    {response}
    \"\"\"

    Return a JSON object exactly like:
      {{"Accuracy":int, "Relevance":int, "Clarity":int, "Brevity":int, "Structure":int}}
    """)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
    )
    return json.loads(resp.choices[0].message.content)


def main():
    rubric = load_rubric()

    with open(OUTPUT_CSV, newline="", encoding="utf-8") as inf, \
         open(EVAL_CSV,   "w", newline="", encoding="utf-8") as outf:
        reader = csv.DictReader(inf)
        # --- FIX IS ON THE LINE BELOW ---
        fieldnames = reader.fieldnames + ["Accuracy", "Relevance", "Clarity", "Brevity", "Structure"]
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            # Handle potential missing keys from the evaluator response gracefully
            try:
                scores = call_evaluator(row["response"], rubric)
                # Ensure all expected score keys are present, defaulting to a neutral value if not
                full_scores = {
                    "Accuracy": scores.get("Accuracy"),
                    "Relevance": scores.get("Relevance"),
                    "Clarity": scores.get("Clarity"),
                    "Brevity": scores.get("Brevity"),
                    "Structure": scores.get("Structure")
                }
                row.update(full_scores)
                writer.writerow(row)
                print(f"[EVAL] {row['variant_id']}×{row['input_id']} → {scores}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"[ERROR] Failed to evaluate {row['variant_id']}×{row['input_id']}: {e}")
                # Write the row anyway but with empty scores
                empty_scores = {"Accuracy": "", "Relevance": "", "Clarity": "", "Brevity": "", "Structure": ""}
                row.update(empty_scores)
                writer.writerow(row)


if __name__ == "__main__":
    main()