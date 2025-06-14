#!/usr/bin/env python3
import os, csv, json, time
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI

# ─── CONFIG ─────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL          = "gpt-4"   # or "gpt-3.5-turbo"
THIS_DIR       = os.path.dirname(__file__)
PROMPT_DIR     = os.path.join(THIS_DIR, "..", "prompts")
VARIANTS_FILE  = os.path.join(THIS_DIR, "..", "data", "variants.json")
INPUTS_FILE    = os.path.join(THIS_DIR, "..", "data", "test_inputs.txt")
OUTPUT_CSV     = os.path.join(THIS_DIR, "..", "data", "outputs.csv")

# Initialize new OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)


def load_variants():
    with open(VARIANTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_inputs():
    with open(INPUTS_FILE, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def render_prompt(template, variant, input_text):
    return template.render(
        role=variant["role"],
        task_description=variant["task_description"],
        bullet_count=variant["bullet_count"],
        word_limit=variant["word_limit"],
        input_text=input_text,
    )


def call_llm(prompt: str):
    start = time.time()
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    latency = (time.time() - start) * 1000
    # Access new-style response
    content = resp.choices[0].message.content
    return content.strip(), latency


def main():
    # Setup Jinja2
    env = Environment(loader=FileSystemLoader(PROMPT_DIR))
    template = env.get_template("template.j2")

    variants = load_variants()
    inputs   = load_inputs()

    # Write CSV header
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        w = csv.writer(csvfile)
        w.writerow(["variant_id", "input_id", "prompt", "response", "latency_ms"])

        for v in variants:
            for i, text in enumerate(inputs, start=1):
                prompt_text = render_prompt(template, v, text)
                response, latency = call_llm(prompt_text)
                w.writerow([v["id"], f"input{i}", prompt_text, response, f"{latency:.1f}"])
                print(f"[GEN] {v['id']}×input{i} → {latency:.1f}ms")


if __name__ == "__main__":
    main()
