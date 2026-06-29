"""
Preference Ranking — Trainer Practice App.

Two independent modes, picked from a landing page:

  1. **Knowledge Quiz** (`?mode=quiz`) — 33-item self-study quiz built from
     `Project_data/Preference_Ranking_QA_Quiz_v3.md`. Each answer freezes on
     click; the correct answer + rule are revealed inline; a per-email
     completion lock prevents retakes.
  2. **Grading Exercise** (`?mode=exercise`) — the existing 3-response grading
     UI that mirrors the in-tool grading screen.

Both modes share trainer name + email and persist via `storage.save_submission`
/ `storage.save_quiz_submission` (Sheets or local JSON).

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
from storage import (
    save_submission,
    list_local_submissions,
    list_local_quiz_submissions,
    QUIZ_HEADER,
)
from quiz import render_quiz, quiz_persistent_keys


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

      .landing-hero {
        background: linear-gradient(120deg, #1f2937, #0f172a);
        color: #f1f5f9; padding: 26px 28px; border-radius: 12px;
        margin-bottom: 18px;
      }
      .landing-hero h1 { font-size: 22px; margin: 0 0 6px 0; }
      .landing-hero p { margin: 0; color: #cbd5e1; font-size: 14px; }

      .mode-card {
        background: #ffffff; border: 1px solid #e5e7eb;
        border-radius: 12px; padding: 18px 20px; height: 100%;
      }
      .mode-card h3 { margin: 0 0 6px 0; font-size: 17px; color: #0f172a; }
      .mode-card p  { margin: 0 0 10px 0; color: #475569; font-size: 14px; line-height: 1.5; }
      .mode-card ul { margin: 0 0 12px 18px; padding: 0; color: #475569; font-size: 13px; }
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
    + quiz_persistent_keys()
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

def _is_valid_turing_email(email: str) -> bool:
    """Domain-restrict trainer emails to @turing.com (case-insensitive)."""
    e = (email or "").strip().lower()
    return e.endswith("@turing.com") and len(e) > len("@turing.com")


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


# Keys that belong to a specific exercise instance (ratings, pairs, comment,
# submission markers). Reset between tasks so opening Part 3 after Part 2 starts
# from a clean form. trainer_name / trainer_email are NOT in this list — they
# survive task switches.
_EXERCISE_RESET_KEYS: list[str] = (
    [f"{rid}_{d}"
     for rid in ("A", "B", "C")
     for d in ("following", "concision", "concision_dir", "truthful", "satisfaction")]
    + ["pair_B_vs_A", "pair_C_vs_A", "pair_C_vs_B", "overall_comment"]
)


def _reset_exercise_keep_identity() -> None:
    """Reset only the grading-exercise widgets and submission state.

    Used when the trainer switches from one task to another via the landing
    page so they don't see leftover ratings from the previous task. Trainer
    name + email are intentionally preserved.
    """
    for k in _EXERCISE_RESET_KEYS:
        st.session_state.pop(k, None)
    for k in ("submitted", "last_submission_id", "last_submission_msg"):
        st.session_state[k] = "" if k != "submitted" else False
    st.session_state.current_tab = "Response A"
    st.session_state.started_at = time.time()


# -----------------------------------------------------------------------------
# Admin viewer (?admin=1)
# -----------------------------------------------------------------------------

def _admin_authorized() -> bool:
    """Return True only if no password is configured, or the user supplied it.

    Configure by adding to .streamlit/secrets.toml (or Streamlit Cloud secrets):
        [admin]
        password = "your-pick-here"
    If no [admin] block exists, the admin view is open (useful locally).
    """
    try:
        configured = st.secrets.get("admin", {}).get("password")  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        configured = None
    if not configured:
        return True

    if st.session_state.get("admin_ok"):
        return True

    st.title("Admin login")
    st.text_input("Admin password", type="password", key="_admin_pw_entry")
    if st.button("Sign in"):
        if st.session_state.get("_admin_pw_entry") == configured:
            st.session_state.admin_ok = True
            st.rerun()
        st.error("Wrong password.")
    return False


# Friendly section headers for each exercise task_id, in landing-page order.
# Anything not in this map falls through to the "Other / unknown task" bucket
# at the bottom of the admin view so legacy or future rows aren't lost.
ADMIN_EXERCISE_PARTS: list[tuple[str, str, str]] = [
    # (task_id, section_heading, short_slug_for_filenames_and_keys)
    ("coding_random_sampling_v1",
     "Part 2 · Grading Exercise — Random sampling",
     "part2_random_sampling"),
    ("logic_dogs_v1",
     "Part 3 · Grading Exercise — Kennel logic",
     "part3_kennel_logic"),
    ("html_webpage_v1",
     "Part 4 · Grading Exercise — HTML & CSS",
     "part4_html_css"),
]


def render_admin() -> None:
    if not _admin_authorized():
        return

    st.title("Admin — Local Submissions on this container")
    st.caption(
        "⚠️ Streamlit Cloud's filesystem is **ephemeral** — local JSON files "
        "are wiped on every reboot/redeploy/idle-restart. Treat Google Sheets "
        "as your canonical store; these local files exist only as a fallback "
        "for submissions where the webhook itself failed."
    )

    quiz_rows = list_local_quiz_submissions()
    exercise_rows = list_local_submissions()

    if not quiz_rows and not exercise_rows:
        st.info(
            "No local JSON files on this container. Either nothing's been "
            "submitted since the last restart, or every submission since "
            "then was also written to Google Sheets (which is the normal case)."
        )
        return

    st.markdown("## Part 1 · Knowledge Quiz submissions")
    _render_admin_quiz_section(quiz_rows)

    # Group exercise submissions by task_id so each Part gets its own
    # heading + download buttons + table. Rows missing a task_id (legacy
    # rows from before the multi-task split) land in "_unknown".
    by_task: dict[str, list[dict[str, Any]]] = {}
    for row in exercise_rows:
        tid = row.get("task_id") or "_unknown"
        by_task.setdefault(tid, []).append(row)

    for task_id, heading, slug in ADMIN_EXERCISE_PARTS:
        st.divider()
        st.markdown(f"## {heading} submissions")
        _render_admin_exercise_section(
            by_task.pop(task_id, []),
            section_key=slug,
            filename_slug=slug,
        )

    # Anything left over — unrecognised task_id (typo, legacy, future task
    # not yet mapped). Render under a clearly-labelled catch-all section so
    # rows can't silently disappear.
    for task_id, rows in by_task.items():
        st.divider()
        label = "Legacy / no task_id" if task_id == "_unknown" else f"Task `{task_id}`"
        st.markdown(f"## Other — {label} submissions")
        slug = f"other_{task_id.replace('/', '_')}"
        _render_admin_exercise_section(
            rows, section_key=slug, filename_slug=slug
        )


def _render_admin_quiz_section(rows: list[dict[str, Any]]) -> None:
    if not rows:
        st.info("No quiz local backups on this container yet.")
        return

    st.success(f"{len(rows)} quiz local file(s) on disk.")

    import csv
    import io
    import json as _json
    import zipfile

    # CSV: storage.QUIZ_HEADER (the sheet schema) plus a trailing quiz_id
    # column so admins can tell the code and general-purpose quizzes apart.
    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow(list(QUIZ_HEADER) + ["quiz_id"])
    for r in rows:
        writer.writerow([
            r.get("submission_id", ""),
            r.get("timestamp_utc", ""),
            r.get("trainer_name", ""),
            r.get("trainer_email", ""),
            r.get("total_score", ""),
            r.get("max_score", ""),
            r.get("elapsed_seconds", ""),
            r.get("quiz_version", ""),
            _json.dumps(
                {
                    "answers": r.get("answers", {}),
                    "correctness": r.get("correctness", {}),
                },
                ensure_ascii=False,
            ),
            r.get("quiz_id", "") or "code_v3",
        ])
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    # Zip: one raw JSON per submission, prefixed `quiz_` to mirror disk layout.
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in rows:
            sid = r.get("submission_id", "unknown")
            zf.writestr(
                f"quiz_{sid}.json",
                _json.dumps(r, indent=2, ensure_ascii=False),
            )
    zip_bytes = zip_buf.getvalue()

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download quiz CSV",
            data=csv_bytes,
            file_name="quiz_submissions.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_quiz_csv",
        )
    with c2:
        st.download_button(
            "Download quiz ZIP (raw JSONs)",
            data=zip_bytes,
            file_name="quiz_submissions.zip",
            mime="application/zip",
            use_container_width=True,
            key="dl_quiz_zip",
        )

    st.markdown("### Preview")
    table_rows: list[dict[str, Any]] = []
    for r in rows:
        table_rows.append({
            "timestamp_utc": r.get("timestamp_utc", ""),
            "trainer_name": r.get("trainer_name", ""),
            "trainer_email": r.get("trainer_email", ""),
            "quiz": r.get("quiz_id", "") or "code_v3",
            "score": (
                f"{r.get('total_score', '?')} / {r.get('max_score', '?')}"
            ),
            "elapsed_s": r.get("elapsed_seconds", ""),
            "id": (r.get("submission_id", "") or "")[:8],
        })
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    st.markdown("### Per-submission details")
    for r in rows:
        with st.expander(
            f"{r.get('timestamp_utc', '?')} — {r.get('trainer_name', '?')} — "
            f"{r.get('submission_id', '?')[:8]}",
        ):
            st.json(r)


def _render_admin_exercise_section(
    rows: list[dict[str, Any]],
    *,
    section_key: str = "default",
    filename_slug: str = "submissions",
) -> None:
    """Render one Part's worth of grading-exercise submissions.

    `section_key` must be unique per call within a single admin render so
    that `st.download_button` widgets and `st.expander` keys don't collide
    when the admin shows multiple sections side-by-side.
    `filename_slug` is the basename used for the downloaded CSV / ZIP.
    """
    if not rows:
        st.info("No submissions for this section yet.")
        return

    st.success(f"{len(rows)} exercise local file(s) on disk.")

    import csv
    import io
    import json as _json
    import zipfile

    csv_buf = io.StringIO()
    writer = csv.writer(csv_buf)
    writer.writerow([
        "submission_id", "timestamp_utc", "trainer_name", "trainer_email", "task_id",
        "A_following", "A_concision", "A_concision_dir", "A_truthful", "A_satisfaction",
        "B_following", "B_concision", "B_concision_dir", "B_truthful", "B_satisfaction",
        "C_following", "C_concision", "C_concision_dir", "C_truthful", "C_satisfaction",
        "pair_B_vs_A", "pair_C_vs_A", "pair_C_vs_B",
        "overall_comment", "elapsed_seconds",
    ])
    for r in rows:
        ra = r.get("ratings", {}).get("A", {}) or {}
        rb = r.get("ratings", {}).get("B", {}) or {}
        rc = r.get("ratings", {}).get("C", {}) or {}
        pp = r.get("pairs", {}) or {}
        writer.writerow([
            r.get("submission_id", ""), r.get("timestamp_utc", ""),
            r.get("trainer_name", ""), r.get("trainer_email", ""), r.get("task_id", ""),
            ra.get("following", ""), ra.get("concision", ""), ra.get("concision_dir", ""),
            ra.get("truthful", ""), ra.get("satisfaction", ""),
            rb.get("following", ""), rb.get("concision", ""), rb.get("concision_dir", ""),
            rb.get("truthful", ""), rb.get("satisfaction", ""),
            rc.get("following", ""), rc.get("concision", ""), rc.get("concision_dir", ""),
            rc.get("truthful", ""), rc.get("satisfaction", ""),
            pp.get("B_vs_A", ""), pp.get("C_vs_A", ""), pp.get("C_vs_B", ""),
            r.get("overall_comment", ""), r.get("elapsed_seconds", ""),
        ])
    csv_bytes = csv_buf.getvalue().encode("utf-8")

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for r in rows:
            sid = r.get("submission_id", "unknown")
            zf.writestr(f"{sid}.json",
                        _json.dumps(r, indent=2, ensure_ascii=False))
    zip_bytes = zip_buf.getvalue()

    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Download exercise CSV",
            data=csv_bytes,
            file_name=f"{filename_slug}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"dl_exercise_csv_{section_key}",
        )
    with c2:
        st.download_button(
            "Download exercise ZIP (raw JSONs)",
            data=zip_bytes,
            file_name=f"{filename_slug}.zip",
            mime="application/zip",
            use_container_width=True,
            key=f"dl_exercise_zip_{section_key}",
        )

    st.markdown("### Preview")
    table_rows: list[dict[str, Any]] = []
    for r in rows:
        table_rows.append({
            "timestamp_utc": r.get("timestamp_utc", ""),
            "trainer_name": r.get("trainer_name", ""),
            "trainer_email": r.get("trainer_email", ""),
            "id": (r.get("submission_id", "") or "")[:8],
            "comment_len": len((r.get("overall_comment", "") or "")),
        })
    st.dataframe(
        table_rows,
        use_container_width=True,
        hide_index=True,
        key=f"df_exercise_{section_key}",
    )

    st.markdown("### Per-submission details")
    for r in rows:
        with st.expander(
            f"{r.get('timestamp_utc', '?')} — {r.get('trainer_name', '?')} — "
            f"{r.get('submission_id', '?')[:8]}"
        ):
            st.json(r)


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
    name = (st.session_state.get("trainer_name") or "").strip() or "—"
    email = (st.session_state.get("trainer_email") or "").strip() or "—"
    st.sidebar.header("Trainer")
    st.sidebar.markdown(f"**{name}**  \n<span style='color:#6b7280;font-size:12px'>{email}</span>",
                        unsafe_allow_html=True)
    st.sidebar.caption("To change these, click 'Back to home' at the bottom.")
    st.sidebar.divider()

    # Sidebar tab labels follow the in-panel left/right order: when the
    # pair panel renders A on the left and B on the right, the sidebar
    # says "A and B" too (not "B and A"). The underlying state keys
    # (pair_B_vs_A, pair_C_vs_A, pair_C_vs_B) and the storage column
    # names are intentionally NOT renamed — only the visible label.
    tabs = ["Response A", "Response B", "Response C", "A and B", "A and C", "B and C", "Submit"]
    done_map = {
        "Response A": _section_done("A"),
        "Response B": _section_done("B"),
        "Response C": _section_done("C"),
        "A and B": _pair_done("pair_B_vs_A"),
        "A and C": _pair_done("pair_C_vs_A"),
        "B and C": _pair_done("pair_C_vs_B"),
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
        "✅ marks completed sections. "
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
        "Write English comment that justifies all three pairwise "
        "preferences (A↔B, B↔C, C↔A): name every response (A, B, C), "
        "compare them on concrete reasons (exact instruction violated, "
        "wrong output, failed edge case, missing detail), and identify "
        "which dimension — Following Instructions, Localization, "
        "Concision, Truthfulness, or Satisfaction — drove each "
        "preference. Avoid generic checklists like \"all responses are "
        "concise/truthful.\""
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
# Exercise mode (the original grading flow)
# -----------------------------------------------------------------------------

def render_exercise(task_id: str | None = None) -> None:
    # Trainer identity is captured on the landing page now. If someone
    # deep-links to ?mode=exercise without it (or with a non-Turing email),
    # route them back instead of letting them submit an anonymous row.
    name = (st.session_state.get("trainer_name") or "").strip()
    email = (st.session_state.get("trainer_email") or "").strip()
    if not name or not email or not _is_valid_turing_email(email):
        st.warning(
            "Please go back to the home page and enter your name + a "
            "@turing.com email before starting the grading exercise."
        )
        if st.button("← Back to home", key="exercise_gate_back_home"):
            st.query_params.clear()
            st.rerun()
        return

    # task_id may come in via ?task=<id>; fall back to the default task on
    # bad/missing values so the existing Part-2 deep link keeps working.
    try:
        task = get_task(task_id) if task_id else get_task()
    except KeyError:
        st.error(
            f"Unknown task id `{task_id}` — sending you back to the home page."
        )
        st.query_params.clear()
        if st.button("← Back to home", key="exercise_bad_task_back_home"):
            st.rerun()
        return

    # Reset rating/pair/comment widgets when the trainer switches to a
    # different task (e.g. opens Part 3 after Part 2). Identity is kept.
    if st.session_state.get("current_task_id") != task["task_id"]:
        _reset_exercise_keep_identity()
        st.session_state.current_task_id = task["task_id"]

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
        _render_home_button_sidebar()
        return

    st.markdown('<div class="section-h">Evaluation</div>', unsafe_allow_html=True)

    selected = render_sidebar(task)
    _render_home_button_sidebar()

    if selected == "Response A":
        render_response_panel(task, task["responses"][0])
    elif selected == "Response B":
        render_response_panel(task, task["responses"][1])
    elif selected == "Response C":
        render_response_panel(task, task["responses"][2])
    elif selected == "A and B":
        render_pair_panel(task, left_id="A", right_id="B")
    elif selected == "A and C":
        render_pair_panel(task, left_id="A", right_id="C")
    elif selected == "B and C":
        render_pair_panel(task, left_id="B", right_id="C")
    elif selected == "Submit":
        render_submit_panel(task)


def _render_home_button_sidebar() -> None:
    """Tail of every mode's sidebar: a way back to the landing page."""
    st.sidebar.divider()
    if st.sidebar.button("← Back to home", key="back_home_exercise",
                         use_container_width=True):
        st.query_params.clear()
        st.rerun()


# -----------------------------------------------------------------------------
# Landing page (mode picker)
# -----------------------------------------------------------------------------

def render_landing() -> None:
    st.markdown(
        '<div class="landing-hero">'
        '<h1>Preference Ranking — Trainer Practice</h1>'
        '<p>Pick one of the two modes below. Each is self-contained; you can '
        'do them in any order.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Your details")
    c_name, c_email = st.columns(2)
    with c_name:
        st.text_input(
            "Your name", key="trainer_name",
            placeholder="Jane Doe",
        )
    with c_email:
        st.text_input(
            "Your Turing Email", key="trainer_email",
            placeholder="jane@turing.com",
            help="Must end with @turing.com. Used to lock the quiz to one attempt per trainer.",
        )

    name_ok = bool(st.session_state.get("trainer_name", "").strip())
    email_raw = (st.session_state.get("trainer_email") or "").strip()
    email_ok = _is_valid_turing_email(email_raw)
    can_start = name_ok and email_ok

    if email_raw and not email_ok:
        st.error("Email must be a @turing.com address.")
    elif not can_start:
        st.info("Enter your name and Turing email above to unlock all modes.")

    def _go_exercise(task_id: str) -> None:
        """Navigate to the grading exercise for a specific task_id."""
        st.query_params.clear()
        st.query_params["mode"] = "exercise"
        st.query_params["task"] = task_id
        st.rerun()

    # Knowledge quizzes — the two independent quizzes sit side by side. They
    # lock independently (per-email, per-quiz_id), so finishing one does not
    # block the other.
    st.markdown("### Knowledge quizzes")
    col_q, col_gq = st.columns(2, gap="large")

    with col_q:
        st.markdown(
            '<div class="mode-card">'
            '<h3>Part 1 · Knowledge Quiz — Code &amp; Math</h3>'
            '<p>29 multiple-choice and true/false items on code/math-eval '
            'comprehension, distilled from the project guide. Click an option '
            'to lock it in and reveal the correct answer + rule.</p>'
            '<ul>'
            '<li>One attempt per email (server-enforced)</li>'
            '<li>Inline reveal of correct answer after each click</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Take the Code & Math Quiz",
            type="primary",
            disabled=not can_start,
            use_container_width=True,
            key="go_quiz",
        ):
            st.query_params.clear()
            st.query_params["mode"] = "quiz"
            st.rerun()

    with col_gq:
        st.markdown(
            '<div class="mode-card">'
            '<h3>Part 1B · Knowledge Quiz — General-Purpose</h3>'
            '<p>31 items on <em>non</em>-code/math tasks: creative writing, '
            'rewrite/restyle, brainstorming, role play, Q&amp;A-from-text, '
            'summarization, and chit chat. Same click-to-lock + inline-reveal '
            'format.</p>'
            '<ul>'
            '<li>Separate one-attempt-per-email lock from the Code &amp; Math quiz</li>'
            '<li>Mirrors the real general-purpose certification tasks</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Take the General-Purpose Quiz",
            type="primary",
            disabled=not can_start,
            use_container_width=True,
            key="go_quiz_general",
        ):
            st.query_params.clear()
            st.query_params["mode"] = "quiz"
            st.query_params["set"] = "general"
            st.rerun()

    # Grading exercises — same UX, different task_id. Each button switches the
    # active task; per-task widget state is reset on entry so you start clean.
    st.markdown("### Grading exercises")
    col_e, col_p3 = st.columns(2, gap="large")

    with col_e:
        st.markdown(
            '<div class="mode-card">'
            '<h3>Part 2 · Grading Exercise — Random sampling</h3>'
            '<p>Rate three candidate responses on the four dimensions, run '
            'all three pairwise comparisons, and write one comparative '
            'comment justifying the final ranking.</p>'
            '<ul>'
            '<li>Topic: Python sampling without replacement</li>'
            '<li>Multiple attempts allowed</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Start the Grading Exercise",
            type="primary",
            disabled=not can_start,
            use_container_width=True,
            key="go_exercise",
        ):
            _go_exercise("coding_random_sampling_v1")

    with col_p3:
        st.markdown(
            '<div class="mode-card">'
            '<h3>Part 3 · Grading Exercise — Kennel logic</h3>'
            '<p>Same flow as Part 2, but applied to a set-theory word '
            'problem about 24 kennel dogs (color / tail / hair). Compare '
            'three derivations of the same target count.</p>'
            '<ul>'
            '<li>Topic: inclusion–exclusion reasoning</li>'
            '<li>Multiple attempts allowed</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Start Grading Exercise — Kennel logic",
            type="primary",
            disabled=not can_start,
            use_container_width=True,
            key="go_exercise_dogs",
        ):
            _go_exercise("logic_dogs_v1")

    st.markdown("")  # vertical breathing room before the next exercise row
    col_p4, _col_spacer = st.columns(2, gap="large")

    with col_p4:
        st.markdown(
            '<div class="mode-card">'
            '<h3>Part 4 · Grading Exercise — HTML &amp; CSS</h3>'
            '<p>Same flow as Part 2, applied to a "build a simple webpage" '
            'request. Three responses all produce a working page; '
            'differentiation is idiomatic CSS placement and presentational '
            'artifacts.</p>'
            '<ul>'
            '<li>Topic: HTML/CSS frontend basics</li>'
            '<li>Multiple attempts allowed</li>'
            '</ul>'
            '</div>',
            unsafe_allow_html=True,
        )
        if st.button(
            "Start Grading Exercise — HTML & CSS",
            type="primary",
            disabled=not can_start,
            use_container_width=True,
            key="go_exercise_html",
        ):
            _go_exercise("html_webpage_v1")

    st.divider()
    st.caption(
        "Tip: deep-link with `?mode=quiz` (Code & Math), "
        "`?mode=quiz&set=general` (General-Purpose), "
        "`?mode=exercise&task=coding_random_sampling_v1`, "
        "`?mode=exercise&task=logic_dogs_v1`, or "
        "`?mode=exercise&task=html_webpage_v1` to jump straight to a flow."
    )


# -----------------------------------------------------------------------------
# Main router
# -----------------------------------------------------------------------------

def main() -> None:
    # CRITICAL: must run BEFORE any widget renders so unmounted widgets'
    # values survive tab navigation.
    _persist_widget_state()
    _init_state()

    if st.query_params.get("admin") == "1":
        render_admin()
        return

    mode = st.query_params.get("mode", "")
    if mode == "quiz":
        # Optional `?set=<code|general>` selects which quiz dataset to serve.
        # Missing / unknown → the code/math quiz (default).
        render_quiz(st.query_params.get("set"))
    elif mode == "exercise":
        # Optional `?task=<task_id>` selects a specific grading task.
        # Missing → first task (Part 2, the canonical PDF example).
        render_exercise(st.query_params.get("task"))
    else:
        render_landing()


if __name__ == "__main__":
    main()
