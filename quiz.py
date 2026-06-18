"""
Quiz module — the "Part 1" knowledge quiz, paired with the exercise mode in
`app.py`.

Behavior (Option B from the plan):
  - Trainer enters name + email on the landing page (in `app.py`).
  - On entering the quiz, we GET the trainer's quiz status by email. If a
    completed row already exists, we show the prior score read-only and refuse
    to restart (the per-email completion lock).
  - Each question is a radio with `index=None`; on first click we capture the
    answer, mark the question locked, and immediately reveal the correct
    answer + rule. A locked radio is rendered with `disabled=True` so the
    trainer can't change their pick.
  - When every question has been answered, "Finish quiz" submits to the
    `QuizSubmissions` sheet (via the same webhook backend) and the lock
    activates server-side.

Streamlit state model:
  - q{id}_radio    — the radio widget's bound key (the option_id selected)
  - q{id}_answer   — the captured option_id; written ONCE on first click
  - q{id}_locked   — True once the trainer has answered

These are appended to PERSISTENT_KEYS in `app.py` so they survive reruns.
"""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

from quiz_data import QUIZ, iter_questions
from storage import save_quiz_submission, quiz_status_for_email


UNSELECTED = None  # st.radio uses None as the "nothing picked yet" sentinel.


# -----------------------------------------------------------------------------
# Session keys
# -----------------------------------------------------------------------------

def quiz_persistent_keys() -> list[str]:
    """Every quiz widget/state key that must survive Streamlit reruns.

    Imported by app.py so the top-level `_persist_widget_state()` helper can
    re-bind these on every rerun, even when the quiz module isn't rendering.
    """
    keys: list[str] = []
    for _, q in iter_questions():
        keys.append(f"q{q['id']}_radio")
        keys.append(f"q{q['id']}_answer")
        keys.append(f"q{q['id']}_locked")
    keys += [
        "quiz_started_at",
        "quiz_submitted",
        "quiz_submission_id",
        "quiz_submission_msg",
        "quiz_final_score",
        "quiz_status_checked_for",  # email we've already checked the server for
        "quiz_prior_completion",    # dict | None — set if server returned a completed row
    ]
    return keys


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _question_locked(q: dict) -> bool:
    return bool(st.session_state.get(f"q{q['id']}_locked", False))


def _question_correct(q: dict) -> bool | None:
    if not _question_locked(q):
        return None
    return st.session_state.get(f"q{q['id']}_answer") == q["correct"]


def _label_for(q: dict, option_id: str) -> str:
    for oid, label in q["options"]:
        if oid == option_id:
            return label
    return option_id


def _answered_count() -> int:
    return sum(1 for _, q in iter_questions() if _question_locked(q))


def _score() -> int:
    return sum(q["points"] for _, q in iter_questions() if _question_correct(q))


def _all_answered() -> bool:
    return _answered_count() == sum(1 for _ in iter_questions())


def _block_progress(block: dict) -> tuple[int, int]:
    answered = sum(1 for q in block["questions"] if _question_locked(q))
    return answered, len(block["questions"])


def _reset_quiz_state() -> None:
    """Clear every per-question key + start a fresh timer."""
    for _, q in iter_questions():
        for suffix in ("radio", "answer", "locked"):
            st.session_state.pop(f"q{q['id']}_{suffix}", None)
    for k in (
        "quiz_submitted",
        "quiz_submission_id",
        "quiz_submission_msg",
        "quiz_final_score",
        "quiz_status_checked_for",
        "quiz_prior_completion",
    ):
        st.session_state.pop(k, None)
    st.session_state.quiz_started_at = time.time()


# -----------------------------------------------------------------------------
# Per-question card
# -----------------------------------------------------------------------------

def _render_question(q: dict, index_in_block: int) -> None:
    locked = _question_locked(q)
    qid = q["id"]
    points = q["points"]
    points_label = "2 pts" if points == 2 else "1 pt"

    st.markdown(
        f"##### {index_in_block}. `{qid}` &nbsp; *({points_label})*"
    )
    st.markdown(q["prompt"])

    options_ids = [oid for oid, _ in q["options"]]
    options_labels = {oid: label for oid, label in q["options"]}

    selected_id = st.radio(
        label=f"Answer for {qid}",
        options=options_ids,
        index=None,
        format_func=lambda oid: options_labels[oid],
        key=f"q{qid}_radio",
        disabled=locked,
        label_visibility="collapsed",
    )

    # Capture-on-first-click. The radio's bound key is q{qid}_radio; we copy
    # to q{qid}_answer once and never overwrite it, so even if Streamlit
    # rebinds the radio later the canonical answer survives.
    if selected_id is not None and not locked:
        st.session_state[f"q{qid}_answer"] = selected_id
        st.session_state[f"q{qid}_locked"] = True
        st.rerun()

    if locked:
        chosen = st.session_state.get(f"q{qid}_answer")
        correct = q["correct"]
        is_right = chosen == correct
        header = (
            f"✅ Correct &nbsp;—&nbsp; **{_label_for(q, correct)}**"
            if is_right
            else (
                f"❌ Incorrect &nbsp;—&nbsp; your answer: "
                f"**{_label_for(q, chosen) if chosen else '—'}**  \n"
                f"Correct answer: **{_label_for(q, correct)}**"
            )
        )
        (st.success if is_right else st.error)(header)
        # The rule renders inline (not in an inner expander) because
        # Streamlit forbids expanders inside expanders. The rule is the
        # whole pedagogical point of the quiz, so always-visible is fine.
        st.markdown(q["rule"])

    st.divider()


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------

def _render_sidebar() -> None:
    st.sidebar.header("Quiz progress")

    answered = _answered_count()
    total = sum(1 for _ in iter_questions())
    score = _score()
    max_points = QUIZ["max_points"]

    st.sidebar.markdown(f"**Answered:** {answered} / {total}")
    st.sidebar.progress(answered / total if total else 0.0)
    st.sidebar.markdown(f"**Running score:** {score} / {max_points}")

    st.sidebar.divider()
    st.sidebar.markdown("**Per-block progress**")
    for block in QUIZ["blocks"]:
        done, n = _block_progress(block)
        marker = "✅" if done == n else ("▶︎" if done > 0 else "◯")
        st.sidebar.markdown(
            f"{marker} &nbsp; **{block['id']}** &nbsp; {done}/{n}",
            unsafe_allow_html=True,
        )

    st.sidebar.divider()
    if st.sidebar.button(
        "← Back to home",
        key="quiz_sidebar_back_home",
        use_container_width=True,
    ):
        st.query_params.clear()
        st.rerun()


# -----------------------------------------------------------------------------
# Completion gate
# -----------------------------------------------------------------------------

def _show_prior_completion(prior: dict) -> None:
    """Render a read-only banner when this email has already finished the quiz."""
    ts = prior.get("timestamp", "")
    name = prior.get("trainer_name", "")

    st.success(
        f"You have already completed this quiz.  \n"
        f"**Trainer:** {name or '—'}  \n"
        f"**Submitted:** {ts or '—'}"
    )
    st.info(
        "Each trainer can take the quiz once. If you genuinely need a "
        "retake, ask the project lead to delete your row from the "
        "`QuizSubmissions` sheet."
    )

    if st.button(
        "← Back to home",
        key="quiz_prior_back_home",
        use_container_width=True,
    ):
        st.query_params.clear()
        st.rerun()


# -----------------------------------------------------------------------------
# Submit
# -----------------------------------------------------------------------------

def _build_payload() -> dict[str, Any]:
    answers: dict[str, str] = {}
    correctness: dict[str, bool] = {}
    for _, q in iter_questions():
        ans = st.session_state.get(f"q{q['id']}_answer", "")
        answers[q["id"]] = ans
        correctness[q["id"]] = (ans == q["correct"])

    score = _score()
    max_points = QUIZ["max_points"]
    started = st.session_state.get("quiz_started_at", time.time())
    return {
        "type": "quiz",
        "quiz_version": QUIZ["version"],
        "trainer_name": st.session_state.get("trainer_name", "").strip(),
        "trainer_email": st.session_state.get("trainer_email", "").strip(),
        "total_score": score,
        "max_score": max_points,
        "elapsed_seconds": int(time.time() - started),
        "answers": answers,
        "correctness": correctness,
    }


def _render_submit_section() -> None:
    st.markdown("## Finish quiz")
    answered = _answered_count()
    total = sum(1 for _ in iter_questions())

    if answered < total:
        st.warning(
            f"You've answered {answered} of {total} questions. "
            f"Finish the remaining {total - answered} before submitting."
        )

    disabled = answered < total
    if st.button(
        "Submit",
        type="primary",
        disabled=disabled,
        use_container_width=True,
    ):
        with st.spinner(
            "Submitting… this can take a few seconds while we save to "
            "Google Sheets."
        ):
            ok, msg, sid = save_quiz_submission(_build_payload())
        if ok:
            st.session_state.quiz_submitted = True
            st.session_state.quiz_submission_id = sid
            st.session_state.quiz_submission_msg = msg
            st.rerun()
        else:
            st.error(f"Submission failed: {msg}")


def _render_post_submit() -> None:
    """Mirrors the exercise's post-submit view in app.py — neutral and brief.

    The score, pass/fail status, and per-question correctness are deliberately
    NOT shown here. Trainers got per-question feedback inline as they took
    the quiz; the aggregate score is recorded in the QuizSubmissions sheet
    for project leads to review.
    """
    st.success("✅ Submitted successfully!")
    st.markdown(
        f"**Submission ID:** `{st.session_state.get('quiz_submission_id', '')}`"
    )
    st.caption(st.session_state.get("quiz_submission_msg", ""))
    st.balloons()

    st.divider()
    st.markdown("### Done")
    st.write(
        "Your responses are saved in the project's Google Sheet. The quiz "
        "is now locked for this email; ask the project lead if you need a "
        "genuine retake."
    )
    if st.button(
        "← Back to home",
        key="quiz_post_back_home",
        use_container_width=True,
    ):
        st.query_params.clear()
        st.rerun()


# -----------------------------------------------------------------------------
# Public entry point
# -----------------------------------------------------------------------------

def _is_valid_turing_email(email: str) -> bool:
    """Mirror of the validator in app.py.

    Deliberately duplicated (not imported) because on Streamlit Cloud the
    script runs as `__main__` and `from app import ...` would re-execute
    app.py as a fresh module, triggering a second `st.set_page_config()`.
    """
    e = (email or "").strip().lower()
    return e.endswith("@turing.com") and len(e) > len("@turing.com")


def render_quiz() -> None:
    """Entry point called from app.py when `?mode=quiz`."""
    email = (st.session_state.get("trainer_email") or "").strip()
    name = (st.session_state.get("trainer_name") or "").strip()
    if not name or not email or not _is_valid_turing_email(email):
        st.warning(
            "Please go back to the home page and enter your name + a "
            "@turing.com email before starting the quiz."
        )
        if st.button("← Back to home", key="quiz_gate_back_home"):
            st.query_params.clear()
            st.rerun()
        return

    if "quiz_started_at" not in st.session_state:
        st.session_state.quiz_started_at = time.time()

    st.markdown(
        '<div class="top-banner">Knowledge Quiz — Preference Ranking v3</div>',
        unsafe_allow_html=True,
    )
    st.markdown(QUIZ["blurb"])
    st.caption(
        f"Trainer: **{name}** · {email} · "
        f"Quiz version **{QUIZ['version']}** · {QUIZ['max_points']} points total"
    )

    # ---- one-time per-email lock check ---------------------------------------
    # Only call the backend once per email per session — repeated calls would
    # rerun on every radio click and burn quota.
    if st.session_state.get("quiz_status_checked_for") != email:
        prior = quiz_status_for_email(email)
        st.session_state.quiz_status_checked_for = email
        st.session_state.quiz_prior_completion = (
            prior if (prior and prior.get("completed")) else None
        )

    if st.session_state.get("quiz_prior_completion"):
        _render_sidebar()
        _show_prior_completion(st.session_state["quiz_prior_completion"])
        return

    # ---- post-submit view ----------------------------------------------------
    if st.session_state.get("quiz_submitted"):
        _render_sidebar()
        _render_post_submit()
        return

    # ---- main quiz UI --------------------------------------------------------
    _render_sidebar()

    for block in QUIZ["blocks"]:
        done, n = _block_progress(block)
        with st.expander(
            f"{block['title']}  &nbsp; ({done}/{n})",
            expanded=True,
        ):
            if block.get("intro"):
                st.caption(block["intro"])
            for i, q in enumerate(block["questions"], start=1):
                _render_question(q, i)

    _render_submit_section()
