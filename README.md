# AI Job Application Assistant

A multi-agent system built for the Wipro Junior FDE pre-screening assignment. Paste a job description and your background — the system handles the rest.

**Live demo:** https://job-assistant-shashwat.streamlit.app
**Author:** Shashwat Rao Balaji — Arizona State University, CS '26

---

## What it does

You give it a job description and your resume. Nine specialized AI agents collaborate to produce:

- A tailored cover letter and resume bullets
- A breakdown of how well you match each requirement
- Likely interview questions with answer frameworks
- A follow-up email draft
- A full security audit of every agent's output

The whole thing runs in about 90 seconds.

---

## How it works

The system runs in five phases:

**Phase 1 (parallel):** The Planner reads the JD and your background and writes a strategy. The Researcher searches the web for company info. Both run at the same time.

**Phase 2 (sequential):** The Analyst compares your background to the JD, following the Planner's strategy. Produces strengths, gaps, talking points, and a fit score.

**Phase 3 (parallel):** The Match Analyzer scores you against each individual JD requirement. The Writer drafts the cover letter and bullets. Both run at the same time.

**Phase 4 (loop):** The Critic scores the draft on five criteria. If anything scores below 3/5, it sends feedback to the Writer and asks for a revision. This loop runs up to twice.

**Phase 5 (parallel):** Interview Prep generates questions specific to this JD and your background. The Email Agent drafts a follow-up. Both run at the same time.

After every single LLM call, a Security Agent scans the output before it passes forward.

---

## Security

Four things happen before any AI agent sees your data:

1. **Input validation** — length checks, 9 prompt injection patterns blocked via regex
2. **PII masking** — SSNs, credit cards, and emails replaced before any LLM call
3. **Role constraints** — every agent's system prompt defines exactly what it can and can't do
4. **Output scanning** — Security Agent checks every agent output for PII leakage, hallucinated facts, and policy violations

The API key lives only in environment variables. Never hardcoded.

---

## Stack

- Python 3.12
- Claude Sonnet (`claude-sonnet-4-20250514`) — Anthropic API
- Streamlit for the UI
- Custom Python orchestration (no LangChain)
- `ThreadPoolExecutor` for parallel agent execution
- pypdf for resume upload

---

## Running locally

```bash
git clone https://github.com/sr2904/job-assistant.git
cd job-assistant
pip3 install -r requirements.txt
pip3 install pypdf
export ANTHROPIC_API_KEY=your_key_here
streamlit run app.py
```

Opens at `http://localhost:8501`.

---

## Repo structure

```
agents/
  orchestrator.py     — runs the pipeline, coordinates all agents
  planner.py
  researcher.py
  analyst.py
  match_analyzer.py
  writer.py
  critic.py
  security.py
  interview_prep.py
  email_draft.py

utils/
  guardrails.py       — input validation and PII masking
  logger.py           — structured logging

tests/
  sample_inputs.py    — test cases including a prompt injection attempt

app.py                — Streamlit UI
Dockerfile            — for GCP Cloud Run deployment
```
