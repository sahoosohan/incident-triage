"""LLM call with an offline heuristic fallback so the demo runs without a key."""
import json, os, re

MODEL = os.getenv("TRIAGE_MODEL", "claude-sonnet-5-5")

SYSTEM = ("You are an IT service-desk triage assistant. Reply with ONLY a JSON object: "
          '{"category": str, "priority": "P1|P2|P3|P4", "root_causes": [str, str], '
          '"kb_ids": [str]}. P1=outage/all users, P2=major impact, P3=degraded, P4=request. '
          "Only use kb_ids from the candidates given.")

def _llm(prompt: str):
    import anthropic
    client = anthropic.Anthropic()
    r = client.messages.create(model=MODEL, max_tokens=500, system=SYSTEM,
                               messages=[{"role": "user", "content": prompt}])
    txt = "".join(b.text for b in r.content if b.type == "text")
    return json.loads(re.search(r"\{.*\}", txt, re.S).group(0))

CATEGORIES = [
    ("Authentication", ["login", "password", "vpn", "locked", "mfa", "credentials"]),
    ("Database", ["database", "connection pool", "pool exhausted", "too many connections", "sql"]),
    ("Storage", ["disk", "no space", "volume", "storage"]),
    ("Email", ["outlook", "mailbox", "email", "sync"]),
    ("Performance", ["slow", "latency", "loading"]),
    ("Hardware", ["printer", "monitor", "laptop", "spooler"]),
    ("Application", ["api", "500", "error"]),
]
CAUSES = [
    (r"account locked|invalid credentials|auth failed", "Expired credentials or account lockout"),
    (r"pool exhausted|too many connections|request timed out", "Database connection pool exhausted"),
    (r"no space left|usage 100%", "Disk volume full (logs/temp files growing unchecked)"),
    (r"ost file|cache mismatch|sync failed", "Corrupt mail profile or OST cache"),
    (r"slow query|high latency", "Slow queries or resource contention"),
    (r"spooler|unreachable", "Print spooler stopped or network issue"),
]

def _heuristic(text: str, candidates):
    low = text.lower()
    cat = next((c for c, kws in CATEGORIES if any(k in low for k in kws)), "General")
    if re.search(r"all users|production|outage|down\b", low): pri = "P1"
    elif re.search(r"cannot|can't|fail|locked|100%|500", low): pri = "P2"
    elif re.search(r"slow|offline|intermittent|stuck", low): pri = "P3"
    else: pri = "P4"
    causes = [c for p, c in CAUSES if re.search(p, low)][:2] or ["Unclear - needs engineer investigation"]
    return {"category": cat, "priority": pri, "root_causes": causes,
            "kb_ids": [c["id"] for c in candidates[:2]]}

def complete(prompt: str, text: str, candidates):
    """Returns (result_dict, source)."""
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return _llm(prompt), "llm"
        except Exception as e:
            print(f"  ! LLM failed ({e.__class__.__name__}); using heuristic fallback")
    return _heuristic(text, candidates), "heuristic"
