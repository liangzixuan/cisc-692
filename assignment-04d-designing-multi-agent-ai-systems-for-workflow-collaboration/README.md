# Multi-Agent AI Hiring Workflow

## Scenario Description
Multi-agent system for collaborative candidate screening, interview design, and culture fit evaluation.

## Agent Roles
- **Resume Screener**
- **Interview Designer**
- **Culture Fit Assessor**

## Workflow Overview
1. Resume Screener shortlists top candidates.
2. Interview Designer creates tailored questions.
3. Culture Fit Assessor evaluates candidate responses.

## Technical Implementation
- CrewAI used for agent orchestration.
- Clearly defined tasks and dependencies.

## Execution & Outputs
### 1 . Command to run the workflow
```bash
# Activate your virtual environment first, then:
python workflow.py
```
### 2 . What you’ll see
```bash
╭───────────────────────────── Crew Execution Started ─────────────────────────────╮
│  Name: crew │ ID: e9d232bc-2ca2-49cf-9ed5-05faaae4fd06                           │
╰──────────────────────────────────────────────────────────────────────────────────╯

🚀 Crew: crew
└── 📋 Task: … Screen resumes and shortlist top 5 candidates.
    Status: Executing Task…
╭──────────────── Agent Started: Resume Screener ───────────────╮
│ …                                                             │
╰───────────────────────────────────────────────────────────────╯
…
✅ Agent Final Answer:
```json
[
  { "name": "Alice Johnson",  "key_qualifications": [ … ] },
  { "name": "Michael Smith",  "key_qualifications": [ … ] },
  {
  "interview_questions": {
    "Alice Johnson": [
      "Can you describe a project where you successfully implemented RESTful APIs?",
      "How do you approach problem-solving in an agile team?",
      …
    ],
    "Michael Smith": [ … ]
    }
  },
  {
  "candidates": {
    "Alice Johnson": {
      "culture_fit_score": 8,
      "rationale": "Alice demonstrated strong technical skills …"
    },
    "Michael Smith": { "culture_fit_score": 9, … },
    …
  }
  }
]
```
### 3 . Monitoring logs
- Real-time: just keep the terminal open—CrewAI streams each agent’s start, thought, and final answer.
- File logging (optional): set an environment variable before running:
```bash
export CREWAI_LOGFILE=crew_run.log
python workflow.py
```
This writes the same rich trace to crew_run.log for later inspection.

The output is also saved into `logs_outputs_and_interactions.pdf`.

## Reflection
Design decisions.
I chose the hiring workflow because it maps naturally to three clearly separable roles—Resume Screener, Interview Designer, Culture-Fit Assessor. CrewAI’s task-context mechanism let each agent read the prior agent’s output without global shared memory, reinforcing modularity.

Key challenges & insights.

- Task schema changes. Recent CrewAI releases require an expected_output field. Omitting it triggered a pydantic ValidationError; adding concise JSON descriptions fixed the issue and clarified each agent’s deliverable.

- Prompt granularity. Early prompts were too generic, yielding vague lists. Tightening them (“exactly 4 questions per candidate”, “return valid JSON only”) improved downstream parsing reliability.

- Evaluation subjectivity. Scoring culture fit is inherently fuzzy. I mitigated this by instructing the assessor agent to ground its rationale in explicit company values.

Emerging directions.

- Automated feedback loop: pipe the Culture-Fit Assessor’s scores back to the Resume Screener to iteratively refine screening criteria.

- Persistence layer: store each agent’s JSON output in Redis or a simple SQLite DB so the pipeline can be resumed or audited.

- Alternative orchestration: replicate the same workflow with AutoGen to compare verbosity, flexibility, and error-handling ergonomics.

Overall, the assignment underscored that building robust multi-agent systems is less about fancy prompts and more about explicit contracts (clear I/O schemas, validation) and tight iterative refinement.