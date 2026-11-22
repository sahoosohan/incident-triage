# AI-Assisted Incident Triage Tool
Reads sample tickets + logs, redacts sensitive data, classifies category/priority with an LLM,
suggests root causes and KB articles, requires human validation, and shows SLA + recurring-issue trends.

    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=...        # optional; without it a rule-based fallback is used
    python -m triage.cli run            # triage tickets
    python -m triage.cli review         # human validation in the terminal
    python -m triage.cli summary        # SLA status
    streamlit run dashboard.py          # dashboard + review queue

Pipeline: ticket + log tail -> redact (email, IP, phone, secrets) -> KB retrieval -> LLM (JSON) -> human review -> SLA/trends.
Set TRIAGE_MODEL to change the model.
