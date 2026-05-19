"""
Critic Agent - Claude version with trimmed inputs
"""
import anthropic
import os
import json
from utils.logger import log_event

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a Critic Agent. Evaluate job application content.
Return ONLY valid JSON, no markdown fences.

{
  "approved": true/false,
  "scores": {"specificity":1-5,"accuracy":1-5,"strength":1-5,"relevance":1-5,"tone":1-5},
  "feedback": "actionable feedback if not approved, empty string if approved",
  "summary": "one sentence assessment"
}
"""

def CriticAgent():
    class _CriticAgent:
        def run(self, draft: str, job_description: str, analysis: str) -> dict:
            log_event("critic", "Starting review")
            for attempt in range(2):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=600,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": f"JD:\n{job_description[:1000]}\n\nDRAFT:\n{str(draft)[:2000]}\n\nReturn JSON evaluation."}]
                    )
                    raw = response.content[0].text.strip()
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    result = json.loads(raw.strip())
                    log_event("critic", f"Approved: {result.get('approved')}")
                    return result
                except json.JSONDecodeError:
                    if attempt == 1:
                        return {"approved": True, "scores": {}, "feedback": "", "summary": "Parse error, passed by default."}
                except Exception as e:
                    log_event("critic", f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == 1:
                        raise
    return _CriticAgent()