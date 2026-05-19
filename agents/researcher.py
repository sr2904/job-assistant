"""
Researcher Agent - Claude version
"""
import anthropic
import os
from utils.logger import log_event

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """You are a Researcher Agent. Your ONLY job is to gather factual information 
about a company and job role.

Rules:
- Only report facts. Do not invent information.
- Do not write cover letters or application content.
- Keep output structured and concise.

Output format:
1. Company Overview (2-3 sentences)
2. Role Context
3. Recent News or Signals
4. Culture/Values
"""

def ResearcherAgent():
    class _ResearcherAgent:
        def run(self, job_description: str) -> str:
            log_event("researcher", "Starting research")
            for attempt in range(2):
                try:
                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system=SYSTEM_PROMPT,
                        tools=[{"type": "web_search_20250305", "name": "web_search"}],
                        messages=[{"role": "user", "content": f"Research this company and role:\n{job_description[:3000]}"}]
                    )
                    result = ""
                    for block in response.content:
                        if hasattr(block, 'text'):
                            result += block.text
                    if result.strip():
                        log_event("researcher", "Research complete")
                        return result
                except Exception as e:
                    log_event("researcher", f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == 1:
                        return "Research unavailable."
    return _ResearcherAgent()