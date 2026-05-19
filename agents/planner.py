"""
Planner Agent - Claude version
"""
import anthropic
import os
from utils.logger import log_event

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a Planner Agent. You are the first agent in a multi-agent job application system.
Your job is to read the job description and candidate background, then produce a clear strategy 
that all other agents (Researcher, Analyst, Writer, Critic) will follow.

Rules:
- Be specific and actionable.
- Identify the 3 most important requirements from the JD.
- Identify the candidate's 2 strongest selling points.
- Flag any significant gaps the Writer must handle carefully.
- Never write application content yourself.

Output format:
## PLAN SUMMARY
One sentence describing the overall strategy.

## TOP 3 JD REQUIREMENTS TO ADDRESS
1. [requirement]
2. [requirement]
3. [requirement]

## CANDIDATE'S TOP 2 SELLING POINTS
1. [selling point]
2. [selling point]

## GAPS TO HANDLE CAREFULLY
[List any significant mismatches]

## TONE AND ANGLE
[One sentence on tone and angle for the Writer]
"""

def PlannerAgent():
    class _PlannerAgent:
        def run(self, job_description: str, user_background: str) -> str:
            log_event("planner", "Creating strategy")
            for attempt in range(2):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system=SYSTEM_PROMPT,
                        messages=[{"role": "user", "content": f"JOB DESCRIPTION:\n{job_description[:3000]}\n\nCANDIDATE BACKGROUND:\n{user_background[:2000]}\n\nProduce your structured plan."}]
                    )
                    result = response.content[0].text
                    log_event("planner", "Plan created")
                    return result
                except Exception as e:
                    log_event("planner", f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == 1:
                        raise
    return _PlannerAgent()