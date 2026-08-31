# AI-Enabled IT Helpdesk System

A full-stack **agentic IT helpdesk** built for the [micro1 Agentic Workflows Hackathon](https://micro1.ai). Employees report IT issues; a multi-agent workflow analyzes, validates, routes, and assigns tickets — with human-in-the-loop controls.

## Hackathon: Problem & Solution

| Question | Answer |
|----------|--------|
| **Who?** | Employees, IT support engineers, IT managers |
| **Bottleneck?** | Manual L1 triage — categorization, spam filtering, duplicates, assignment |
| **Agent solution?** | 6 specialized agents orchestrated with structured JSON + audit trail |
| **Measured improvement?** | **+47pt** triage score vs baseline (48.8% → 95.8%), 0 false positives |
| **Reproducible?** | `python -m evaluation.run_eval` — see [REPRODUCTION.md](REPRODUCTION.md) |

### Submission Documents

| Document | Purpose |
|----------|---------|
| [IMPROVEMENT_CHANGELOG.md](IMPROVEMENT_CHANGELOG.md) | Iteration story + evidence |
| [REPRODUCTION.md](REPRODUCTION.md) | Judge reproduction guide |
| [docs/AGENT_ARCHITECTURE.md](docs/AGENT_ARCHITECTURE.md) | Agent design & orchestration |
| [docs/AGENT_TRAJECTORIES.md](docs/AGENT_TRAJECTORIES.md) | Step-by-step agent traces |

## Features

- Role-based authentication (User, IT Support, IT Manager)
- AI-first issue analysis, validation, categorization, and severity classification
- Intelligent ticket assignment based on expertise and workload
- In-app notifications
- Ticket lifecycle management with audit logging
- Knowledge base, search, manager dashboards, and override controls
- Mock AI provider (works offline) with optional OpenAI integration

## Demo Accounts

| Role | Name | Email | Password |
|------|------|-------|----------|
| User | Rahul Sharma | rahul@demo.com | Demo@123 |
| IT Support | Amit Patel | amit@demo.com | Demo@123 |
| IT Support | Priya Mehta | priya@demo.com | Demo@123 |
| IT Support | Raj Shah | raj@demo.com | Demo@123 |
| IT Manager | Neha Shah | neha@demo.com | Demo@123 |

## Quick Start

### Backend

**Requires Python 3.11+** (Python 3.14 supported with `pydantic>=2.13.0`)

```bash
cd ai-helpdesk/backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy ..\.env.example .env    # optional
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd ai-helpdesk/frontend
npm install
npm run dev
```

App: http://localhost:5173

## Demo Flow

1. Login as **rahul@demo.com**
2. Click **Report an IT Problem**
3. Submit: *"I cannot connect to the company VPN..."*
4. AI analyzes, suggests troubleshooting, validates, creates ticket
5. Login as **amit@demo.com** — see assigned notification and ticket
6. Update status: IN_PROGRESS → RESOLVED
7. Login as Rahul — confirm and close ticket
8. Login as **neha@demo.com** — view manager dashboard and audit logs

## Project Structure

```
ai-helpdesk/
├── backend/          # FastAPI, SQLAlchemy, AI services
├── frontend/         # React + Vite
├── .env.example
└── README.md
```

## Configuration

See `.env.example` for:

- `AI_PROVIDER=mock|openai`
- `AI_API_KEY` (for OpenAI)
- Thresholds, CORS, database URL

## Evaluation (Hackathon)

```bash
cd backend
python -m evaluation.run_eval
```

Compares **baseline** (keyword + round-robin) vs **agent workflow** on 12 test cases. Results written to `evaluation/results.json`.

## Tests

```bash
cd backend
pytest tests/ -v
```

## Architecture

```
Frontend → REST API → Agent Orchestrator → Assignment Engine → Database
                           ├── Analysis Agent
                           ├── Validation Agent
                           ├── Duplicate Agent
                           ├── Classification Agent
                           └── Severity Agent
                                    ↓
                          Notifications / Audit Logs
```

See [docs/AGENT_ARCHITECTURE.md](docs/AGENT_ARCHITECTURE.md) for full agent definitions.
