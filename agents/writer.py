"""
Writer Agent - Claude version with trimmed inputs
"""
import anthropic
import os
from utils.logger import log_event

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a Writer Agent. Write tailored job application content.

Output format:
## COVER LETTER
[Full cover letter, 3-4 paragraphs]

## RESUME BULLETS
[5-6 tailored bullet points with strong action verbs]
"""

def WriterAgent():
    class _WriterAgent:
        def run(self, job_description: str, user_background: str,
                research: str, analysis: str, plan: str = "",
                critique_feedback: str = None) -> str:
            log_event("writer", f"Starting {'revision' if critique_feedback else 'initial draft'}")
            revision = f"\nCRITIQUE TO ADDRESS:\n{critique_feedback}\n" if critique_feedback else ""
            for attempt in range(2):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1500,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": f"PLAN:\n{str(plan)[:500]}\n\nJD:\n{job_description[:1500]}\n\nCANDIDATE:\n{user_background[:1500]}\n\nANALYSIS:\n{str(analysis)[:800]}\n{revision}\nWrite cover letter and bullets."}]
                    )
                    result = response.content[0].text
                    log_event("writer", "Draft complete")
                    return result
                except Exception as e:
                    log_event("writer", f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == 1:
                        raise
    return _WriterAgent()