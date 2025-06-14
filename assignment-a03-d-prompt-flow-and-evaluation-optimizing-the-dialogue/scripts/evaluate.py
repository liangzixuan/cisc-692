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
      {{"Accuracy":int, "Relevance":int, "Clarity":int, "Brevity":int}}
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
        fieldnames = reader.fieldnames + ["Accuracy", "Relevance", "Clarity", "Brevity"]
        writer = csv.DictWriter(outf, fieldnames=fieldnames)
        writer.writeheader()

        for row in reader:
            scores = call_evaluator(row["response"], rubric)
            row.update(scores)
            writer.writerow(row)
            print(f"[EVAL] {row['variant_id']}×{row['input_id']} → {scores}")


if __name__ == "__main__":
    main()
