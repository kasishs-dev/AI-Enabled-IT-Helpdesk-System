import json
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional
import httpx
from app.config import get_settings

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


class AIProvider(ABC):
    @abstractmethod
    async def complete_json(self, system_prompt: str, user_payload: dict, schema_hint: str) -> dict[str, Any]:
        ...


class MockAIProvider(AIProvider):
    """Rule-based AI for demo without external API keys."""

    VPN_KEYWORDS = ["vpn", "remote access", "connect to company"]
    WIFI_KEYWORDS = ["wifi", "wi-fi", "wireless"]
    HARDWARE_KEYWORDS = ["laptop", "screen", "flicker", "keyboard", "hardware", "monitor"]
    EMAIL_KEYWORDS = ["email", "outlook", "mailbox"]
    PASSWORD_KEYWORDS = ["password", "reset password", "locked out", "account"]
    PRODUCTION_KEYWORDS = ["production", "company-wide", "entire company", "all employees", "outage"]
    SECURITY_KEYWORDS = ["security", "breach", "ransomware", "phishing"]

    async def complete_json(self, system_prompt: str, user_payload: dict, schema_hint: str) -> dict[str, Any]:
        text = _normalize(user_payload.get("description", "") + " " + user_payload.get("title", ""))

        if "validation" in schema_hint:
            return self._validate(text, user_payload)
        if "duplicate" in schema_hint:
            return self._duplicate(text, user_payload)
        if "severity" in schema_hint:
            return self._severity(text, user_payload)
        if "categor" in schema_hint:
            return self._categorize(text)
        if "troubleshoot" in schema_hint or "suggestion" in schema_hint:
            return self._suggestions(text)
        return self._analyze(text)

    def _is_invalid(self, text: str) -> bool:
        t = text.strip()
        if len(t) < 10:
            return True
        words = [w for w in t.split() if w.isalpha()]
        if not words:
            return True
        trivial = {"hello", "hi", "test", "help", "hey", "thanks", "ok", "please"}
        if all(w in trivial for w in words) and len(words) <= 4:
            return True
        if set(words) <= {"need", "help", "please", "me", "hi", "hello"}:
            return True
        return t.lower() in trivial

    def _detect_category(self, text: str) -> tuple[str, str]:
        if any(k in text for k in self.VPN_KEYWORDS):
            return "VPN", "VPN Connectivity"
        if any(k in text for k in self.WIFI_KEYWORDS):
            return "WiFi", "Wireless Connectivity"
        if any(k in text for k in self.HARDWARE_KEYWORDS):
            return "Hardware", "Laptop/Hardware Issue"
        if any(k in text for k in self.EMAIL_KEYWORDS):
            return "Email", "Email Access"
        if any(k in text for k in self.PASSWORD_KEYWORDS):
            return "Password / Account", "Account Access"
        if any(k in text for k in self.SECURITY_KEYWORDS):
            return "Security", "Security Incident"
        if "printer" in text:
            return "Printer", "Printing Issue"
        if "software" in text or "application" in text or "install" in text:
            return "Application", "Software Installation"
        return "Other", "General IT Issue"

    def _analyze(self, text: str) -> dict[str, Any]:
        if self._is_invalid(text):
            return {
                "problem_summary": "Insufficient information provided.",
                "possible_category": "Other",
                "initial_suggestions": ["Please provide more details about your IT issue."],
                "requires_it_intervention": False,
                "confidence": 0.2,
            }
        category, _ = self._detect_category(text)
        suggestions = self._suggestions(text)["suggestions"]
        return {
            "problem_summary": text[:200],
            "possible_category": category,
            "initial_suggestions": suggestions,
            "requires_it_intervention": True,
            "confidence": 0.92,
        }

    def _suggestions(self, text: str) -> dict[str, Any]:
        category, _ = self._detect_category(text)
        kb = {
            "VPN": [
                "Check whether your internet connection is working.",
                "Restart the VPN client.",
                "Verify that your VPN credentials are correct.",
                "Restart your laptop.",
                "Try connecting again.",
            ],
            "WiFi": [
                "Toggle WiFi off and on.",
                "Forget and reconnect to the corporate network.",
                "Move closer to the access point.",
                "Restart your device.",
            ],
            "Hardware": [
                "Check cable connections.",
                "Update display drivers.",
                "Connect an external monitor to isolate the issue.",
                "Note when flickering occurs for IT review.",
            ],
            "Email": [
                "Verify internet connectivity.",
                "Restart Outlook.",
                "Check webmail access.",
                "Clear cached credentials if prompted.",
            ],
        }
        suggestions = kb.get(category, [
            "Document exact error messages.",
            "Note when the issue started.",
            "Try restarting the affected application.",
            "Contact IT if the issue persists.",
        ])
        return {"suggestions": suggestions, "summary": f"We understand you're having a {category.lower()} related issue."}

    def _validate(self, text: str, payload: dict) -> dict[str, Any]:
        if self._is_invalid(text):
            return {
                "is_genuine": False,
                "confidence": 0.95,
                "reason": "The request does not contain enough information to identify an IT issue. Please provide a clear title and description.",
                "requires_it_intervention": False,
                "duplicate_ticket": False,
            }
        if "password reset" in text or ("reset" in text and "password" in text and "how" in text):
            return {
                "is_genuine": False,
                "confidence": 0.88,
                "reason": "This issue can likely be resolved using self-service password reset instructions.",
                "requires_it_intervention": False,
                "duplicate_ticket": False,
            }
        return {
            "is_genuine": True,
            "confidence": 0.94,
            "reason": "The user reports a specific IT issue with enough detail for investigation.",
            "requires_it_intervention": True,
            "duplicate_ticket": False,
        }

    def _categorize(self, text: str) -> dict[str, Any]:
        category, subcategory = self._detect_category(text)
        return {"category": category, "subcategory": subcategory, "confidence": 0.97}

    def _severity(self, text: str, payload: dict) -> dict[str, Any]:
        if any(k in text for k in self.PRODUCTION_KEYWORDS):
            return {
                "severity": "P1",
                "priority": "CRITICAL",
                "impact": "Organization-wide",
                "urgency": "Critical",
                "affected_users": 500,
                "business_impact": "Critical production system unavailable for the organization.",
                "reasoning": "Company-wide production outage requires immediate IT response.",
            }
        if any(k in text for k in self.VPN_KEYWORDS):
            return {
                "severity": "P2",
                "priority": "HIGH",
                "impact": "Single user",
                "urgency": "High",
                "affected_users": 1,
                "business_impact": "User cannot access required corporate VPN.",
                "reasoning": "VPN failure prevents remote access to internal systems.",
            }
        if any(k in text for k in self.HARDWARE_KEYWORDS):
            return {
                "severity": "P3",
                "priority": "MEDIUM",
                "impact": "Single user",
                "urgency": "Medium",
                "affected_users": 1,
                "business_impact": "Hardware issue affecting user productivity.",
                "reasoning": "Single-user hardware issue with workaround potential.",
            }
        if any(k in text for k in self.SECURITY_KEYWORDS):
            return {
                "severity": "P1",
                "priority": "CRITICAL",
                "impact": "Organization",
                "urgency": "Critical",
                "affected_users": 100,
                "business_impact": "Potential security incident.",
                "reasoning": "Security issues require immediate escalation.",
            }
        return {
            "severity": "P4",
            "priority": "LOW",
            "impact": "Single user",
            "urgency": "Low",
            "affected_users": 1,
            "business_impact": "Minor IT issue.",
            "reasoning": "Low business impact general request.",
        }

    def _duplicate(self, text: str, payload: dict) -> dict[str, Any]:
        existing = payload.get("existing_tickets", [])
        single_user = any(p in text for p in ["i cannot", "my laptop", "i am unable", "i have tried", "since this morning"])
        for ticket in existing:
            existing_text = _normalize(ticket.get("title", "") + " " + ticket.get("description", ""))
            org_wide = any(p in existing_text for p in ["multiple users", "employees", "company-wide", "entire company"])
            if single_user and org_wide:
                continue
            if "vpn" in text and "vpn" in existing_text and not (single_user and org_wide):
                return {"is_duplicate": True, "similar_ticket_id": ticket.get("ticket_number"), "confidence": 0.91}
            overlap = set(text.split()) & set(existing_text.split())
            if len(overlap) >= 5 and len(text) > 30:
                return {"is_duplicate": True, "similar_ticket_id": ticket.get("ticket_number"), "confidence": 0.85}
        return {"is_duplicate": False, "similar_ticket_id": None, "confidence": 0.1}


class OpenAIProvider(AIProvider):
    async def complete_json(self, system_prompt: str, user_payload: dict, schema_hint: str) -> dict[str, Any]:
        settings = get_settings()
        if not settings.ai_api_key:
            raise RuntimeError("AI API key not configured")
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.ai_api_key}"},
                json={
                    "model": settings.ai_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": json.dumps(user_payload)},
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)


def get_ai_provider() -> AIProvider:
    settings = get_settings()
    if settings.ai_provider.lower() == "openai" and settings.ai_api_key:
        return OpenAIProvider()
    return MockAIProvider()


class AIHelpdeskService:
    PROMPT_VERSION = "v1"

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or get_ai_provider()
        self.available = True

    async def _safe_call(self, prompt_file: str, payload: dict, schema_hint: str) -> tuple[dict[str, Any], bool]:
        try:
            prompt = load_prompt(prompt_file)
            result = await self.provider.complete_json(prompt, payload, schema_hint)
            return result, True
        except Exception:
            return {"error": "AI unavailable", "fallback": True}, False

    async def analyze_issue(self, issue: dict) -> dict[str, Any]:
        return (await self._safe_call("issue_analysis_v1.txt", issue, "analysis"))[0]

    async def generate_suggestions(self, issue: dict) -> dict[str, Any]:
        return (await self._safe_call("troubleshooting_v1.txt", issue, "suggestions"))[0]

    async def validate_issue(self, issue: dict) -> dict[str, Any]:
        return (await self._safe_call("validation_v1.txt", issue, "validation"))[0]

    async def categorize_issue(self, issue: dict) -> dict[str, Any]:
        return (await self._safe_call("categorization_v1.txt", issue, "categorization"))[0]

    async def determine_severity(self, issue: dict) -> dict[str, Any]:
        return (await self._safe_call("severity_v1.txt", issue, "severity"))[0]

    async def detect_duplicate(self, issue: dict) -> dict[str, Any]:
        return (await self._safe_call("duplicate_detection_v1.txt", issue, "duplicate"))[0]

    async def process_issue(self, issue: dict, settings_thresholds: dict) -> dict[str, Any]:
        analysis = await self.analyze_issue(issue)
        suggestions_data = await self.generate_suggestions(issue)
        suggestions = suggestions_data.get("suggestions") or analysis.get("initial_suggestions", [])
        validation = await self.validate_issue(issue)
        duplicate = await self.detect_duplicate(issue)

        ai_available = not validation.get("fallback") and not analysis.get("fallback")

        if ai_available and duplicate.get("is_duplicate") and duplicate.get("confidence", 0) >= settings_thresholds["duplicate"]:
            return {
                "ai_available": True,
                "analysis": analysis,
                "suggestions": suggestions,
                "validation": validation,
                "duplicate": duplicate,
                "categorization": None,
                "severity": None,
                "create_ticket": False,
                "suppression_outcome": "DUPLICATE",
                "message": f"A similar issue is already being handled. Existing Ticket: {duplicate.get('similar_ticket_id')}",
            }

        if ai_available:
            is_genuine = validation.get("is_genuine", False)
            requires_it = validation.get("requires_it_intervention", False)
            confidence = validation.get("confidence", 0)
            if not is_genuine or (not requires_it and confidence >= settings_thresholds["validation"]):
                outcome = "INVALID" if not is_genuine else "SELF_SERVICE"
                return {
                    "ai_available": True,
                    "analysis": analysis,
                    "suggestions": suggestions,
                    "validation": validation,
                    "duplicate": duplicate,
                    "categorization": None,
                    "severity": None,
                    "create_ticket": False,
                    "suppression_outcome": outcome,
                    "message": validation.get("reason", "Request does not require IT intervention."),
                }

        categorization = await self.categorize_issue(issue)
        severity = await self.determine_severity(issue)

        if not ai_available:
            return {
                "ai_available": False,
                "analysis": {"problem_summary": "AI analysis unavailable", "confidence": 0},
                "suggestions": suggestions,
                "validation": {"is_genuine": True, "reason": "Routed for human review"},
                "duplicate": duplicate,
                "categorization": categorization if not categorization.get("fallback") else {"category": "Other", "subcategory": "General", "confidence": 0},
                "severity": severity if not severity.get("fallback") else {"severity": "P3", "priority": "MEDIUM", "reasoning": "Default severity pending review"},
                "create_ticket": True,
                "suppression_outcome": None,
                "message": "AI unavailable. Ticket created for human review.",
            }

        return {
            "ai_available": True,
            "analysis": analysis,
            "suggestions": suggestions,
            "validation": validation,
            "duplicate": duplicate,
            "categorization": categorization,
            "severity": severity,
            "create_ticket": True,
            "suppression_outcome": None,
            "message": "Issue validated. Creating ticket.",
        }
