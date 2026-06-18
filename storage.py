"""
Submission storage with three backends, tried in priority order:

  1. Apps Script webhook (recommended when you can't create a GCP project).
     Configured by setting [webhook] url in .streamlit/secrets.toml.

  2. Google Sheets via service account (gspread).
     Configured by adding the service-account JSON under
     [gcp_service_account] in .streamlit/secrets.toml and the target
     sheet key under [sheet].

  3. Local JSON files (default fallback).
     One JSON file per submission written to ./submissions/.

The same `save_submission` function is used by the app regardless of
the active backend.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st


SUBMISSIONS_DIR = Path(__file__).parent / "submissions"
SUBMISSIONS_DIR.mkdir(exist_ok=True)


_SECRETS_PATHS = (
    Path.home() / ".streamlit" / "secrets.toml",
    Path(__file__).parent / ".streamlit" / "secrets.toml",
)


def _secrets_file_exists() -> bool:
    return any(p.exists() for p in _SECRETS_PATHS)


def _safe_get_secret(*keys: str, default=None):
    """Read a nested secret without raising when secrets.toml is absent.

    Streamlit shows a yellow warning banner in the UI as soon as anything
    touches `st.secrets` while no secrets.toml exists -- even if the access
    is wrapped in try/except. So we skip the lookup entirely in that case.
    """
    if not _secrets_file_exists():
        return default
    try:
        cursor: Any = st.secrets
        for k in keys:
            if k not in cursor:
                return default
            cursor = cursor[k]
        return cursor
    except Exception:  # noqa: BLE001
        return default


# -----------------------------------------------------------------------------
# Backend 1: Apps Script webhook (no GCP project required)
# -----------------------------------------------------------------------------

def _webhook_url() -> str | None:
    url = _safe_get_secret("webhook", "url")
    if isinstance(url, str) and (url.startswith("https://") or url.startswith("http://")):
        # Reject the placeholder from secrets.toml.example
        if "PASTE_DEPLOYMENT_ID_HERE" in url:
            return None
        return url
    return None


def _post_to_webhook(url: str, payload: dict[str, Any]) -> tuple[bool, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    # Apps Script web-apps redirect to googleusercontent.com on POST; urllib's
    # default redirect handler converts the POST into a GET, which loses the
    # body and returns 405. The standard fix is to do a manual two-step:
    # POST -> read Location -> follow with another POST.
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        # 302 redirect → follow manually with another POST.
        if exc.code in (301, 302, 303, 307, 308) and exc.headers.get("Location"):
            new_url = exc.headers["Location"]
            req2 = urllib.request.Request(
                new_url, data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req2, timeout=20) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
            except Exception as exc2:  # noqa: BLE001
                return False, f"Webhook redirect failed: {exc2}"
        else:
            return False, f"Webhook HTTP {exc.code}: {exc.reason}"
    except (urllib.error.URLError, TimeoutError) as exc:
        return False, f"Webhook unreachable: {exc}"
    except Exception as exc:  # noqa: BLE001
        return False, f"Webhook error: {exc}"

    try:
        parsed = json.loads(text)
        if parsed.get("ok"):
            return True, "ok"
        return False, f"backend error: {parsed.get('error', text[:200])}"
    except json.JSONDecodeError:
        if "ok" in text.lower():
            return True, "ok"
        return False, f"unexpected response: {text[:200]}"


# -----------------------------------------------------------------------------
# Backend 2: Google Sheets API via service account
# -----------------------------------------------------------------------------

def _sheets_client():
    """Return a (worksheet, available) pair. (None, False) if not configured."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None, False

    if not (_safe_get_secret("gcp_service_account") and _safe_get_secret("sheet")):
        return None, False

    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        client = gspread.authorize(creds)
        sheet_key = st.secrets["sheet"]["key"]
        worksheet_name = st.secrets["sheet"].get("worksheet", "Submissions")
        spreadsheet = client.open_by_key(sheet_key)
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=26
            )
            worksheet.append_row(_header_row())
        return worksheet, True
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Google Sheets backend unavailable: {exc}")
        return None, False


def _header_row() -> list[str]:
    return [
        "submission_id",
        "timestamp_utc",
        "trainer_name",
        "trainer_email",
        "task_id",
        "A_following", "A_concision", "A_concision_dir", "A_truthful", "A_satisfaction",
        "B_following", "B_concision", "B_concision_dir", "B_truthful", "B_satisfaction",
        "C_following", "C_concision", "C_concision_dir", "C_truthful", "C_satisfaction",
        "pair_B_vs_A",
        "pair_C_vs_A",
        "pair_C_vs_B",
        "overall_comment",
        "elapsed_seconds",
    ]


QUIZ_HEADER: list[str] = [
    "submission_id",
    "timestamp_utc",
    "trainer_name",
    "trainer_email",
    "total_score",
    "max_score",
    "elapsed_seconds",
    "quiz_version",
    "answers_json",
]


def _flatten_quiz_for_sheet(payload: dict[str, Any]) -> list[Any]:
    return [
        payload["submission_id"],
        payload["timestamp_utc"],
        payload.get("trainer_name", ""),
        payload.get("trainer_email", ""),
        payload.get("total_score", ""),
        payload.get("max_score", ""),
        payload.get("elapsed_seconds", ""),
        payload.get("quiz_version", ""),
        json.dumps(
            {
                "answers": payload.get("answers", {}),
                "correctness": payload.get("correctness", {}),
            },
            ensure_ascii=False,
        ),
    ]


def _flatten_for_sheet(payload: dict[str, Any]) -> list[Any]:
    r = payload["ratings"]
    p = payload["pairs"]
    return [
        payload["submission_id"],
        payload["timestamp_utc"],
        payload["trainer_name"],
        payload["trainer_email"],
        payload["task_id"],
        r["A"]["following"], r["A"]["concision"], r["A"]["concision_dir"], r["A"]["truthful"], r["A"]["satisfaction"],
        r["B"]["following"], r["B"]["concision"], r["B"]["concision_dir"], r["B"]["truthful"], r["B"]["satisfaction"],
        r["C"]["following"], r["C"]["concision"], r["C"]["concision_dir"], r["C"]["truthful"], r["C"]["satisfaction"],
        p["B_vs_A"],
        p["C_vs_A"],
        p["C_vs_B"],
        payload["overall_comment"],
        payload.get("elapsed_seconds", ""),
    ]


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def save_submission(payload: dict[str, Any]) -> tuple[bool, str, str]:
    """Persist a submission. Returns (success, message, submission_id).

    A local JSON copy is ALWAYS written first as a safety net before any
    remote backend is attempted. That way the trainer's work is never lost
    if the network blips or the webhook is misconfigured.

    Remote backends are tried in priority order: webhook → Sheets API.
    """
    submission_id = payload.get("submission_id") or str(uuid.uuid4())
    payload = {
        **payload,
        "submission_id": submission_id,
        "timestamp_utc": payload.get("timestamp_utc")
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    # 1) Always save local backup first.
    _write_local(payload)

    # 2) Try webhook backend.
    webhook = _webhook_url()
    if webhook:
        ok, info = _post_to_webhook(webhook, payload)
        if ok:
            return True, "Saved to Google Sheets (local backup also kept).", submission_id
        return True, (
            f"Saved locally — Google Sheets unreachable ({info}). "
            "Your work is safe; ask your trainer to retrieve it from the JSON file."
        ), submission_id

    # 3) Try Sheets API backend.
    worksheet, sheets_ok = _sheets_client()
    if sheets_ok:
        try:
            worksheet.append_row(
                _flatten_for_sheet(payload),
                value_input_option="USER_ENTERED",
            )
            return True, "Saved to Google Sheets (local backup also kept).", submission_id
        except Exception as exc:  # noqa: BLE001
            return True, (
                f"Saved locally — Google Sheets append failed ({exc}). "
                "Your work is safe."
            ), submission_id

    # 4) No remote backend configured — local file is the destination.
    return True, "Saved locally (no remote backend configured).", submission_id


def _write_local(payload: dict[str, Any]) -> Path:
    out_path = SUBMISSIONS_DIR / f"{payload['submission_id']}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path


def _write_local_quiz(payload: dict[str, Any]) -> Path:
    """Quiz local backup uses a quiz_ prefix so the admin viewer can tell them apart."""
    out_path = SUBMISSIONS_DIR / f"quiz_{payload['submission_id']}.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    return out_path


def list_local_submissions() -> list[dict[str, Any]]:
    """Read every exercise-submission JSON file in submissions/. Excludes quiz_* files."""
    rows: list[dict[str, Any]] = []
    for f in sorted(SUBMISSIONS_DIR.glob("*.json")):
        if f.name.startswith("quiz_"):
            continue
        try:
            rows.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            continue
    return rows


def list_local_quiz_submissions() -> list[dict[str, Any]]:
    """Read every quiz_*.json backup in submissions/."""
    rows: list[dict[str, Any]] = []
    for f in sorted(SUBMISSIONS_DIR.glob("quiz_*.json")):
        try:
            rows.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            continue
    return rows


# -----------------------------------------------------------------------------
# Quiz API
# -----------------------------------------------------------------------------

def save_quiz_submission(payload: dict[str, Any]) -> tuple[bool, str, str]:
    """Persist a quiz submission. Returns (success, message, submission_id).

    Same priority chain as `save_submission`: local backup first (always),
    then webhook, then Sheets API, then local-only. The payload's `type` field
    is forced to "quiz" so the Apps Script handler can route to the
    `QuizSubmissions` sheet.
    """
    submission_id = payload.get("submission_id") or str(uuid.uuid4())
    payload = {
        **payload,
        "type": "quiz",
        "submission_id": submission_id,
        "timestamp_utc": payload.get("timestamp_utc")
        or datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }

    _write_local_quiz(payload)

    webhook = _webhook_url()
    if webhook:
        ok, info = _post_to_webhook(webhook, payload)
        if ok:
            return True, "Saved quiz score to Google Sheets (local backup also kept).", submission_id
        return True, (
            f"Saved locally — Google Sheets unreachable ({info}). "
            "Your quiz lock will not be enforced until the row reaches the sheet."
        ), submission_id

    worksheet, sheets_ok = _quiz_sheets_client()
    if sheets_ok:
        try:
            worksheet.append_row(
                _flatten_quiz_for_sheet(payload),
                value_input_option="USER_ENTERED",
            )
            return True, "Saved quiz score to Google Sheets (local backup also kept).", submission_id
        except Exception as exc:  # noqa: BLE001
            return True, (
                f"Saved locally — Google Sheets append failed ({exc}). "
                "Your work is safe."
            ), submission_id

    return True, "Saved quiz score locally (no remote backend configured).", submission_id


def quiz_status_for_email(email: str) -> dict[str, Any] | None:
    """Return prior completed-quiz record for this email, or None.

    Resolution order matches `save_quiz_submission`:
      1. Webhook (GET `?action=quiz_status&email=...`).
      2. Local JSON backups in submissions/quiz_*.json.

    Returning None means "no prior completion found OR we couldn't reach the
    server". `quiz.py` treats None as "let the trainer proceed"; the lock will
    activate as soon as their submission row lands in the sheet.
    """
    email = (email or "").strip().lower()
    if not email:
        return None

    webhook = _webhook_url()
    if webhook:
        record = _get_quiz_status_from_webhook(webhook, email)
        if record is not None:
            return record
        # Webhook reachable but didn't return useful data — fall through to
        # local backups as a safety net.

    # Fallback: scan local JSON backups (only useful for single-machine runs).
    for row in list_local_quiz_submissions():
        if (row.get("trainer_email") or "").strip().lower() == email:
            return {
                "completed": True,
                "score": row.get("total_score"),
                "max_score": row.get("max_score"),
                "timestamp": row.get("timestamp_utc"),
                "trainer_name": row.get("trainer_name"),
                "answers": row.get("answers"),
            }
    return None


def _get_quiz_status_from_webhook(url: str, email: str) -> dict[str, Any] | None:
    """Issue a GET to the Apps Script web-app and return the parsed JSON.

    The Apps Script handler responds with:
      { "completed": false }                — no row found
      { "completed": true, "score": ..., "max_score": ..., "timestamp": ...,
        "trainer_name": ..., "answers": {...} }
    Returns None on any transport / parse error so the caller can decide what
    to do.
    """
    query = urllib.parse.urlencode({"action": "quiz_status", "email": email})
    full = f"{url}?{query}"
    req = urllib.request.Request(full, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308) and exc.headers.get("Location"):
            new_url = exc.headers["Location"]
            req2 = urllib.request.Request(new_url, method="GET")
            try:
                with urllib.request.urlopen(req2, timeout=15) as resp:
                    text = resp.read().decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                return None
        else:
            return None
    except (urllib.error.URLError, TimeoutError):
        return None
    except Exception:  # noqa: BLE001
        return None

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, dict):
        return None
    if not parsed.get("completed"):
        return None
    return parsed


def _quiz_sheets_client():
    """Return a (worksheet, available) pair for the QuizSubmissions tab.

    Reuses the same service-account credentials as `_sheets_client()` but
    targets a separate worksheet (configurable via secrets:
    `sheet.quiz_worksheet`, defaulting to "QuizSubmissions").
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        return None, False

    if not (_safe_get_secret("gcp_service_account") and _safe_get_secret("sheet")):
        return None, False

    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        client = gspread.authorize(creds)
        sheet_key = st.secrets["sheet"]["key"]
        worksheet_name = st.secrets["sheet"].get("quiz_worksheet", "QuizSubmissions")
        spreadsheet = client.open_by_key(sheet_key)
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=26
            )
            worksheet.append_row(QUIZ_HEADER)
        return worksheet, True
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Google Sheets (quiz) backend unavailable: {exc}")
        return None, False
