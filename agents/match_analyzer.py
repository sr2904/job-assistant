"""
Match Analyzer Agent - Claude version with trimmed inputs
"""
import anthropic
import os
import json
from utils.logger import log_event

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a Match Analyzer Agent. Produce a detailed breakdown of how 
a candidate matches each specific job requirement.

Return ONLY valid JSON, no markdown fences.

{
  "overall_score": 8,
  "overall_verdict": "Strong Match",
  "summary": "2-3 sentence overall summary",
  "requirements": [
    {
      "requirement": "Python programming",
      "match_level": "strong",
      "candidate_evidence": "Built FastAPI backend at internship",
      "score": 5
    }
  ],
  "top_strengths": ["strength 1", "strength 2", "strength 3"],
  "key_gaps": ["gap 1", "gap 2"],
  "recommendation": "Highlight X in interview"
}

match_level must be: strong, partial, weak, or missing
score must be 1-5
Extract 5-7 key requirements from the JD.
"""

def MatchAnalyzerAgent():
    class _MatchAnalyzerAgent:
        def run(self, job_description: str, user_background: str, analysis: str) -> dict:
            log_event("match_analyzer", "Analyzing matches")
            for attempt in range(2):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1500,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": f"JD:\n{job_description[:1500]}\n\nCANDIDATE:\n{user_background[:1500]}\n\nANALYSIS:\n{str(analysis)[:800]}\n\nReturn JSON match breakdown."}]
                    )
                    raw = response.content[0].text.strip()
                    if raw.startswith("```"):
                        raw = raw.split("```")[1]
                        if raw.startswith("json"):
                            raw = raw[4:]
                    result = json.loads(raw.strip())
                    log_event("match_analyzer", "Done")
                    return result
                except json.JSONDecodeError as e:
                    log_event("match_analyzer", f"JSON error: {str(e)}")
                    if attempt == 1:
                        return {"overall_score": 0, "error": "Parse error"}
                except Exception as e:
                    log_event("match_analyzer", f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == 1:
                        return {"overall_score": 0, "error": str(e)}
    return _MatchAnalyzerAgent()