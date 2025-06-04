## 1. Developers Track-Specific Task
Build a rational intelligent agent system that performs an end-to-end workflow. This agent should:
- Retrieve, update, or log data using at least two distinct storage styles (e.g., SQL + in-memory cache or NoSQL)
- Make decisions using a behavior tree or function-triggered logic
- Demonstrate batch or stream handling
- Respect identity governance via a mock credential or access scope
- Include an internal policy enforcement point (e.g., restrict action if “risk_score > threshold” or "no token provided")
- Please carefully review the rubric aligned to your track before you begin—your deliverables, tools, and evaluation criteria are tailored to reflect your background and expected approach.

## 2. NoteGPT Workflow
Workflow Goal: A user uploads or pastes a document (PDF, webpage, or text). The NoteGPT agent must:
- Ingest & Preprocess the document (OCR if needed, detect language).
- Classify the content type (e.g., “academic paper,” “news article,” “slide deck”).
- Summarize into key points (500‐word summary for an academic paper, 5 bullet points for a news article, etc.).
- Generate Notes (e.g., a mind‐map outline, summary paragraphs, or Q&A pairs).
- Store both the raw content and the generated summary in a database.
- Enforce Governance: If the document contains flagged topics (e.g., prohibited content, copyrighted text), require human review or deny summary.
- Batch Job: Nightly generate “study guide” digests for all “academic papers” processed that day.
- Stream: Real‐time “new document processed” notifications to a monitoring dashboard.

## 3. System Overview
NoteGPT is an AI‐powered learning assistant that ingests user‐provided documents (PDF, text, images via OCR), classifies them, summarizes content, and generates structured notes. Core features demonstrated in this assignment:
- **Automated Document Processing**: Full pipeline from upload → classification → summarization → note generation.
- **Real‐Time Monitoring**: Uses Redis Streams to notify a monitoring dashboard and human Reviewers about processed or flagged documents.
- **Governance Checkpoints**: Prohibited content detection, subscription‐based word‐limit enforcement, and human review for flagged content.

## 4. Use Cases
1. **FreeUser Summarization**:  
   - A FreeUser uploads a 1,500‐word academic paper. Agent classifies as “academic,” runs a 500‐word summary template, stores results in SQL, and sends a notification to `processed_notifications`.  
   - Log shows classification, summary style, and final status.
2. **PremiumUser Flagged Content**:  
   - A PremiumUser uploads a 3,200‐word research report containing “self‐harm”. Agent loads `prohibited_keywords`, finds “self‐harm,” routes doc to `review_queue`, updates the document’s status to `pending_review`, and logs a policy exception. A human Reviewer sees the flagged doc in real time via `consumer.py`.
3. **Nightly Academic Digest**:  
   - At 02:00 AM, the nightly batch job runs. It queries SQL for all “academic” summaries created in the last 24 hours, concatenates them into `archives/digest_{date}.txt`, and logs this digest in the `digests` table.
4. **Admin Updates Policy**:  
   - An Admin wants to add “spoiler” to the prohibited list. They call `POST /update_policy/` with `key_name="prohibited_keywords"` and a JSON array including the new keyword. The service updates SQL, and the Redis cache is refreshed to include “spoiler.”

## 5. Governance Rules
1. **`max_words_free`** = 2000 (documents > 2,000 words rejected for `FreeUser`).  
2. **`prohibited_keywords`** (e.g., `["self-harm", "hate", "terror"]`): any match → flagged.  
   - If `role == PremiumUser` → route to human Review (`review_queue`).  
   - Else (FreeUser or anonymous) → auto‐reject with a 403 error.
3. **Summarization Templates** stored in `policies` table:  
   - `"template_academic"` → “Write a 500‐word abstract.”  
   - `"template_news"` → “List 5 key bullet points.”  
   - `"template_slides"` → “Generate 10‐point outline.”  
   - `"template_other"` → “Produce a 200‐word summary.”
4. **Identity Scopes** (encoded in JWT):  
   - `FreeUser` → limited to < 2,000 words; no review queue.  
   - `PremiumUser` → unlimited word count; flagged docs go to `review_queue`.  
   - `Reviewer` → can call `/override_review/` to approve or reject flagged docs.  
   - `Admin` → can call `/update_policy/` to modify `prohibited_keywords` or templates.

## 6. Architectural Tradeoffs
### a) SQL vs Redis (CAP)
- **SQL (Postgres/SQLite)**:  
  - Ensures **strong consistency** for raw text, summaries, and notes (ACID).  
  - Guarantees durability: if the DB crashes, no data is lost.  
  - Drawback: storing large text blobs is slower; possible performance bottleneck under heavy load.
- **Redis Streams (review_queue, processed_notifications)**:  
  - **Availability + Partition Tolerance** (AP): if a Redis shard is down, we still accept new events and replay later.  
  - Provides low latency (sub‐millisecond) for pub/sub notifications.  
  - If Redis node fails, ephemeral events may be lost, but the core data is still in SQL.

### b) Batch vs Stream Processing
- **Stream (Real‐Time)**:  
  - *Pros*: Immediate routing of flagged docs to Reviewers; real‐time monitoring of processed docs.  
  - *Cons*: Requires a running Redis instance; if too many events flood the queue, some may backlog.
- **Batch (Nightly Digest)**:  
  - *Pros*: Aggregates academic summaries once per day for a “study guide,” reducing load on SQL by running during off‐hours.  
  - *Cons*: Data is only available next morning; if an academic summary fails to get stored, that day’s digest is incomplete.

### c) Autonomy vs Control
- **Autonomy**:  
  - The agent decides summarization style based on classification.  
  - It automatically ingests, classifies, summarizes, and stores without human intervention (for non‐flagged content).
- **Governance**:  
  - Prohibited content detection forces human review or auto‐reject.  
  - Only Admin can update prohibited lists or templates.  
  - Reviewer role can manually override flagged docs (ensuring human in the loop for sensitive content).

### d) Scalability & Maintainability
- **Scalability**:  
  - Redis Streams can scale horizontally: multiple consumer instances can all read from `processed_notifications` or `review_queue` (consumer groups).  
  - SQL (Postgres) can be read‐replicated if load increases (but SQLite can be used for simplicity in small deployments).
- **Maintainability**:  
  - Agent logic is separated in `agent_logic.py`.  
  - Policies are stored as JSON in the `policies` table, so changes do not require code modifications.  
  - Redis Hash caches policies and templates for fast lookups.

## 7. How to Run
### Prerequisites
- Python 3.9+  
- Docker & Docker Compose for spinning up Redis + SQLite

### 1. Clone the Repo
```bash
git clone https://github.com/liangzixuan/cisc-692.git
cd cisc-692/assignment-a02-architecting-and-governing-autonomous-ai-agents
```
### 2. Install Dependencies
```bash
cd app
pip install -r requirements.txt
```
### 3. Start Redis
In the root directory of the project, run:
```bash
docker-compose up -d redis
```
### 4. Initialize SQL Database
This script creates tables users, documents, summaries, policies, digests
```bash
python app/db.py
```
### 5. Start the FastAPI Server
```bash
cd app
uvicorn main:app --reload
```

### 6. Start the Reviewer Consumer (in a separate terminal)
```bash
cd app
python consumer.py
```

### 7. Run the Nightly Digest Manually
```bash
python app/tasks/generate_daily_digest.py
```

### 8. Testing Endpoints
Obtain a JWT
```bash
curl -X POST "http://127.0.0.1:8000/token/?user_id=alice123&role=FreeUser"
curl -X POST "http://127.0.0.1:8000/token/?user_id=bob456&role=PremiumUser"
curl -X POST "http://127.0.0.1:8000/token/?user_id=rev001&role=Reviewer"
curl -X POST "http://127.0.0.1:8000/token/?user_id=admin01&role=Admin"
```
submit a document
```bash
TOKEN=<free_user_token>
curl -X POST http://127.0.0.1:8000/submit_document/ -H "Authorization: Bearer $TOKEN" -F "file=@test-documents/test_academic.txt"
```
submit a document that exceeds 2000 words limit
```bash
TOKEN=<free_user_token>
curl -X POST http://127.0.0.1:8000/submit_document/ -H "Authorization: Bearer $TOKEN" -F "file=@test-documents/large_test_academic.txt"
```
submit a document with prohibited content
```bash
TOKEN=<premium_user_token>
curl -X POST http://127.0.0.1:8000/submit_document/ -H "Authorization: Bearer $TOKEN" -F "file=@test-documents/test_flagged.txt"
```
reviewer overrides a flagged document
```bash
TOKEN=<reviewer_token>
curl -X POST http://127.0.0.1:8000/override_review/ -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"doc_id":<flagged_doc_id>, "action":"approve","notes":"Approved for research"}'
```
admin updates the prohibited keywords policy
```bash
TOKEN=<admin_token>
curl -X POST http://127.0.0.1:8000/update_policy/  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json"  -d '{"key_name":"prohibited_keywords","new_value":"[\"self-harm\",\"hate\",\"terror\",\"spoiler\"]"}'
```
view the updated list of prohibited_keywords
```bash
docker exec -it notegpt_redis redis-cli HGETALL prohibited_keywords
```
With every command, we can check the logs in `app/logs/` to see the detailed outcomes.

## 8. Self‐Assessment Rubric
### Agent Behavior & Decision Logic
How I satisfied it: 
- Implemented a behavior tree in `agent_logic.py` that handles document classification, summarization, and note generation based on content type. The agent uses Redis Streams for real‐time notifications and human review routing.
- Preprocess & classify (validated JWT, fetched policies, fetched user role, ingested text)   
- Governance check (flagged vs allowed). 
- Summarization & note generation (LLM calls). 
- SQL updates and Redis notifications (stream events).
### Identity & Governance Logic
- JWT auth with `validate_jwt_and_get_role()` in `auth.py`.
- ABAC: enforced `max_words_free` for `FreeUser`.
- Prohibited content check: `redis_client.hget("prohibited_keywords", word)` → flagged. 
- Human review: flagged docs go to `review_queue` and require `Reviewer` role to override.
### Architectural Tradeoffs
- Chose SQL (Postgres/SQLite) for document durability (CP tradeoff) and Redis Streams for real‐time (AP). 
- Explained CAP: SQL is CP, Redis is AP.   
- Discussed Streams vs Batch: real‐time notifications vs nightly digest.
### Code & Observability
- Code is modular (`auth.py`, `policies.py`, `agent_logic.py`, `consumer.py`, etc.).   
- Logging: `logs/event_log.json` and `logs/policy_exceptions.json` with JSON entries. 
### Technical Reflection & Documentation
- README.md covers system overview, use cases, governance rules, tradeoffs, how to run, directory structure. 
- Embedded code snippets, sample log entries, and a high‐level architecture ASCII diagram.  
### Presentation & Demo
- Provided instructions to obtain JWTs, submit docs, review flagged docs, and run nightly digest.