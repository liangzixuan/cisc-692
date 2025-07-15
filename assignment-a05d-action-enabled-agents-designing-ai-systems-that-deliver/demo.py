# CLI entrypoint to run end-to-end

import asyncio, pathlib
from agent import run_agent

if __name__ == "__main__":
    lead_text = pathlib.Path("data/sample_lead.txt").read_text()
    final = asyncio.run(run_agent(lead_text))
    print("=== FINAL AGENT MESSAGE ===")
    print(final)
