# Agent Architecture — AI Helpdesk

## Hackathon Problem Statement

| Question | Answer |
|----------|--------|
| **Who has this problem?** | Employees reporting IT issues; IT support engineers triaging tickets; IT managers overseeing operations |
| **What bottleneck?** | Manual L1 triage: categorization, severity, spam filtering, duplicate detection, and assignment take 10–20 min/ticket and cause misrouting |
| **Why solve it?** | Reduces ticket noise, routes issues faster to the right engineer, and frees IT staff for complex work |
| **Can it be reproduced?** | Yes — mock AI provider, seeded demo data, `python -m evaluation.run_eval` |

---

## Agentic Workflow Overview

The system uses a **coordinator pattern**: `AIHelpdeskService.process_issue()` orchestrates specialized agents in sequence. Each agent has a single responsibility, versioned prompts, and structured JSON output stored in `AIAnalysis`.

```
User submits issue
        │
        ▼
┌───────────────────┐
│ Issue Orchestrator │  (AIHelpdeskService.process_issue)
└─────────┬─────────┘
          │
    ┌─────┴─────┬──────────┬────────────┬───────────┐
    ▼           ▼          ▼            ▼           ▼
 Analysis   Validation  Duplicate   Classification  Severity
  Agent       Agent      Agent         Agent         Agent
    │           │          │            │           │
    └─────┬─────┴──────────┴────────────┴───────────┘
          ▼
   Decision: CREATE | SUPPRESS | DUPLICATE
          │
          ▼ (if CREATE)
   Assignment Agent  ──►  Notification Service
          │
          ▼
   Human IT engineer investigates (human-in-the-loop)
```

---

## Agent Definitions

### 1. Analysis Agent
- **Prompt:** `backend/app/ai/prompts/issue_analysis_v1.txt`
- **Input:** title, description, device, OS, location, application
- **Output:** `problem_summary`, `possible_category`, `initial_suggestions`, `requires_it_intervention`, `confidence`
- **Purpose:** First-pass understanding + immediate troubleshooting for the user

### 2. Validation Agent
- **Prompt:** `backend/app/ai/prompts/validation_v1.txt`
- **Input:** issue text + analysis context
- **Output:** `is_genuine`, `confidence`, `reason`, `requires_it_intervention`
- **Purpose:** Suppress spam, invalid, and self-service requests before ticket creation
- **Safety rule:** P1/P2 issues are never auto-suppressed on low confidence

### 3. Duplicate Detection Agent
- **Prompt:** `backend/app/ai/prompts/duplicate_detection_v1.txt`
- **Input:** issue + list of open tickets (title, description, ticket_number)
- **Output:** `is_duplicate`, `similar_ticket_id`, `confidence`
- **Purpose:** Link to existing incidents instead of creating redundant tickets
- **Threshold:** configurable via `AI_DUPLICATE_THRESHOLD` (default 0.90)

### 4. Classification Agent
- **Prompt:** `backend/app/ai/prompts/categorization_v1.txt`
- **Output:** `category`, `subcategory`, `confidence`
- **Purpose:** Auto-categorize without user needing IT taxonomy knowledge

### 5. Severity Agent
- **Prompt:** `backend/app/ai/prompts/severity_v1.txt`
- **Output:** `severity` (P1–P4), `priority`, `impact`, `urgency`, `business_impact`, `reasoning`
- **Purpose:** Business-impact-based priority, not keyword-only escalation

### 6. Assignment Agent
- **Module:** `backend/app/assignment/engine.py`
- **Input:** category, subcategory, severity + IT engineer profiles (expertise, workload)
- **Scoring:** expertise (40) + workload (30) + availability (20) + severity capability (10)
- **Purpose:** Route to best-fit engineer, not round-robin

---

## Orchestration Logic

File: `backend/app/ai/service.py` → `AIHelpdeskService.process_issue()`

```python
1. analysis   = AnalysisAgent(issue)
2. suggestions = TroubleshootingAgent(issue)
3. validation  = ValidationAgent(issue)
4. duplicate   = DuplicateAgent(issue, existing_tickets)

IF duplicate.confidence >= threshold AND is_duplicate:
    RETURN suppress(DUPLICATE)

IF NOT validation.is_genuine OR self_service:
    RETURN suppress(INVALID | SELF_SERVICE)

5. categorization = ClassificationAgent(issue)
6. severity       = SeverityAgent(issue)
7. CREATE ticket
8. assignee       = AssignmentAgent(category, severity, team)
9. NOTIFY assignee (+ manager if P1)
```

---

## Tools & Context Each Agent Receives

| Agent | Context / Tools |
|-------|-------------------|
| Analysis | Issue fields, knowledge base articles (future RAG) |
| Validation | Issue text, prior analysis, validation threshold |
| Duplicate | Open tickets from DB, duplicate threshold |
| Classification | Issue text, analysis summary |
| Severity | Issue text, business impact signals |
| Assignment | IT profiles (expertise, active ticket count, availability) |

---

## Human-in-the-Loop Checkpoints

1. **Manager override** — category, severity, assignment, validation (`/api/tickets/{id}/override-validation`)
2. **IT engineer actions** — accept, escalate, resolve (AI cannot close tickets)
3. **User confirmation** — must confirm before ticket closes
4. **Audit log** — every override and status change recorded

---

## AI Provider Abstraction

```python
class AIProvider(ABC):
    async def complete_json(system_prompt, user_payload, schema_hint) -> dict

# Implementations:
# - MockAIProvider  (rule-based, offline, reproducible for hackathon)
# - OpenAIProvider  (production, set AI_PROVIDER=openai + AI_API_KEY)
```

All agent outputs are stored in `AIAnalysis` table with `analysis_type`, `prompt_version`, `input_data`, `output_data`, `confidence`.

---

## Baseline Comparison

The **baseline** (`backend/baseline/simple_triage.py`) represents pre-agent triage:
- Single-pass keyword matching
- Always creates a ticket
- No validation or duplicate detection
- Flat P3 severity (except "critical" keyword)
- Round-robin assignment

Run comparison: `python -m evaluation.run_eval`

---

## File Map

```
backend/
├── app/ai/
│   ├── service.py              # Orchestrator + agents
│   └── prompts/                # Versioned agent prompts
├── app/assignment/engine.py    # Assignment agent
├── baseline/simple_triage.py   # Hackathon baseline
└── evaluation/
    ├── test_cases.json         # 12 evaluation cases
    ├── run_eval.py             # Baseline vs agent runner
    └── results.json            # Latest measured results
```

See also: [AGENT_TRAJECTORIES.md](AGENT_TRAJECTORIES.md) for step-by-step execution traces.
