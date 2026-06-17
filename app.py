"""
Preference Ranking — Trainer Practice App.

Mirrors the in-tool grading UI (see screenshots in /test/) with:

  - top banner: user request + predicted category
  - sidebar: trainer info + nav + progress (with green ✅ for done sections)
  - per-response: 4 dimensions + holistic Satisfaction, each with inline ✅
  - per-pair: side-by-side responses + 7-point comparison
  - final overall comment

Submissions are saved via storage.save_submission (Sheets or local JSON).

Run locally:
    streamlit run trainer_app/app.py

Optional admin viewer (read local submissions):
    open http://localhost:8501/?admin=1
"""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

from tasks import get_task
from storage import save_submission, list_local_submissions


# -----------------------------------------------------------------------------
# Page config + global CSS
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Instruction Fine-Tuning Grading — Practice",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.2rem; padding-bottom: 4rem; max-width: 1500px; }

      .top-banner {
        background: #1f2937; color: #e5e7eb;
        padding: 10px 18px; border-radius: 8px;
        font-weight: 600; letter-spacing: 0.02em; font-size: 14px;
        margin-bottom: 14px;
      }
      .pred-cat { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
      .user-request {
        background: #dbeafe; color: #0f172a;
        border: 1px solid #bfdbfe; border-radius: 6px;
        padding: 14px 16px; font-size: 15px; line-height: 1.5;
      }
      .section-h {
        font-size: 13px; font-weight: 700; color: #334155;
        text-transform: uppercase; letter-spacing: 0.08em;
        margin: 18px 0 8px 0;
      }
      .question-label { font-weight: 600; font-size: 15px; margin: 12px 0 4px 0; }
      .tick-ok { color: #10b981; font-weight: 700; }
      .tick-pending { color: #cbd5e1; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# Rating vocabularies (kept identical to the official tool)
# -----------------------------------------------------------------------------

FOLLOWING = ["— select —", "Not following", "Partially following", "Fully following"]
CONCISION = ["— select —", "Bad", "Acceptable", "Good"]
CONCISION_DIR = ["Could have been made shorter", "Could have been made longer"]
TRUTHFUL = ["— select —", "Not Truthful", "Partially Truthful", "Truthful"]
SATISFACTION = [
    "— select —",
    "Highly Unsatisfying",
    "Slightly Unsatisfying",
    "Slightly Satisfying",
    "Highly Satisfying",
]
PAIRWISE = [
    "— select —",
    "Left Much Better",
    "Left Better",
    "Left Slightly Better",
    "Same",
    "Right Slightly Better",
    "Right Better",
    "Right Much Better",
]

UNSELECTED = "— select —"

# Every widget key whose state must survive tab navigation. Streamlit otherwise
# drops the entry for any widget that wasn't rendered in the current rerun.
PERSISTENT_KEYS: list[str] = (
    [f"{rid}_{d}"
     for rid in ("A", "B", "C")
     for d in ("following", "concision", "concision_dir", "truthful", "satisfaction")]
    + ["pair_B_vs_A", "pair_C_vs_A", "pair_C_vs_B"]
    + ["trainer_name", "trainer_email", "overall_comment"]
)


def _persist_widget_state() -> None:
    """Re-assign each known widget key to itself.

    This is the standard Streamlit pattern to keep widget state alive across
    reruns when the widget itself isn't rendered. Must be called at the very
    top of `main()` BEFORE any widget renders.
    """
    for k in PERSISTENT_KEYS:
        if k in st.session_state:
            st.session_state[k] = st.session_state[k]


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _filled(key: str) -> bool:
    val = st.session_state.get(key, UNSELECTED)
    if isinstance(val, str):
        return val.strip() not in ("", UNSELECTED)
    return val is not None


def _tick(filled: bool) -> str:
    return (
        '<span class="tick-ok">✅</span>' if filled
        else '<span class="tick-pending">◯</span>'
    )


def _question(label: str, filled: bool) -> None:
    st.markdown(
        f'<div class="question-label">{_tick(filled)} &nbsp; {label}</div>',
        unsafe_allow_html=True,
    )


def _section_done(prefix: str) -> bool:
    keys = [f"{prefix}_{d}" for d in ("following", "concision", "truthful", "satisfaction")]
    return all(_filled(k) for k in keys)


def _section_filled_count(prefix: str) -> int:
    keys = [f"{prefix}_{d}" for d in ("following", "concision", "truthful", "satisfaction")]
    return sum(_filled(k) for k in keys)


def _pair_done(pair_key: str) -> bool:
    return _filled(pair_key)


def _init_state() -> None:
    if "started_at" not in st.session_state:
        st.session_state.started_at = time.time()
    defaults = {
        "trainer_name": "",
        "trainer_email": "",
        "overall_comment": "",
        "current_tab": "Response A",
        "submitted": False,
        "last_submission_id": "",
        "last_submission_msg": "",
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


def _reset_form() -> None:
    """Wipe every widget value + submission marker so the trainer can start over."""
    for k in PERSISTENT_KEYS:
        st.session_state.pop(k, None)
    for k in ("submitted", "last_submission_id", "last_submission_msg"):
        st.session_state[k] = "" if k != "submitted" else False
    st.session_state.current_tab = "Response A"
    st.session_state.started_at = time.time()


# -----------------------------------------------------------------------------
# Admin viewer (?admin=1)
# -----------------------------------------------------------------------------

def render_admin() -> None:
    st.title("Admin — Local Submissions")
    rows = list_local_submissions()
    if not rows:
        st.info("No local submissions yet. They live in `trainer_app/submissions/`.")
        return
    st.success(f"{len(rows)} submission(s) on disk.")
    for row in rows:
        with st.expander(
            f"{row.get('timestamp_utc', '?')} — {row.get('trainer_name', '?')} — "
            f"{row.get('submission_id', '?')[:8]}"
        ):
            st.json(row)


# -----------------------------------------------------------------------------
# Per-response evaluation panel
# -----------------------------------------------------------------------------

def render_response_panel(task: dict, resp: dict) -> None:
    """Render single-response evaluation: dimensions on the right of the response."""
    rid = resp["id"]
    left, right = st.columns([6, 5], gap="large")

    with left:
        st.markdown(f"#### {resp['label']}")
        st.markdown(resp["markdown"])

    with right:
        _question("How well does the response follow instructions?",
                  _filled(f"{rid}_following"))
        st.radio(
            label="following", options=FOLLOWING,
            key=f"{rid}_following", horizontal=True, label_visibility="collapsed",
        )

        _question("How concise is the response?", _filled(f"{rid}_concision"))
        st.radio(
            label="concision", options=CONCISION,
            key=f"{rid}_concision", horizontal=True, label_visibility="collapsed",
        )

        concision_val = st.session_state.get(f"{rid}_concision", UNSELECTED)
        if concision_val in ("Bad", "Acceptable"):
            _question("Length direction", _filled(f"{rid}_concision_dir"))
            st.selectbox(
                "Length direction", CONCISION_DIR,
                key=f"{rid}_concision_dir", label_visibility="collapsed",
            )
        else:
            # Drop the key so re-mounting the widget later doesn't error on
            # a stale "N/A" value not in the options list.
            st.session_state.pop(f"{rid}_concision_dir", None)

        _question("How truthful is the response?", _filled(f"{rid}_truthful"))
        st.radio(
            label="truthful", options=TRUTHFUL,
            key=f"{rid}_truthful", horizontal=True, label_visibility="collapsed",
        )

        st.markdown(f"**Your ratings for {resp['label']}**")
        summary_rows = [
            ("Following Instructions", st.session_state.get(f"{rid}_following", "N/A")),
            ("Concision", st.session_state.get(f"{rid}_concision", "N/A")),
            ("Truthful", st.session_state.get(f"{rid}_truthful", "N/A")),
        ]
        st.table({
            "Dimension": [r[0] for r in summary_rows],
            "Rating": [r[1] if r[1] != UNSELECTED else "N/A" for r in summary_rows],
        })

        _question("How satisfying is the response?", _filled(f"{rid}_satisfaction"))
        st.radio(
            label="satisfaction", options=SATISFACTION,
            key=f"{rid}_satisfaction", horizontal=True, label_visibility="collapsed",
        )

    # Section completion banner
    st.divider()
    done = _section_filled_count(rid)
    if done == 4:
        st.success(
            f"✅ All 4 dimensions filled for {resp['label']}. "
            "Move to the next tab from the sidebar."
        )
    else:
        st.info(
            f"{done} of 4 dimensions filled for {resp['label']}. "
            f"{4 - done} remaining."
        )


# -----------------------------------------------------------------------------
# Pairwise comparison panel
# -----------------------------------------------------------------------------

def render_pair_panel(task: dict, left_id: str, right_id: str) -> None:
    by_id = {r["id"]: r for r in task["responses"]}
    left_r = by_id[left_id]
    right_r = by_id[right_id]

    pair_key = f"pair_{right_id}_vs_{left_id}"  # B_vs_A, C_vs_A, C_vs_B

    # Warn if user is here before completing the single-response sections.
    incomplete = [rid for rid in (left_id, right_id) if not _section_done(rid)]
    if incomplete:
        st.warning(
            f"You haven't finished the dimension ratings for "
            f"{', '.join(f'Response {x}' for x in incomplete)}. The summary "
            "below will show N/A until you do."
        )

    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(f"#### {left_r['label']}  *(Left)*")
        st.markdown(left_r["markdown"])
    with c2:
        st.markdown(f"#### {right_r['label']}  *(Right)*")
        st.markdown(right_r["markdown"])

    st.markdown("**Your single-response ratings (read-only):**")
    rows = []
    for label, dim_key in [
        ("Instruction Following", "following"),
        ("Concision", "concision"),
        ("Truthful", "truthful"),
        ("Satisfaction", "satisfaction"),
    ]:
        rows.append({
            "Dimension": label,
            f"Rating for {left_id}": st.session_state.get(f"{left_id}_{dim_key}", "N/A"),
            f"Rating for {right_id}": st.session_state.get(f"{right_id}_{dim_key}", "N/A"),
        })
    st.table(rows)

    _question(
        f"Compare responses in terms of satisfaction "
        f"({left_r['label']} vs {right_r['label']}):",
        _filled(pair_key),
    )
    st.radio(
        label=f"{left_id}_vs_{right_id}",
        options=PAIRWISE,
        key=pair_key,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.caption(
        f"Reads as: '{left_r['label']} is …' vs '{right_r['label']} is …'. "
        "Use Satisfaction as the primary criterion; Truthfulness breaks ties."
    )

    st.divider()
    if _pair_done(pair_key):
        st.success(
            f"✅ Pairwise verdict recorded: **{st.session_state[pair_key]}**. "
            "Move to the next tab from the sidebar."
        )
    else:
        st.info("Pick one of the 7 options above to record your verdict for this pair.")


# -----------------------------------------------------------------------------
# Sidebar progress + tab switcher
# -----------------------------------------------------------------------------

def render_sidebar(task: dict) -> str:
    st.sidebar.header("Trainer info")
    st.sidebar.text_input("Your name", key="trainer_name", placeholder="Jane Doe")
    st.sidebar.text_input("Your email", key="trainer_email", placeholder="jane@example.com")
    st.sidebar.divider()

    tabs = ["Response A", "Response B", "Response C", "B and A", "C and A", "C and B", "Submit"]
    done_map = {
        "Response A": _section_done("A"),
        "Response B": _section_done("B"),
        "Response C": _section_done("C"),
        "B and A": _pair_done("pair_B_vs_A"),
        "C and A": _pair_done("pair_C_vs_A"),
        "C and B": _pair_done("pair_C_vs_B"),
        "Submit": False,
    }

    done_count = sum(1 for t in tabs[:-1] if done_map[t])
    st.sidebar.markdown(f"### Progress — {done_count}/6 complete")
    st.sidebar.progress(done_count / 6)

    selected = st.session_state.get("current_tab", "Response A")
    for t in tabs:
        is_done = done_map[t]
        is_active = (t == selected)
        if is_done:
            marker = "✅"
        elif is_active:
            marker = "▶︎"
        else:
            marker = "◯"
        label = f"{marker}  {t}"
        if is_active:
            label += "  ← here"
        if st.sidebar.button(label, key=f"nav_{t}", use_container_width=True):
            st.session_state.current_tab = t
            st.rerun()

    st.sidebar.divider()
    st.sidebar.caption(
        "Practice clone of the grading tool. ✅ marks completed sections. "
        "Your answers are kept when you switch tabs."
    )
    return st.session_state.current_tab


# -----------------------------------------------------------------------------
# Submit panel
# -----------------------------------------------------------------------------

def all_required_done() -> bool:
    if not all(_section_done(s) for s in ("A", "B", "C")):
        return False
    if not all(_pair_done(p) for p in ("pair_B_vs_A", "pair_C_vs_A", "pair_C_vs_B")):
        return False
    if not st.session_state.get("trainer_name", "").strip():
        return False
    if len(st.session_state.get("overall_comment", "").strip()) < 30:
        return False
    return True


def _readiness_checklist() -> list[tuple[str, bool]]:
    return [
        ("Response A — all 4 dimensions", _section_done("A")),
        ("Response B — all 4 dimensions", _section_done("B")),
        ("Response C — all 4 dimensions", _section_done("C")),
        ("Pair B vs A", _pair_done("pair_B_vs_A")),
        ("Pair C vs A", _pair_done("pair_C_vs_A")),
        ("Pair C vs B", _pair_done("pair_C_vs_B")),
        ("Trainer name filled", bool(st.session_state.get("trainer_name", "").strip())),
        ("Overall comment ≥ 30 chars",
         len(st.session_state.get("overall_comment", "").strip()) >= 30),
    ]


def render_submit_panel(task: dict) -> None:
    st.subheader("Final comment & submit")
    st.caption(
        "Write **one** comment that justifies your **overall ranking of all "
        "three responses** (Rank 1, 2, 3). Name each response (A, B, C), "
        "compare them on concrete reasons, and tie each placement to a "
        "dimension (Following / Truthfulness / Concision / Satisfaction). "
        "English only. Minimum 30 characters."
    )
    _question(
        "Please describe the reasons for your gradings",
        _filled("overall_comment")
        and len(st.session_state.get("overall_comment", "").strip()) >= 30,
    )
    st.text_area(
        "overall_comment",
        key="overall_comment",
        height=200,
        label_visibility="collapsed",
        placeholder=(
            "Example shape: '<X> is ranked 1 because … . <Y> is ranked 2; "
            "close to <X> but missing … . <Z> is ranked 3 because … . "
            "Truthfulness/Concision drives the ordering.'"
        ),
    )

    st.markdown("**Readiness checklist**")
    for label, ok in _readiness_checklist():
        st.markdown(f"- {_tick(ok)} &nbsp; {label}", unsafe_allow_html=True)

    with st.expander("Review what will be submitted (JSON)"):
        st.json(_build_payload(task))

    disabled = not all_required_done()
    if disabled:
        st.warning(
            "Fix every ◯ above before you can submit. (All A/B/C dimensions, "
            "all 3 pairwise verdicts, your name, and a comment ≥ 30 chars.)"
        )

    if st.button("Submit", type="primary", disabled=disabled, use_container_width=True):
        with st.spinner("Submitting… this can take a few seconds while we save to Google Sheets."):
            ok, msg, submission_id = save_submission(_build_payload(task))
        if ok:
            st.session_state.submitted = True
            st.session_state.last_submission_id = submission_id
            st.session_state.last_submission_msg = msg
            st.rerun()
        else:
            st.error(f"Submission failed: {msg}")


def render_post_submit_view(task: dict) -> None:
    """Shown after a successful submission instead of the form."""
    st.success("✅ Submitted successfully!")
    st.markdown(
        f"**Submission ID:** `{st.session_state.last_submission_id}`"
    )
    st.caption(st.session_state.last_submission_msg or "")
    st.balloons()

    st.divider()
    st.markdown("### Want to do another?")
    st.write(
        "Clicking **Start new submission** will clear all your answers and "
        "take you back to Response A. Your previous submission has already "
        "been saved — both in Google Sheets and as a local backup file."
    )
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Start new submission", type="primary", use_container_width=True):
            _reset_form()
            st.rerun()
    with c2:
        st.markdown(
            "If you're done for today, you can simply close this tab. "
            "Your submission is safe."
        )


def _build_payload(task: dict) -> dict[str, Any]:
    def r(rid: str) -> dict[str, str]:
        return {
            "following": st.session_state.get(f"{rid}_following", ""),
            "concision": st.session_state.get(f"{rid}_concision", ""),
            "concision_dir": st.session_state.get(f"{rid}_concision_dir", "N/A"),
            "truthful": st.session_state.get(f"{rid}_truthful", ""),
            "satisfaction": st.session_state.get(f"{rid}_satisfaction", ""),
        }

    return {
        "task_id": task["task_id"],
        "trainer_name": st.session_state.get("trainer_name", "").strip(),
        "trainer_email": st.session_state.get("trainer_email", "").strip(),
        "ratings": {"A": r("A"), "B": r("B"), "C": r("C")},
        "pairs": {
            "B_vs_A": st.session_state.get("pair_B_vs_A", ""),
            "C_vs_A": st.session_state.get("pair_C_vs_A", ""),
            "C_vs_B": st.session_state.get("pair_C_vs_B", ""),
        },
        "overall_comment": st.session_state.get("overall_comment", "").strip(),
        "elapsed_seconds": int(time.time() - st.session_state.started_at),
    }


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main() -> None:
    # CRITICAL: must run BEFORE any widget renders so unmounted widgets'
    # values survive tab navigation.
    _persist_widget_state()
    _init_state()

    if st.query_params.get("admin") == "1":
        render_admin()
        return

    task = get_task()

    st.markdown(
        '<div class="top-banner">Instruction Fine-Tuning Grading — Practice</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="pred-cat">Predicted Category: {task["category"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("**User**")
    st.markdown(
        f'<div class="user-request">{task["user_request"]}</div>',
        unsafe_allow_html=True,
    )

    # Post-submit view replaces the form; the sidebar stays hidden until reset.
    if st.session_state.get("submitted"):
        render_post_submit_view(task)
        return

    st.markdown('<div class="section-h">Evaluation</div>', unsafe_allow_html=True)

    selected = render_sidebar(task)

    if selected == "Response A":
        render_response_panel(task, task["responses"][0])
    elif selected == "Response B":
        render_response_panel(task, task["responses"][1])
    elif selected == "Response C":
        render_response_panel(task, task["responses"][2])
    elif selected == "B and A":
        render_pair_panel(task, left_id="A", right_id="B")
    elif selected == "C and A":
        render_pair_panel(task, left_id="A", right_id="C")
    elif selected == "C and B":
        render_pair_panel(task, left_id="B", right_id="C")
    elif selected == "Submit":
        render_submit_panel(task)


if __name__ == "__main__":
    main()
