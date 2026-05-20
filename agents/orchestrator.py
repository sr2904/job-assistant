"""
Orchestrator - Full 9-Agent Pipeline
Small delay after Researcher to avoid token rate limits
"""
import time
from agents.planner import PlannerAgent
from agents.researcher import ResearcherAgent
from agents.analyst import AnalystAgent
from agents.writer import WriterAgent
from agents.critic import CriticAgent
from agents.security import SecurityAgent
from agents.interview_prep import InterviewPrepAgent
from agents.email_draft import EmailDraftAgent
from agents.match_analyzer import MatchAnalyzerAgent
from utils.guardrails import validate_input
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

        # Step 1: Guardrails
        update("🔒 Validating inputs...")
        valid, reason = validate_input(job_description, user_background)
        if not valid:
            return {"error": reason}

        # Step 2: Planner
        update("🗺️ Planner: Decomposing task and creating strategy...")
        try:
            plan_raw = self.planner.run(job_description=job_description, user_background=user_background)
            shared_memory["plan"], sec_result = self._security_check("Planner", plan_raw, update)
            shared_memory["security_log"].append({"agent": "Planner", **sec_result})
        except Exception as e:
            shared_memory["plan"] = "No plan available."
            update("⚠️ Planner failed, continuing.")

        # Step 3: Researcher
        update("🔍 Researcher: Gathering company and role context...")
        try:
            research_raw = self.researcher.run(job_description=job_description)
            # Trim researcher output aggressively to avoid token limits downstream
            research_trimmed = research_raw[:1500] if research_raw else "Research unavailable."
            shared_memory["research"], sec_result = self._security_check("Researcher", research_trimmed, update)
            shared_memory["security_log"].append({"agent": "Researcher", **sec_result})
        except Exception as e:
            shared_memory["research"] = "Research unavailable."
            update("⚠️ Researcher failed, continuing.")

        # Small delay after researcher to let token rate limit reset
        update("🧠 Analyst: Analyzing your fit against the plan...")
        time.sleep(15)
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

        # Step 5: Match Analyzer
        update("📊 Match Analyzer: Breaking down requirement-by-requirement fit...")
        try:
            shared_memory["match_data"] = self.match_analyzer.run(
                job_description=job_description,
                user_background=user_background,
                analysis=shared_memory["analysis"]
            )
        except Exception as e:
            shared_memory["match_data"] = {}
            update("⚠️ Match analyzer failed.")

        # Step 6: Writer
        update("✍️ Writer: Drafting your cover letter and resume bullets...")
        try:
            draft_raw = self.writer.run(
                job_description=job_description,
                user_background=user_background,
                research=shared_memory["research"],
                analysis=shared_memory["analysis"],
                plan=shared_memory["plan"]
            )
            shared_memory["draft"], sec_result = self._security_check("Writer", draft_raw, update)
            shared_memory["security_log"].append({"agent": "Writer", **sec_result})
        except Exception as e:
            return {"error": "Writer agent failed. Please try again."}

        # Step 7: Critic loop
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
                    update(f"🔁 Critic requesting improvements...")
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

        # Step 8: Interview Prep
        update("🎯 Interview Prep: Generating likely questions...")
        try:
            shared_memory["interview_prep"] = self.interview_prep.run(
                job_description=job_description,
                user_background=user_background,
                analysis=shared_memory["analysis"]
            )
        except Exception as e:
            shared_memory["interview_prep"] = "Interview prep unavailable."

        # Step 9: Email Draft
        update("📧 Email Agent: Drafting your follow-up email...")
        try:
            shared_memory["email_draft"] = self.email_draft.run(
                job_description=job_description,
                user_background=user_background
            )
        except Exception as e:
            shared_memory["email_draft"] = "Email draft unavailable."

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