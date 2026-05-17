# AI Job Application Assistant
### Multi-Agent System — Wipro Junior FDE Assignment

A multi-agent AI system that collaboratively helps users produce tailored job applications.

---

## Architecture

```
User Input
    │
    ▼
[Guardrails] — Input validation, prompt injection protection
    │
    ▼
[Orchestrator] — Shared memory, sequential coordination
    │
    ├──▶ [Researcher Agent] — Web search: company info, role context, news
    │
    ├──▶ [Analyst Agent]   — Fit analysis: strengths, gaps, talking points
    │
    ├──▶ [Writer Agent]    — Draft: cover letter + resume bullets
    │
    └──▶ [Critic Agent]   — Evaluate draft (1-5 per criterion)
              │
              └── If rejected → Writer revises (max 2 loops)
```

---

## Local Setup

```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set your Gemini API key
export GEMINI_API_KEY=your_key_here

# 3. Run
streamlit run app.py
```

---

## GCP Cloud Run Deployment

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Build and push
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/job-assistant

# 3. Deploy
gcloud run deploy job-assistant \
  --image gcr.io/YOUR_PROJECT_ID/job-assistant \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your_key_here
```

---

## Tech Stack
- **LLM:** Gemini 2.0 Flash (Google AI)
- **UI:** Streamlit
- **Hosting:** GCP Cloud Run
- **Orchestration:** Custom Python (no LangChain)
