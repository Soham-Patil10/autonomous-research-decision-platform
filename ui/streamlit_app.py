"""Review console: submit tasks, resolve escalations, explore traces.

Three tabs, matching the three things a human actually does with this system:
ask it something, decide on what it escalated, and work out why a run went wrong.
"""

from __future__ import annotations

import requests
import streamlit as st

API = "http://localhost:8000/api"

st.set_page_config(page_title="Research & Decision Console", layout="wide")
st.title("Autonomous Research & Decision Intelligence")

ask_tab, review_tab, trace_tab = st.tabs(["Ask", "Approval queue", "Trace explorer"])

# --------------------------------------------------------------------------- #
with ask_tab:
    question = st.text_area("Question", "Should we expand into the German EV market?")
    if st.button("Submit", type="primary"):
        r = requests.post(f"{API}/tasks", json={"question": question}, timeout=30)
        st.session_state["task_id"] = r.json()["task_id"]
        st.success(f"submitted: {st.session_state['task_id']}")

    if task_id := st.session_state.get("task_id"):
        if st.button("Refresh status"):
            st.json(requests.get(f"{API}/tasks/{task_id}", timeout=30).json())
        report = requests.get(f"{API}/tasks/{task_id}/report", timeout=30)
        if report.ok:
            data = report.json()
            st.metric("Confidence", f"{data['confidence']:.0%}")
            st.subheader("Recommendation")
            st.write(data["recommendation"])
            st.subheader("Claims and citations")
            for claim in data["claims"]:
                icon = {True: "OK", False: "UNVERIFIED", None: "?"}[claim["verified"]]
                st.markdown(f"**[{icon}]** {claim['text']}  \n`{claim['evidence_ids']}`")
            if data["unverified"]:
                st.warning("Unverified claims:\n\n" + "\n".join(f"- {u}" for u in data["unverified"]))

# --------------------------------------------------------------------------- #
with review_tab:
    st.caption("Tasks the system escalated because it was not confident enough to proceed.")
    queue = requests.get(f"{API}/review/queue", timeout=30).json()
    if not queue:
        st.info("Nothing awaiting review.")
    for item in queue:
        with st.expander(f"[{item['risk'].upper()}] {item['reason']} - task {item['task_id']}"):
            st.write(item["summary"])
            st.json(item["payload"])
            note = st.text_input("Reviewer note", key=f"n{item['id']}")
            c1, c2 = st.columns(2)
            if c1.button("Approve", key=f"a{item['id']}"):
                requests.post(
                    f"{API}/review/{item['id']}",
                    json={"decision": "approved", "reviewer_note": note},
                    timeout=30,
                )
            if c2.button("Reject", key=f"r{item['id']}"):
                requests.post(
                    f"{API}/review/{item['id']}",
                    json={"decision": "rejected", "reviewer_note": note},
                    timeout=30,
                )

# --------------------------------------------------------------------------- #
with trace_tab:
    st.caption("Every span of a run, in order. The first error is where to start reading.")
    tid = st.text_input("Task id", st.session_state.get("task_id", ""))
    if tid:
        trace = requests.get(f"{API}/tasks/{tid}/trace", timeout=30).json()
        for s in trace:
            mark = "FAIL" if s.get("status") == "error" else "ok"
            st.markdown(f"`{mark}` **{s['name']}** — {s.get('duration_ms', 0):.0f} ms")
            if s.get("error"):
                st.error(s["error"])
