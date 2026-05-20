"""
Guardrails
----------
Input validation and prompt injection protection.
Applied by the Orchestrator before any agent receives user input.
"""

import re

INJECTION_PATTERNS = [
    r"ignore (previous|all|above) instructions",
    r"disregard (your|the) (system|previous) (prompt|instructions)",
    r"you are now",
    r"new persona",
    r"jailbreak",
    r"DAN mode",
    r"pretend you (have no|don't have) restrictions",
    r"forget (your|all) (instructions|rules|constraints)",
    r"override (your|all) (instructions|rules)",
]

MAX_JD_LENGTH = 15000
MAX_BACKGROUND_LENGTH = 5000
MIN_LENGTH = 50


def validate_input(job_description: str, user_background: str) -> tuple:
    """Returns (is_valid: bool, reason: str)"""

    if len(job_description.strip()) < MIN_LENGTH:
        return False, "Job description is too short. Please paste the full job posting."

    if len(user_background.strip()) < MIN_LENGTH:
        return False, "Background is too short. Please describe your experience in more detail."

    if len(job_description) > MAX_JD_LENGTH:
        return False, f"Job description is too long (max {MAX_JD_LENGTH} characters). Please trim it."

    if len(user_background) > MAX_BACKGROUND_LENGTH:
        return False, f"Background is too long (max {MAX_BACKGROUND_LENGTH} characters). Please trim it."

    combined_input = (job_description + " " + user_background).lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, combined_input, re.IGNORECASE):
            return False, "Input contains disallowed content. Please enter a valid job description and background."

    return True, "ok"


def mask_pii(text: str) -> str:
    """Masks sensitive PII patterns for safe logging."""
    text = re.sub(r"\b\d{3}-\d{2}-\d{4}\b", "[SSN REDACTED]", text)
    text = re.sub(r"\b\d{16}\b", "[CARD REDACTED]", text)

    def mask_email(match):
        email = match.group()
        parts = email.split("@")
        return parts[0][:2] + "***@" + parts[1]

    text = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", mask_email, text)
    return text
