"""
Analyst Agent - Claude version with trimmed inputs
"""
import anthropic
import os
from utils.logger import log_event

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an Analyst Agent. Analyze fit between candidate and job description.

Output format:
1. Key Strengths (bullet list)
2. Potential Gaps (bullet list)
3. Key Talking Points (3-4 angles)
4. Fit Score (1-10 with justification)
"""

def AnalystAgent():
    class _AnalystAgent:
        def run(self, job_description: str, user_background: str, research: str, plan: str = "") -> str:
            log_event("analyst", "Starting analysis")
            for attempt in range(2):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": f"PLAN:\n{str(plan)[:500]}\n\nJD:\n{job_description[:1500]}\n\nCANDIDATE:\n{user_background[:1500]}\n\nRESEARCH SUMMARY:\n{str(research)[:500]}\n\nAnalyze fit."}]
                    )
                    result = response.content[0].text
                    log_event("analyst", "Analysis complete")
                    return result
                except Exception as e:
                    log_event("analyst", f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == 1:
                        raise
    return _AnalystAgent()