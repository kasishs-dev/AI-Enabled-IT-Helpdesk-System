# Reproduction Guide — AI Helpdesk Hackathon Submission

This guide lets a judge reproduce the **application**, **baseline**, **agent evaluation**, and **demo flow** from a clean environment.

---

## Requirements

| Tool | Version tested |
|------|----------------|
| Python | 3.11+ (3.14.7 tested) |
| Node.js | 18+ (22.x tested) |
| npm | 9+ |
| OS | Windows / macOS / Linux |

**Cost:** $0 with mock AI (default). Optional OpenAI: ~$0.01/issue.

**Runtime:**
- Backend setup: ~2 min
- Frontend setup: ~1 min
- Evaluation script: ~5 sec
- Full demo flow: ~5 min

---

## 1. Clone & Environment

```bash
cd ai-helpdesk
copy .env.example backend\.env     # Windows
# cp .env.example backend/.env     # macOS/Linux
```

Default `.env` uses `AI_PROVIDER=mock` — no API keys required.

---

## 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
pip install -r requirements.txt

# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
```

Start API:
```bash
uvicorn app.main:app --reload --port 8000
```

Verify: http://localhost:8000/api/health → `{"status":"ok"}`

---

## 3. Frontend Setup

New terminal:

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## 4. Run Baseline vs Agent Evaluation

From `backend/` with venv activated:

```bash
# Full comparison (baseline + agent, writes results.json)
python -m evaluation.run_eval

# JSON output only
python -m evaluation.run_eval --json

# Baseline only
python -m baseline.simple_triage

# Agent only
python -m evaluation.run_eval --agent-only
```

### Expected Output (approximate)

```
BASELINE:  Mean triage score ~48.8%  |  False positives: 4
AGENT:     Mean triage score ~95.8%  |  False positives: 0
IMPROVEMENT: +47.0 points
```

Full results: `backend/evaluation/results.json`

---

## 5. Run Unit & Integration Tests

```bash
cd backend
pytest tests/ -v
```

Expected: **9 passed**

---

## 6. Demo Flow (End-to-End)

### Accounts (password: `Demo@123`)

| Role | Email |
|------|-------|
| Employee | rahul@demo.com |
| IT Support | amit@demo.com |
| IT Manager | neha@demo.com |

### Steps

1. Login as **rahul@demo.com**
2. **Report Problem** → submit VPN issue:
   > I cannot connect to the company VPN. I have tried restarting the VPN client and my laptop but it still doesn't connect.
3. Observe AI processing steps → ticket created (e.g. INC-000019)
4. Login as **amit@demo.com** → notification + assigned ticket
5. Open ticket → **Start Work** → **Mark Resolved**
6. Login as **rahul** → **Yes — Close Ticket**
7. Login as **neha@demo.com** → manager dashboard + audit logs

### Suppression demo

Login as Rahul → submit title/description: `Hello` / `Hello`  
Expected: No ticket created, validation explanation shown.

---

## 7. API Documentation

With backend running: http://localhost:8000/docs

Key endpoints:
- `POST /api/auth/login`
- `POST /api/issues/create`
- `GET /api/tickets`
- `GET /api/dashboard/manager`

---

## 8. Docker Alternative

```bash
cd docker
docker compose up --build
```

Frontend: http://localhost:5173  
Backend: http://localhost:8000

---

## 9. Optional: OpenAI Provider

Edit `backend/.env`:
```env
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
AI_API_KEY=sk-...
```

Re-run evaluation — same test cases, LLM-backed agents.

---

## 10. Submission Checklist for Judges

- [ ] `python -m evaluation.run_eval` shows +47pt improvement
- [ ] `pytest tests/ -v` passes
- [ ] Demo flow completes without manual DB edits
- [ ] `docs/AGENT_ARCHITECTURE.md` explains agent design
- [ ] `docs/AGENT_TRAJECTORIES.md` shows 5 execution traces
- [ ] `IMPROVEMENT_CHANGELOG.md` documents iteration story

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `pydantic-core` build fails on Python 3.14 | Use `pydantic>=2.13.0` (already in requirements.txt) |
| CORS errors | Ensure frontend proxy in `vite.config.js` points to port 8000 |
| Empty database | Delete `backend/helpdesk.db` and restart — seed runs on startup |

---

## Data Used

All evaluation data is **synthetic** (see `evaluation/test_cases.json`). Demo users and tickets are seeded in `app/seed.py`. No private or production data required.
