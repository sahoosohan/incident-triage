"""streamlit run dashboard.py"""
import pandas as pd, streamlit as st
from triage.engine import load_tickets, load_results, save_results, triage_ticket
from triage.sla import sla_status

st.set_page_config(page_title="Incident Triage", layout="wide")
st.title("AI-Assisted Incident Triage")

res = load_results()
tix = load_tickets()
if st.sidebar.button("Triage new tickets"):
    for t in tix:
        res.setdefault(t["id"], triage_ticket(t))
    save_results(res); st.rerun()

rows = []
for t in tix:
    r = res.get(t["id"])
    if not r: continue
    rv = r["review"]
    pri = rv["priority"] or r["priority"]
    rows.append({"Ticket": t["id"], "Subject": t["subject"], "Category": rv["category"] or r["category"],
                 "Priority": pri, "SLA": sla_status(pri, t["created_at"], t["resolved_at"]),
                 "Review": rv["status"], "Root cause": r["root_causes"][0],
                 "Opened": t["created_at"].date()})
df = pd.DataFrame(rows)
if df.empty:
    st.info("No results yet. Run `python -m triage.cli run` or use the sidebar button."); st.stop()

tab1, tab2, tab3 = st.tabs(["SLA status", "Recurring issues", "Review queue"])
with tab1:
    c = st.columns(4)
    for col, s in zip(c, ["On track", "At risk", "Breached", "Met"]):
        col.metric(s, int((df.SLA == s).sum()))
    st.dataframe(df.drop(columns=["Root cause", "Opened"]), width="stretch", hide_index=True)
with tab2:
    rec = df.groupby(["Category", "Root cause"]).size().reset_index(name="Count")
    st.subheader("Recurring root causes (2+ tickets)")
    st.dataframe(rec[rec.Count > 1].sort_values("Count", ascending=False), hide_index=True, width="stretch")
    st.bar_chart(df.groupby("Category").size())
with tab3:
    pending = [tid for tid, r in res.items() if r["review"]["status"] == "pending"]
    st.caption(f"{len(pending)} AI suggestions awaiting human validation")
    for tid in pending:
        r, t = res[tid], next(x for x in tix if x["id"] == tid)
        with st.expander(f"{tid} - {t['subject']}  ->  {r['category']} / {r['priority']}"):
            st.write("**Likely causes:**", "; ".join(r["root_causes"]))
            st.write("**KB:**", ", ".join(r["kb_ids"]) or "-")
            st.write("**Redacted before AI:**", r["redactions"] or "nothing")
            cat = st.text_input("Category", r["category"], key=f"c{tid}")
            pri = st.selectbox("Priority", ["P1", "P2", "P3", "P4"], ["P1", "P2", "P3", "P4"].index(r["priority"]), key=f"p{tid}")
            a, b = st.columns(2)
            if a.button("Approve / save edits", key=f"a{tid}"):
                edited = (cat, pri) != (r["category"], r["priority"])
                r["review"].update(status="edited" if edited else "accepted", category=cat, priority=pri)
                save_results(res); st.rerun()
            if b.button("Reject", key=f"r{tid}"):
                r["review"]["status"] = "rejected"; save_results(res); st.rerun()
