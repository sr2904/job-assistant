"""
Interview Prep Agent - Claude version
"""
import anthropic
import os
from utils.logger import log_event

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are an Interview Prep Agent. Generate likely interview questions 
and answer frameworks for a specific job application.

Output format:
## LIKELY TECHNICAL QUESTIONS
[3-4 technical questions with brief answer frameworks]

## LIKELY BEHAVIORAL QUESTIONS
[3-4 behavioral questions with STAR framework hints]

## QUESTIONS TO ASK THEM
[3 smart questions the candidate should ask]
"""

def InterviewPrepAgent():
    class _InterviewPrepAgent:
        def run(self, job_description: str, user_background: str, analysis: str) -> str:
            log_event("interview_prep", "Generating interview prep")
            for attempt in range(2):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": f"JD:\n{job_description[:2500]}\n\nBACKGROUND:\n{user_background[:1500]}\n\nANALYSIS:\n{str(analysis)[:1000]}\n\nGenerate interview prep."}]
                    )
                    result = response.content[0].text
                    log_event("interview_prep", "Done")
                    return result
                except Exception as e:
                    log_event("interview_prep", f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == 1:
                        return "Interview prep unavailable."
    return _InterviewPrepAgent()