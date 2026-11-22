import json, re
from datetime import datetime, timedelta
from pathlib import Path
from .redact import redact
from .llm import complete

DATA = Path(__file__).resolve().parent.parent / "data"
RESULTS = DATA / "results.json"

def load_tickets(now=None):
    now = now or datetime.now()
    out = []
    for t in json.loads((DATA / "tickets.json").read_text()):
        t["created_at"] = now - timedelta(hours=t["age_hours"])
        r = t.get("resolved_after_hours")
        t["resolved_at"] = t["created_at"] + timedelta(hours=r) if r else None
        out.append(t)
    return out

def read_log(t, tail=15):
    if not t.get("log"): return ""
    return "\n".join((DATA / "logs" / t["log"]).read_text().splitlines()[-tail:])

def kb_candidates(text, k=3):
    kb = json.loads((DATA / "kb.json").read_text())
    words = set(re.findall(r"[a-z]+", text.lower()))
    scored = sorted(kb, key=lambda a: -len(words & set(a["keywords"])))
    return [a for a in scored if words & set(a["keywords"])][:k]

def triage_ticket(t):
    raw = f"Subject: {t['subject']}\nBody: {t['body']}\nLog tail:\n{read_log(t)}"
    clean, counts = redact(raw)                     # redact BEFORE the model sees anything
    cands = kb_candidates(clean)
    prompt = clean + "\n\nKB candidates:\n" + "\n".join(f"{a['id']}: {a['title']}" for a in cands)
    res, source = complete(prompt, clean, cands)
    valid = {a["id"] for a in json.loads((DATA / "kb.json").read_text())}
    return {"ticket_id": t["id"], "category": res["category"], "priority": res["priority"],
            "root_causes": res["root_causes"], "kb_ids": [k for k in res["kb_ids"] if k in valid],
            "redactions": counts, "source": source,
            "review": {"status": "pending", "category": None, "priority": None, "note": ""}}

def load_results():
    return json.loads(RESULTS.read_text()) if RESULTS.exists() else {}

def save_results(res):
    RESULTS.write_text(json.dumps(res, indent=1))
