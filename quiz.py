"""
Quiz module — the "Part 1" knowledge quizzes, paired with the exercise mode in
`app.py`.

Two independent quiz datasets are served through this one UI engine:
  - `code`    → `quiz_data.py`         (code/math eval comprehension, code_v3)
  - `general` → `quiz_data_general.py` (general-purpose tasks, general_v1)

The active dataset is chosen by the `?set=` query param (default: `code`).
Every per-question and scalar session key is namespaced by the dataset's
`quiz_id`, and the per-email completion lock is queried/saved per `quiz_id`, so
the two quizzes never collide — a trainer can complete both, each locked
independently.

Behavior (per dataset):
  - Trainer enters name + email on the landing page (in `app.py`).
  - On entering a quiz, we GET the trainer's quiz status by email + quiz_id. If
    a completed row already exists, we show the prior score read-only and refuse
    to restart (the per-email/per-quiz completion lock).
  - Each question is a radio with `index=None`; on first click we capture the
    answer, mark the question locked, and immediately reveal the correct
    answer + rule. A locked radio is rendered with `disabled=True`.
  - When every question has been answered, "Submit" persists to the
    `QuizSubmissions` sheet (via the same webhook backend) and the lock
    activates server-side.

Streamlit state model (all namespaced by quiz_id):
  - q_{quiz_id}_{qid}_radio    — the radio widget's bound key (option_id)
  - q_{quiz_id}_{qid}_answer   — the captured option_id; written ONCE
  - q_{quiz_id}_{qid}_locked   — True once the trainer has answered

These are appended to PERSISTENT_KEYS in `app.py` so they survive reruns.
"""

from __future__ import annotations

import time
from typing import Any

import streamlit as st

import quiz_data
import quiz_data_general
from storage import save_quiz_submission, quiz_status_for_email


UNSELECTED = None  # st.radio uses None as the "nothing picked yet" sentinel.


# -----------------------------------------------------------------------------
# Dataset registry
# -----------------------------------------------------------------------------

# Maps the `?set=` query param value to its dataset module.
_QUIZ_SETS: dict[str, Any] = {
    "code": quiz_data,
    "general": quiz_data_general,
}
_DEFAULT_SET = "code"

# Human-readable banner labels per set.
_SET_LABELS: dict[str, str] = {
    "code": "Code & Math",
    "general": "General-Purpose",
}


def _resolve_set(set_name: str | None) -> str:
    """Return a valid set key, defaulting to the code quiz for unknown values."""
    return set_name if set_name in _QUIZ_SETS else _DEFAULT_SET


def _module_for(set_name: str) -> Any:
    return _QUIZ_SETS[_resolve_set(set_name)]


# -----------------------------------------------------------------------------
# Session keys (namespaced by quiz_id)
# -----------------------------------------------------------------------------

_SCALAR_NAMES = (
    "started_at",
    "submitted",
    "submission_id",
    "submission_msg",
    "final_score",
    "status_checked_for",   # email we've already checked the server for
    "prior_completion",     # dict | None — set if server returned a completed row
)


def _qid(mod: Any) -> str:
    # Fallback keeps older datasets (without an explicit quiz_id) working.
    return mod.QUIZ.get("quiz_id", "code_v3")


def _qkey(mod: Any, question_id: str, suffix: str) -> str:
    return f"q_{_qid(mod)}_{question_id}_{suffix}"


def _skey(mod: Any, name: str) -> str:
    return f"quiz_{_qid(mod)}_{name}"


def quiz_persistent_keys() -> list[str]:
    """Every quiz widget/state key (across BOTH datasets) that must survive reruns.

    Imported by app.py so the top-level `_persist_widget_state()` helper can
    re-bind these on every rerun, even when the quiz module isn't rendering.
    """
    keys: list[str] = []
    for mod in _QUIZ_SETS.values():
        for _, q in mod.iter_questions():
            keys.append(_qkey(mod, q["id"], "radio"))
            keys.append(_qkey(mod, q["id"], "answer"))
            keys.append(_qkey(mod, q["id"], "locked"))
        for name in _SCALAR_NAMES:
            keys.append(_skey(mod, name))
    return keys


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _question_locked(mod: Any, q: dict) -> bool:
    return bool(st.session_state.get(_qkey(mod, q["id"], "locked"), False))


def _question_correct(mod: Any, q: dict) -> bool | None:
    if not _question_locked(mod, q):
        return None
    return st.session_state.get(_qkey(mod, q["id"], "answer")) == q["correct"]


def _label_for(q: dict, option_id: str) -> str:
    for oid, label in q["options"]:
        if oid == option_id:
            return label
    return option_id


def _answered_count(mod: Any) -> int:
    return sum(1 for _, q in mod.iter_questions() if _question_locked(mod, q))


def _score(mod: Any) -> int:
    return sum(
        q["points"] for _, q in mod.iter_questions() if _question_correct(mod, q)
    )


def _total_items(mod: Any) -> int:
    return sum(1 for _ in mod.iter_questions())


def _all_answered(mod: Any) -> bool:
    return _answered_count(mod) == _total_items(mod)


def _block_progress(mod: Any, block: dict) -> tuple[int, int]:
    answered = sum(1 for q in block["questions"] if _question_locked(mod, q))
    return answered, len(block["questions"])


def _reset_quiz_state(mod: Any) -> None:
    """Clear every per-question key + start a fresh timer (for this dataset)."""
    for _, q in mod.iter_questions():
        for suffix in ("radio", "answer", "locked"):
            st.session_state.pop(_qkey(mod, q["id"], suffix), None)
    for name in (
        "submitted",
        "submission_id",
        "submission_msg",
        "final_score",
        "status_checked_for",
        "prior_completion",
    ):
        st.session_state.pop(_skey(mod, name), None)
    st.session_state[_skey(mod, "started_at")] = time.time()


# -----------------------------------------------------------------------------
# Per-question card
# -----------------------------------------------------------------------------

def _render_question(mod: Any, q: dict, index_in_block: int) -> None:
    locked = _question_locked(mod, q)
    qid = q["id"]
    points = q["points"]
    points_label = "2 pts" if points == 2 else "1 pt"

    st.markdown(
        f"##### {index_in_block}. `{qid}` &nbsp; *({points_label})*"
    )
    st.markdown(q["prompt"])

    options_ids = [oid for oid, _ in q["options"]]
    options_labels = {oid: label for oid, label in q["options"]}

    radio_key = _qkey(mod, qid, "radio")
    answer_key = _qkey(mod, qid, "answer")
    locked_key = _qkey(mod, qid, "locked")

    selected_id = st.radio(
        label=f"Answer for {qid}",
        options=options_ids,
        index=None,
        format_func=lambda oid: options_labels[oid],
        key=radio_key,
        disabled=locked,
        label_visibility="collapsed",
    )

    # Capture-on-first-click. The radio's bound key is radio_key; we copy
    # to answer_key once and never overwrite it, so even if Streamlit
    # rebinds the radio later the canonical answer survives.
    if selected_id is not None and not locked:
        st.session_state[answer_key] = selected_id
        st.session_state[locked_key] = True
        st.rerun()

    if locked:
        chosen = st.session_state.get(answer_key)
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

def _render_sidebar(mod: Any) -> None:
    st.sidebar.header("Quiz progress")

    answered = _answered_count(mod)
    total = _total_items(mod)
    score = _score(mod)
    max_points = mod.QUIZ["max_points"]

    st.sidebar.markdown(f"**Answered:** {answered} / {total}")
    st.sidebar.progress(answered / total if total else 0.0)
    st.sidebar.markdown(f"**Running score:** {score} / {max_points}")

    st.sidebar.divider()
    st.sidebar.markdown("**Per-block progress**")
    for block in mod.QUIZ["blocks"]:
        done, n = _block_progress(mod, block)
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
        "Each trainer can take this quiz once. If you genuinely need a "
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

def _build_payload(mod: Any) -> dict[str, Any]:
    answers: dict[str, str] = {}
    correctness: dict[str, bool] = {}
    for _, q in mod.iter_questions():
        ans = st.session_state.get(_qkey(mod, q["id"], "answer"), "")
        answers[q["id"]] = ans
        correctness[q["id"]] = (ans == q["correct"])

    score = _score(mod)
    max_points = mod.QUIZ["max_points"]
    started = st.session_state.get(_skey(mod, "started_at"), time.time())
    return {
        "type": "quiz",
        "quiz_id": _qid(mod),
        "quiz_version": mod.QUIZ["version"],
        "trainer_name": st.session_state.get("trainer_name", "").strip(),
        "trainer_email": st.session_state.get("trainer_email", "").strip(),
        "total_score": score,
        "max_score": max_points,
        "elapsed_seconds": int(time.time() - started),
        "answers": answers,
        "correctness": correctness,
    }


def _render_submit_section(mod: Any) -> None:
    st.markdown("## Finish quiz")
    answered = _answered_count(mod)
    total = _total_items(mod)

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
            ok, msg, sid = save_quiz_submission(_build_payload(mod))
        if ok:
            st.session_state[_skey(mod, "submitted")] = True
            st.session_state[_skey(mod, "submission_id")] = sid
            st.session_state[_skey(mod, "submission_msg")] = msg
            st.rerun()
        else:
            st.error(f"Submission failed: {msg}")


def _render_post_submit(mod: Any) -> None:
    """Mirrors the exercise's post-submit view in app.py — neutral and brief.

    The score, pass/fail status, and per-question correctness are deliberately
    NOT shown here. Trainers got per-question feedback inline as they took
    the quiz; the aggregate score is recorded in the QuizSubmissions sheet
    for project leads to review.
    """
    st.success("✅ Submitted successfully!")
    st.markdown(
        f"**Submission ID:** `{st.session_state.get(_skey(mod, 'submission_id'), '')}`"
    )
    st.caption(st.session_state.get(_skey(mod, "submission_msg"), ""))
    st.balloons()

    st.divider()
    st.markdown("### Done")
    st.write(
        "Your responses are saved in the project's Google Sheet. This quiz "
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


def render_quiz(set_name: str | None = None) -> None:
    """Entry point called from app.py when `?mode=quiz` (optionally `&set=`)."""
    active_set = _resolve_set(set_name)
    mod = _module_for(active_set)
    label = _SET_LABELS.get(active_set, active_set)

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

    started_key = _skey(mod, "started_at")
    if started_key not in st.session_state:
        st.session_state[started_key] = time.time()

    st.markdown(
        f'<div class="top-banner">Knowledge Quiz — {label} '
        f'(Preference Ranking)</div>',
        unsafe_allow_html=True,
    )
    st.markdown(mod.QUIZ["blurb"])
    st.caption(
        f"Trainer: **{name}** · {email} · "
        f"Quiz version **{mod.QUIZ['version']}** · "
        f"{mod.QUIZ['max_points']} points total"
    )

    # ---- one-time per-email/per-quiz lock check ------------------------------
    # Only call the backend once per email per session — repeated calls would
    # rerun on every radio click and burn quota.
    status_checked_key = _skey(mod, "status_checked_for")
    prior_key = _skey(mod, "prior_completion")
    if st.session_state.get(status_checked_key) != email:
        prior = quiz_status_for_email(email, _qid(mod))
        st.session_state[status_checked_key] = email
        st.session_state[prior_key] = (
            prior if (prior and prior.get("completed")) else None
        )

    if st.session_state.get(prior_key):
        _render_sidebar(mod)
        _show_prior_completion(st.session_state[prior_key])
        return

    # ---- post-submit view ----------------------------------------------------
    if st.session_state.get(_skey(mod, "submitted")):
        _render_sidebar(mod)
        _render_post_submit(mod)
        return

    # ---- main quiz UI --------------------------------------------------------
    _render_sidebar(mod)

    for block in mod.QUIZ["blocks"]:
        done, n = _block_progress(mod, block)
        with st.expander(
            f"{block['title']}  &nbsp; ({done}/{n})",
            expanded=True,
        ):
            if block.get("intro"):
                st.caption(block["intro"])
            for i, q in enumerate(block["questions"], start=1):
                _render_question(mod, q, i)

    _render_submit_section(mod)
