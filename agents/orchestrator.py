"""
Orchestrator - Full 9-Agent Pipeline
Optimized with parallelism for faster execution
"""
from concurrent.futures import ThreadPoolExecutor
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.analyst import AnalystAgent
from agents.writer import WriterAgent
from agents.critic import CriticAgent
from agents.security import SecurityAgent
from agents.interview_prep import InterviewPrepAgent
from agents.email_draft import EmailDraftAgent
from agents.match_analyzer import MatchAnalyzerAgent
from utils.guardrails import validate_input, mask_pii
from utils.logger import log_event


class Orchestrator:
    def __init__(self):
        self.planner        = PlannerAgent()
        self.researcher     = ResearcherAgent()
        self.analyst        = AnalystAgent()
        self.writer         = WriterAgent()
        self.critic         = CriticAgent()
        self.security       = SecurityAgent()
        self.interview_prep = InterviewPrepAgent()
        self.email_draft    = EmailDraftAgent()
        self.match_analyzer = MatchAnalyzerAgent()
        self.MAX_CRITIQUE_LOOPS = 2

    def _security_check(self, agent_name: str, output: str, update) -> tuple:
        update(f"🛡️ Security Agent: Scanning {agent_name} output...")
        try:
            result = self.security.run(agent_name=agent_name, agent_output=output)
            if not result.get("safe"):
                issues = ", ".join(result.get("issues_found", []))
                update(f"⚠️ Security flagged {agent_name}: {issues}")
            else:
                update(f"✅ Security cleared {agent_name}")
            return result.get("sanitized_output", output), result
        except Exception as e:
            log_event("security", f"Security check failed: {str(e)}")
            return output, {"safe": True, "issues_found": [], "action_taken": "skipped"}

    def run(self, job_description: str, user_background: str, status_callback=None) -> dict:

        def update(msg):
            log_event("orchestrator", msg)
            if status_callback:
                status_callback(msg)

        shared_memory = {
            "job_description":  job_description,
            "user_background":  user_background,
            "plan":             None,
            "research":         None,
            "analysis":         None,
            "draft":            None,
            "final_output":     None,
            "match_data":       None,
            "interview_prep":   None,
            "email_draft":      None,
            "critique_history": [],
            "security_log":     [],
            "errors":           []
        }

        # ── Step 1: Guardrails ────────────────────────────────────────────────
        update("🔒 Validating inputs...")
        valid, reason = validate_input(job_description, user_background)
        if not valid:
            return {"error": reason}

        # Mask PII in user background before any LLM sees it
        user_background = mask_pii(user_background)

        # ── Step 2: PARALLEL — Planner + Researcher ───────────────────────────
        # These two agents don't depend on each other so they run simultaneously
        update("🗺️ Planner + 🔍 Researcher: Running in parallel...")
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                future_plan     = pool.submit(self.planner.run,
                                              job_description=job_description,
                                              user_background=user_background)
                future_research = pool.submit(self.researcher.run,
                                              job_description=job_description)
                plan_raw     = future_plan.result()
                research_raw = future_research.result()

            # Security scan Planner output
            shared_memory["plan"], sec_result = self._security_check("Planner", plan_raw, update)
            shared_memory["security_log"].append({"agent": "Planner", **sec_result})

            # Trim research output aggressively to avoid token limits downstream
            research_trimmed = research_raw[:1500] if research_raw else "Research unavailable."
            shared_memory["research"], sec_result = self._security_check("Researcher", research_trimmed, update)
            shared_memory["security_log"].append({"agent": "Researcher", **sec_result})

        except Exception as e:
            log_event("orchestrator", f"Parallel phase 1 error: {str(e)}")
            shared_memory["plan"]     = shared_memory["plan"] or "No plan available."
            shared_memory["research"] = shared_memory["research"] or "Research unavailable."
            update("⚠️ Planner/Researcher had issues, continuing.")

        # ── Step 3: SEQUENTIAL — Analyst ─────────────────────────────────────
        # Needs both plan and research, so must run after Step 2
        update("🧠 Analyst: Analyzing your fit against the plan...")
        try:
            analysis_raw = self.analyst.run(
                job_description=job_description,
                user_background=user_background,
                research=shared_memory["research"],
                plan=shared_memory["plan"]
            )
            shared_memory["analysis"], sec_result = self._security_check("Analyst", analysis_raw, update)
            shared_memory["security_log"].append({"agent": "Analyst", **sec_result})
        except Exception as e:
            return {"error": "Analyst agent failed. Please try again."}

        # ── Step 4: PARALLEL — Match Analyzer + Writer ────────────────────────
        # Both only need Analyst output — run simultaneously
        update("📊 Match Analyzer + ✍️ Writer: Running in parallel...")
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                future_match = pool.submit(self.match_analyzer.run,
                                           job_description=job_description,
                                           user_background=user_background,
                                           analysis=shared_memory["analysis"])
                future_draft = pool.submit(self.writer.run,
                                           job_description=job_description,
                                           user_background=user_background,
                                           research=shared_memory["research"],
                                           analysis=shared_memory["analysis"],
                                           plan=shared_memory["plan"])
                shared_memory["match_data"] = future_match.result()
                draft_raw = future_draft.result()

            shared_memory["draft"], sec_result = self._security_check("Writer", draft_raw, update)
            shared_memory["security_log"].append({"agent": "Writer", **sec_result})

        except Exception as e:
            log_event("orchestrator", f"Parallel phase 2 error: {str(e)}")
            if not shared_memory.get("draft"):
                return {"error": "Writer agent failed. Please try again."}
            shared_memory["match_data"] = shared_memory.get("match_data") or {}
            update("⚠️ Match Analyzer/Writer had issues.")

        # ── Step 5: SEQUENTIAL — Critic ↔ Writer loop ─────────────────────────
        for i in range(self.MAX_CRITIQUE_LOOPS):
            update(f"🔎 Critic: Reviewing draft (pass {i+1}/{self.MAX_CRITIQUE_LOOPS})...")
            try:
                critique_result = self.critic.run(
                    draft=shared_memory["draft"],
                    job_description=job_description,
                    analysis=shared_memory["analysis"]
                )
                shared_memory["critique_history"].append(critique_result)

                if critique_result["approved"]:
                    update("✅ Critic approved the output!")
                    break
                else:
                    update("🔁 Critic requesting improvements...")
                    draft_raw = self.writer.run(
                        job_description=job_description,
                        user_background=user_background,
                        research=shared_memory["research"],
                        analysis=shared_memory["analysis"],
                        plan=shared_memory["plan"],
                        critique_feedback=critique_result["feedback"]
                    )
                    shared_memory["draft"], sec_result = self._security_check("Writer(revision)", draft_raw, update)
                    shared_memory["security_log"].append({"agent": "Writer(revision)", **sec_result})
            except Exception as e:
                update("⚠️ Critic encountered an issue, using current draft.")
                break

        shared_memory["final_output"] = shared_memory["draft"]

        # ── Step 6: PARALLEL — Interview Prep + Email Agent ───────────────────
        # End-cap agents — neither depends on the other
        update("🎯 Interview Prep + 📧 Email Agent: Running in parallel...")
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                future_interview = pool.submit(self.interview_prep.run,
                                               job_description=job_description,
                                               user_background=user_background,
                                               analysis=shared_memory["analysis"])
                future_email     = pool.submit(self.email_draft.run,
                                               job_description=job_description,
                                               user_background=user_background)
                shared_memory["interview_prep"] = future_interview.result()
                shared_memory["email_draft"]    = future_email.result()
        except Exception as e:
            log_event("orchestrator", f"Parallel phase 3 error: {str(e)}")
            shared_memory["interview_prep"] = shared_memory.get("interview_prep") or "Interview prep unavailable."
            shared_memory["email_draft"]    = shared_memory.get("email_draft") or "Email draft unavailable."
            update("⚠️ Interview Prep/Email had issues.")

        update("🎉 Pipeline complete!")

        return {
            "plan":             shared_memory["plan"],
            "research":         shared_memory["research"],
            "analysis":         shared_memory["analysis"],
            "match_data":       shared_memory["match_data"],
            "final_output":     shared_memory["final_output"],
            "interview_prep":   shared_memory["interview_prep"],
            "email_draft":      shared_memory["email_draft"],
            "critique_history": shared_memory["critique_history"],
            "security_log":     shared_memory["security_log"],
        }