# Preference Ranking — Trainer Practice App

A Streamlit app with **two independent modes** that calibrate annotators on
the Preference Ranking project guide:

1. **Knowledge Quiz** — 33 multiple-choice / true-false items distilled from
   `Project_data/Preference_Ranking_QA_Quiz_v3.md`. Each answer freezes the
   moment it's clicked and the correct answer + rule are revealed inline.
   The quiz is **locked to one attempt per email** (server-enforced). There
   is no pass/fail threshold; the raw score lands in the sheet for later
   analysis.
2. **Grading Exercise** — the in-tool grading UI clone (see screenshots in
   `../test/`): rate three candidate responses on four dimensions + holistic
   Satisfaction, run all three pairwise comparisons, and write one
   comparative comment. Mirrors the production grading screen.

Both flows submit to a shared Google Sheet (or local JSON files when
nothing is configured). On launch trainers land on a small picker that
collects name + email once and routes to whichever mode they choose; the
URL params `?mode=quiz` and `?mode=exercise` deep-link straight to either
flow on subsequent visits.

## What's in here

```
trainer_app/
├── app.py                      # Streamlit router (landing + admin + mode dispatch)
├── quiz.py                     # Knowledge quiz UI + per-email completion gate
├── quiz_data.py                # The 33 quiz items, structured as Python data
├── tasks.py                    # The exercise task and 3 candidate responses
├── storage.py                  # Google Sheets / webhook / local JSON storage
├── apps_script.gs              # Apps Script handler for both POST and GET
├── setup_sheets.py             # Provisions BOTH the Submissions + QuizSubmissions tabs
├── test_webhook.py             # Round-trip smoke test for exercise + quiz lock
├── requirements.txt
├── .streamlit/
│   ├── config.toml             # Theme + server config
│   └── secrets.toml.example    # Template for Sheets credentials
├── submissions/                # Local fallback (gitignored). quiz_*.json = quiz backups.
└── README.md
```

## Quick start — run it locally

```bash
cd trainer_app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open <http://localhost:8501>. With no `secrets.toml`, submissions are
saved as JSON files inside `trainer_app/submissions/`.

To view local submissions, open <http://localhost:8501/?admin=1>.

## Deploy — Option 1A (RECOMMENDED, NO GCP project needed): Apps Script webhook

Use this when your organization won't let you create Google Cloud
projects. The submission backend is a tiny JavaScript snippet attached
directly to your Google Sheet — no Cloud Console, no service accounts,
no IT involvement. Total time: ~3 minutes.

### Step 1. Create the Google Sheet

1. Open <https://sheets.new>. Name it e.g. **"Preference Ranking Submissions"**.

### Step 2. Paste the Apps Script

1. In the sheet: **Extensions → Apps Script** (opens a new tab with the script editor).
2. Delete whatever boilerplate code is in `Code.gs`.
3. Open `trainer_app/apps_script.gs` from this repo, copy ALL of it, paste into the editor.
4. Press **Ctrl/Cmd + S** (save). Give the project any name.

### Step 3. Deploy it as a Web App

1. Top-right **Deploy → New deployment**.
2. Click the gear ⚙ next to "Select type" → **Web app**.
3. Fill in:
   - **Description:** anything, e.g. "Preference ranking webhook"
   - **Execute as:** *Me* (your account)
   - **Who has access:** *Anyone* (this means anyone with the URL — not searchable; you'll keep the URL secret)
4. Click **Deploy**.
5. Apps Script asks you to **Authorize access** the first time:
   - Pick your Google account
   - You may see "Google hasn't verified this app" → click **Advanced → Go to (project name) (unsafe)** → **Allow**. This is normal because the script is your own personal code; the scary warning is Google's default for unverified scripts.
6. After deploy, copy the **Web app URL**. It looks like:
   ```text
   https://script.google.com/macros/s/AKfycbz.../exec
   ```

### Step 4. Paste the URL into secrets

Create `trainer_app/.streamlit/secrets.toml` with just two lines:

```toml
[webhook]
url = "https://script.google.com/macros/s/AKfycbz.../exec"
```

### Step 5. Restart Streamlit

In the terminal running the app: **Ctrl+C**, then `streamlit run app.py`.

That's it. Submit a test entry — you should see:

> Submitted. Saved to Google Sheets via Apps Script.

And a new row in the **Submissions** tab of your sheet (the tab is
auto-created on the first submission with the header row).

### When you redeploy the Apps Script

If you ever edit `apps_script.gs` and save it, you also need to
**Deploy → Manage deployments → ✏ Edit → Version: New version → Deploy**
for the new code to take effect. The URL stays the same.

---

## Deploy — Option 1B: Streamlit Community Cloud + Google Sheet via service account

Use this if you DO have GCP project-create permissions. Time: ~15 min.

### A. Create the Google Sheet and a service account

1. Create a new Google Sheet — name it e.g. **"Preference Ranking
   Submissions"**. Copy the **sheet key** from the URL (the long string
   between `/d/` and `/edit`).
2. Go to <https://console.cloud.google.com/> → new project (or pick an
   existing one).
3. **APIs & Services → Library** → enable both:
   - Google Sheets API
   - Google Drive API
4. **APIs & Services → Credentials → Create credentials → Service
   account.** Skip the optional steps; click *Done*.
5. Click the service account you just created → **Keys → Add key →
   Create new key → JSON**. A `service-account-xxx.json` will download.
6. Back in the Google Sheet, click **Share**, paste the service
   account's email (looks like `xxx@your-project.iam.gserviceaccount.com`),
   and give it **Editor** access.

### B. Push to GitHub

```bash
cd /path/to/PreferenceRankingV5
git init      # if not already a repo
git add trainer_app
git commit -m "Add trainer practice app"
git branch -M main
git remote add origin git@github.com:<your-user>/preference-ranking-trainer.git
git push -u origin main
```

> Make sure `trainer_app/.streamlit/secrets.toml` is NOT committed —
> the included `.gitignore` already excludes it.

### C. Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io/> and sign in with GitHub.
2. **New app** → pick your repo, branch `main`, main file path
   `trainer_app/app.py`.
3. Click **Advanced settings → Secrets** and paste:

   ```toml
   [sheet]
   key = "PASTE_SHEET_KEY_HERE"
   worksheet = "Submissions"

   [gcp_service_account]
   # paste the WHOLE contents of the downloaded service-account JSON,
   # but reformatted as TOML. Use the secrets.toml.example as a template.
   ```

4. **Deploy.** Streamlit gives you a public URL like
   `https://<your-app>.streamlit.app` — send it to your trainers.

When a trainer submits, a new row appears in the sheet. You can view
everything live in the Google Sheet.

## Deploy — Option 2 (zero setup): local LAN demo

If you just want a small group on the same network to try it
right now:

```bash
streamlit run app.py --server.address 0.0.0.0
```

Then share `http://<your-laptop-ip>:8501` over your office VPN/Wi-Fi.
Submissions land in `trainer_app/submissions/*.json`. Read them with the
admin viewer (`?admin=1`) or open the JSON files directly.

## Deploy — Option 3: Hugging Face Spaces

Free alternative to Streamlit Cloud, same idea:

1. Create a new Space, SDK = **Streamlit**.
2. Push the `trainer_app/` contents to the Space repo.
3. In the Space's **Settings → Variables and secrets**, add each
   secret key (`sheet.key`, `gcp_service_account.private_key`, etc.) —
   or paste the whole TOML under "Secrets" and adapt code accordingly.

## How submissions look in the sheet

Two tabs are written to:

**`Submissions`** (one row per grading-exercise attempt):

| submission_id | timestamp_utc | trainer_name | trainer_email | task_id | A_following | A_concision | A_concision_dir | A_truthful | A_satisfaction | B_… | C_… | pair_B_vs_A | pair_C_vs_A | pair_C_vs_B | overall_comment | elapsed_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

**`QuizSubmissions`** (one row per finished quiz):

| submission_id | timestamp_utc | trainer_name | trainer_email | total_score | max_score | elapsed_seconds | quiz_version | answers_json |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

`answers_json` is a single JSON column packed with two dicts:
`{"answers": {"A1": "c", "A2": "false", …}, "correctness": {"A1": true, …}}`.
Saves the sheet from having 33 narrow columns; project leads can parse it
when they want to inspect per-question detail.

## Reviewing submissions

- **Sheets backend:** open the sheet — sort by `trainer_name` or
  filter by `timestamp_utc`. The two tabs are independent.
- **Local backend:** `streamlit run app.py` then visit `/?admin=1`,
  or just read the JSON files in `submissions/`. Quiz backups live in
  `submissions/quiz_*.json`; exercise backups have no prefix.

## Quiz lock & how to clear it

The quiz is locked to one attempt per email. When a trainer opens the
quiz, the app issues a `GET <webhook>?action=quiz_status&email=…`; if
the Apps Script handler reports a completed row, the trainer sees their
prior score and cannot retake.

To wipe a trainer's lock (e.g., they need a genuine retake), delete
their row from the `QuizSubmissions` tab. Their next visit will start a
fresh attempt.

**Known mid-quiz refresh edge case:** between page-1 and "Finish quiz",
nothing has been written to the server yet. A user who refreshes mid-quiz
starts from scratch. They lose every locked answer (and the running
score), so the cheat path is self-punishing rather than a free lookup.
The lock activates the moment they click "Finish quiz".

## Adding more tasks later

Open `tasks.py` and append another dict to `ALL_TASKS`. To let trainers
pick which task they're attempting, expose a `?task_id=…` query
parameter in `app.py` (call `get_task(st.query_params.get("task_id"))`).

## Why these 3 responses?

The task uses the PDF's canonical example:

> *"Provide example python code to draw 60 random samples without
> replacement and compute their average."*

- **Response A** is the PDF's bad reference: uses `np.random.randint`,
  which samples **with** replacement. Trainers should catch this and
  rank A lowest. (Following = Partially / Truthful = Partially or Not /
  Satisfaction = Slightly Unsatisfying.)
- **Response B** is the canonical good answer using
  `np.random.choice(..., replace=False)`. Concise, correct. Should be
  Rank 1. (Fully / Truthful / Good / Highly Satisfying.)
- **Response C** is correct (uses `random.sample`) but very verbose
  with unrequested alternative-approaches section. Rank 2.
  (Fully / Truthful / Acceptable — could have been shorter / Slightly
  Satisfying.)

If trainers rank **B > C > A**, they got it right. The `overall_comment`
should name each response and tie the ranking to **Truthfulness** (A's
sampling bug) and **Concision** (C's verbosity) — i.e. exactly the
"Good Example 2" pattern from the project guide.
