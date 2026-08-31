# Agent Trajectories

Representative execution traces from the agentic workflow. Each trace shows agent instructions → structured output → orchestrator decision.

---

## Trajectory 1: Genuine VPN Issue (Ticket Created)

**Input:**
```json
{
  "title": "VPN is not connecting",
  "description": "I cannot connect to the company VPN. I have tried restarting the VPN client and my laptop but it still doesn't connect."
}
```

| Step | Agent | Output | Orchestrator Decision |
|------|-------|--------|----------------------|
| 1 | **Analysis** | `category: VPN`, `confidence: 0.92`, 5 troubleshooting steps | Continue |
| 2 | **Validation** | `is_genuine: true`, `requires_it_intervention: true`, `confidence: 0.94` | Continue |
| 3 | **Duplicate** | `is_duplicate: false` | Continue |
| 4 | **Classification** | `category: VPN`, `subcategory: VPN Connectivity` | — |
| 5 | **Severity** | `severity: P2`, `priority: HIGH` | — |
| 6 | **Assignment** | Score: Amit 70 vs Raj 85 → **Raj Shah** (lower workload + VPN expertise) | Notify Raj |

**Final result:** Ticket `INC-0000XX` created, P2, assigned to VPN specialist, user sees troubleshooting steps immediately.

**Human checkpoint:** IT engineer investigates; user confirms closure.

---

## Trajectory 2: Invalid Request (Suppressed)

**Input:**
```json
{
  "title": "Hello",
  "description": "Hello"
}
```

| Step | Agent | Output | Orchestrator Decision |
|------|-------|--------|----------------------|
| 1 | **Analysis** | `requires_it_intervention: false`, `confidence: 0.2` | Continue to validation |
| 2 | **Validation** | `is_genuine: false`, `reason: "Insufficient information..."` | **SUPPRESS (INVALID)** |
| 3 | Duplicate | *(skipped)* | — |
| 4 | Classification | *(skipped)* | — |

**Final result:** No ticket created. User receives explanation to provide more details.

**Baseline comparison:** Baseline would create a ticket with category `Other`, severity P3, assigned round-robin — **false positive**.

---

## Trajectory 3: Duplicate VPN Issue (Linked, No New Ticket)

**Input:**
```json
{
  "title": "VPN is not working",
  "description": "VPN is not working for me. Connection keeps failing when I try to connect."
}
```

**Context:** Open ticket `INC-1001` — "VPN not working, connection keeps failing..."

| Step | Agent | Output | Orchestrator Decision |
|------|-------|--------|----------------------|
| 1 | **Analysis** | VPN category, troubleshooting steps | Continue |
| 2 | **Validation** | `is_genuine: true` | Continue |
| 3 | **Duplicate** | `is_duplicate: true`, `similar_ticket_id: INC-1001`, `confidence: 0.91` | **SUPPRESS (DUPLICATE)** |

**Final result:** User told existing ticket INC-1001 is handling the issue. No redundant ticket.

**Baseline comparison:** Baseline creates duplicate ticket — **false positive**.

---

## Trajectory 4: P1 Production Outage (Escalation)

**Input:**
```json
{
  "title": "Production application down",
  "description": "Production application is completely unavailable for the entire company. All employees affected."
}
```

| Step | Agent | Output | Orchestrator Decision |
|------|-------|--------|----------------------|
| 1 | **Analysis** | Application category, high impact | Continue |
| 2 | **Validation** | `is_genuine: true` | Continue |
| 3 | **Duplicate** | `is_duplicate: false` | Continue |
| 4 | **Severity** | `P1`, `CRITICAL`, org-wide impact | Create + escalate |
| 5 | **Assignment** | Best available engineer | Notify engineer + **IT Manager alert** |

**Final result:** P1 ticket created, status ESCALATED, manager notified.

**Safety rule applied:** P1 never suppressed regardless of AI confidence.

---

## Trajectory 5: Self-Service Password (Suppressed)

**Input:**
```json
{
  "title": "How do I reset password",
  "description": "How do I reset my password? I forgot it."
}
```

| Step | Agent | Output | Orchestrator Decision |
|------|-------|--------|----------------------|
| 1 | **Analysis** | Password category detected | Continue |
| 2 | **Validation** | `is_genuine: false`, self-service KB available | **SUPPRESS (SELF_SERVICE)** |

**Final result:** User directed to self-service instructions. No IT ticket.

---

## Retry / Fallback Behavior

When the LLM provider is unavailable (`OpenAIProvider` timeout/error):

```
AI unavailable
    ↓
Create ticket with "AI analysis unavailable"
    ↓
Default severity P3, category Other
    ↓
Route to default IT queue
    ↓
Human review required
```

The orchestrator never fabricates AI decisions silently — `ai_validation_result: AI_UNAVAILABLE` is persisted.

---

## How to Capture Live Trajectories

1. Submit an issue via UI or `POST /api/issues/create`
2. Query `ai_analyses` table for the ticket/request
3. Each row shows `analysis_type`, `input_data`, `output_data`, `prompt_version`

Example SQL:
```sql
SELECT analysis_type, output_data, confidence, created_at
FROM ai_analyses
WHERE ticket_id = <id>
ORDER BY created_at;
```

Or run evaluation with verbose output:
```bash
cd backend
python -m evaluation.run_eval --json
```
