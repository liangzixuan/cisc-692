# 📄  Sales Demo Scheduler — Action-Enabled Agent

> **Assignment 05-D:** Action-Enabled Agents — Designing AI Systems That Deliver  
> Course Code: CISC 692 • Next-Gen AI System Design Patterns

---

## 1 . Scenario Description

Inbound leads email our sales mailbox every day.  
Manually parsing each message, checking the CRM, and sending a personalized
demo invite is repetitive and error-prone.

**Goal:** Deploy an LLM-powered agent that automatically:

1. Parses a new-lead email.  
2. Looks up (or inserts) the prospect in a CRM (SQLite).  
3. Generates a tailored demo-invite email.  
4. Sends the email (mock SMTP).  
5. Logs every action to CSV for audit.

Deliverable: a running Python CLI (`python demo.py`) that
executes the full workflow end-to-end, plus logs and sample outputs.

---

## 2 . System Architecture

![System Architecture](https://github.com/liangzixuan/cisc-692/blob/main/assignment-a05d-action-enabled-agents-designing-ai-systems-that-deliver/architecture.png)
- LLM Orchestration: OpenAI with function-calling. Decides which tool to call and when.
- Tools/Actions: Plain Python functions (sync & async). Business logic: DB, email, logging
- Data Storage: SQLit (aiosqlite). Lightweight CRM table.
- Messaging: Mock SMTP and write JSON files. Safe offline email demo.
- Audit Trail: CSV logging of all actions. Transparent trace of every step.

## 3. Agent and Tools
### Tools
- lookup_prospect: Async; auto-creates table if missing
- craft_email: Flexible signature prevents crashes
- send_email: Writes file to `sent/` folder 
- record_action: Appends row to CSV log
### Agent
The agent uses OpenAI’s chat‐completion with explicit
`tools=[ … ]`.  
Each tool call is resolved by an internal Python map; async tools are awaited,
sync tools run in a thread.

## 4. Execution
### Run the workflow
```bash
python demo.py
```
### Sample terminal output
```bash
=== FINAL AGENT MESSAGE ===
I have sent a personalized demo invitation email to Jane Chen at Acme Corp, confirming her request for a demo. The email invites her to schedule a 15-minute live demo next week. 

Additionally, I have logged the action of receiving the demo request. If there's anything else you need, feel free to ask!

```
### View Outputs
```bash
sent/               # mock email JSONs
logs/action_log.csv # ISO-timestamped action trace
```

## 5. Demo Video
(TBD)

## 6. Reflection
Design Choices
- Function-calling keeps LLM deterministic: each step is a typed contract → easier to debug than raw prompting.

- SQLite + aiosqlite gives async DB access without external infra.

- Each tool is idempotent and logs its own outcome → safe to re-run.

Challenges
- Parameter mismatches: LLM omitted email_dict, causing runtime
TypeError. Fixed with stricter JSON schema and tolerant Python defaults.

- Tool-call protocol: v1 API requires exact tool_call_id pairing.
Added loop logic to echo IDs and iterate over all calls.

- Async vs. sync: Mixed coroutine/sync functions → used
inspect.iscoroutinefunction to route correctly.

Insights & Future Work
- Small schema tweaks drastically improve agent reliability.

- Next step: integrate real email (SendGrid) and Kalender API to auto-book slots.

- Could generalize the pattern into a reusable “Sales Bot” template for other teams.

## 7. Repository Map
```bash
├── agent.py          # LLM orchestration + tool loop
├── actions.py        # lookup_prospect, craft_email, send_email, record_action
├── init_db.py        # seeds SQLite
├── demo.py           # CLI entrypoint
├── data/             # sample_lead.txt, prospects.db
├── sent/             # mock email outputs
├── logs/action_log.csv
└── README.md         # (this file)

```