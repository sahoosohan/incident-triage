"""python -m triage.cli run | review | summary"""
import argparse
from .engine import load_tickets, triage_ticket, load_results, save_results
from .sla import sla_status

def cmd_run(_):
    res = load_results()
    for t in load_tickets():
        if t["id"] in res: continue
        res[t["id"]] = triage_ticket(t)
        r = res[t["id"]]
        print(f"{t['id']}: {r['category']:<15}{r['priority']}  [{r['source']}]  redacted={r['redactions'] or '-'}")
    save_results(res)

def cmd_review(_):
    res = load_results()
    tix = {t["id"]: t for t in load_tickets()}
    for tid, r in res.items():
        if r["review"]["status"] != "pending": continue
        print(f"\n{tid} - {tix[tid]['subject']}\n  AI: {r['category']} / {r['priority']}"
              f"\n  Likely causes: {'; '.join(r['root_causes'])}\n  KB: {', '.join(r['kb_ids']) or '-'}")
        a = input("  [a]ccept  [e]dit  [r]eject  [s]kip  [q]uit > ").strip().lower()
        if a == "q": break
        if a == "a": r["review"].update(status="accepted", category=r["category"], priority=r["priority"])
        elif a == "e":
            r["review"].update(status="edited",
                category=input("  category: ").strip() or r["category"],
                priority=(input("  priority P1-P4: ").strip().upper() or r["priority"]),
                note=input("  note: "))
        elif a == "r": r["review"].update(status="rejected", note=input("  reason: "))
    save_results(res)

def cmd_summary(_):
    res = load_results()
    for t in load_tickets():
        r = res.get(t["id"])
        if not r: continue
        pri = r["review"]["priority"] or r["priority"]
        print(f"{t['id']}  {pri}  {sla_status(pri, t['created_at'], t['resolved_at']):<9} {t['subject']}")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["run", "review", "summary"])
    a = p.parse_args()
    {"run": cmd_run, "review": cmd_review, "summary": cmd_summary}[a.cmd](a)
