"""
Quick sanity check for your Apps Script webhook.

Reads the URL from .streamlit/secrets.toml, POSTs a tiny diagnostic payload,
and tells you exactly what went wrong if anything fails.

Usage:
    python test_webhook.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _read_url() -> str | None:
    secrets = Path(__file__).parent / ".streamlit" / "secrets.toml"
    if not secrets.exists():
        print(f"[!] {secrets} does not exist.")
        return None
    try:
        # Python 3.11+ has tomllib; older versions need tomli (not installed).
        try:
            import tomllib  # type: ignore
            data = tomllib.loads(secrets.read_text())
        except ImportError:
            # Fallback: super-simple regex parser for our specific format
            import re
            text = secrets.read_text()
            m = re.search(r'^\s*url\s*=\s*"([^"]+)"', text, re.MULTILINE)
            if not m:
                print("[!] Could not parse url from secrets.toml.")
                return None
            return m.group(1)
        return data.get("webhook", {}).get("url")
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Failed to read secrets.toml: {exc}")
        return None


def main() -> None:
    url = _read_url()
    if not url:
        print("[!] No webhook URL configured.")
        sys.exit(1)

    print(f"[i] URL on disk: {url}")
    if "PASTE_DEPLOYMENT_ID_HERE" in url:
        print("[!] URL is still the placeholder. Save your edits to secrets.toml.")
        sys.exit(1)
    if not url.startswith("https://script.google.com/macros/s/"):
        print("[!] URL doesn't look like an Apps Script web-app URL. "
              "Expected https://script.google.com/macros/s/.../exec")
        sys.exit(1)
    if not url.rstrip("/").endswith("/exec"):
        print("[!] URL should end with '/exec' (you might have copied the editor URL by mistake).")
        sys.exit(1)

    payload = {
        "submission_id": "test-webhook",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "trainer_name": "Webhook test",
        "trainer_email": "",
        "task_id": "diagnostic",
        "ratings": {x: {"following": "", "concision": "", "concision_dir": "",
                        "truthful": "", "satisfaction": ""} for x in "ABC"},
        "pairs": {"B_vs_A": "", "C_vs_A": "", "C_vs_B": ""},
        "overall_comment": "diagnostic ping",
        "elapsed_seconds": 0,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    def _send(request):
        return urllib.request.urlopen(request, timeout=30)

    try:
        resp = _send(req)
        text = resp.read().decode("utf-8", errors="replace")
        code = resp.getcode()
    except urllib.error.HTTPError as exc:
        if exc.code in (301, 302, 303, 307, 308) and exc.headers.get("Location"):
            new_url = exc.headers["Location"]
            print(f"[i] Following redirect to {new_url[:80]}...")
            req2 = urllib.request.Request(
                new_url, data=body,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            try:
                resp = _send(req2)
                text = resp.read().decode("utf-8", errors="replace")
                code = resp.getcode()
            except urllib.error.HTTPError as exc2:
                code = exc2.code
                text = exc2.read().decode("utf-8", errors="replace")[:200]
                print(f"[!] HTTP {code} after redirect.")
                _diagnose(code, text); sys.exit(1)
        else:
            code = exc.code
            text = exc.read().decode("utf-8", errors="replace")[:200]
            print(f"[!] HTTP {code}: {exc.reason}")
            _diagnose(code, text); sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        print(f"[!] Unreachable: {exc}")
        sys.exit(1)

    print(f"[i] HTTP {code}")
    print(f"[i] Response body (first 300 chars): {text[:300]!r}")
    try:
        parsed = json.loads(text)
        if parsed.get("ok"):
            print("\n[OK] Webhook accepted the payload.")
            print("     Open your Google Sheet -- there should be a row with "
                  "trainer_name='Webhook test'. You can delete it.")
            return
        print(f"[!] Apps Script returned ok=false: {parsed.get('error')}")
        sys.exit(1)
    except json.JSONDecodeError:
        print("[!] Response wasn't JSON. The Apps Script handler may not be deployed correctly,")
        print("    or you copied the editor URL instead of the deployment URL.")
        sys.exit(1)


def _diagnose(code: int, body: str) -> None:
    if code == 403:
        print()
        print("  CAUSE: Apps Script deployment 'Who has access' is too restrictive.")
        print("  FIX:   In the Apps Script editor:")
        print("           Deploy -> Manage deployments -> edit existing deployment ->")
        print("           Set 'Who has access' to 'Anyone' (means anyone with the URL).")
        print("           Choose 'Version: New version' and Deploy again.")
    elif code == 404:
        print()
        print("  CAUSE: The deployment URL is wrong or the deployment was deleted.")
        print("  FIX:   Open the Apps Script editor, Deploy -> Manage deployments,")
        print("         copy the active web-app URL and paste it into secrets.toml.")
    elif code == 401:
        print()
        print("  CAUSE: The deployment requires Google sign-in.")
        print("  FIX:   Set 'Who has access' to 'Anyone' (not 'Anyone with Google account').")
    elif code == 405:
        print()
        print("  CAUSE: doPost is not exported by the script, or the deployment is stale.")
        print("  FIX:   Ensure apps_script.gs is pasted in full (it must define doPost(e)),")
        print("         save it, then Deploy -> Manage deployments -> New version.")


if __name__ == "__main__":
    main()
