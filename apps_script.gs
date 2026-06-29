/**
 * Preference Ranking — Apps Script webhook backend.
 *
 * Paste this file into your Google Sheet's Apps Script editor and deploy
 * it as a Web App (see trainer_app/README.md → "No-GCP setup").
 *
 * It handles two payload "types":
 *   - "exercise" (default when missing): appends one row to the
 *     "Submissions" sheet — same behavior as before.
 *   - "quiz":  appends one row to a quiz sheet and enables a GET-based
 *     lookup so the Streamlit app can ask "has email X already finished
 *     this quiz?" before letting a trainer retake it.
 *
 *     Quiz routing is by `quiz_id`:
 *       - "general_v1"            → "QuizSubmissionsGeneral" sheet
 *                                   (status action: quiz_status_general)
 *       - anything else / blank   → "QuizSubmissions" sheet (the original
 *                                   code/math quiz; status action: quiz_status)
 *     The original code-quiz sheet, header, and status function are
 *     UNCHANGED — the general-purpose quiz is fully isolated in its own
 *     sheet so existing data and tests are never touched.
 *
 * On first deploy Apps Script will ask you to authorize:
 *   - "See, edit, create, and delete your spreadsheets in Google Drive"
 * That permission is scoped only to YOUR sheets (because the script is
 * bound to this one sheet).
 *
 * When you edit this file you MUST redeploy:
 *   Deploy → Manage deployments → ✏ Edit → Version: New version → Deploy.
 */

const SHEET_NAME = "Submissions";
const QUIZ_SHEET_NAME = "QuizSubmissions";
// General-purpose quiz lives in its own sheet so the original quiz flow is
// never modified.
const QUIZ_GENERAL_SHEET_NAME = "QuizSubmissionsGeneral";
const QUIZ_GENERAL_ID = "general_v1";

const HEADER = [
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
];

const QUIZ_HEADER = [
  "submission_id",
  "timestamp_utc",
  "trainer_name",
  "trainer_email",
  "total_score",
  "max_score",
  "elapsed_seconds",
  "quiz_version",
  "answers_json",
];

/**
 * Entry point. Apps Script automatically calls this on every POST to the
 * deployed web-app URL. The Streamlit app's storage layer hits this URL.
 */
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    if (payload && payload.type === "quiz") {
      if (payload.quiz_id === QUIZ_GENERAL_ID) {
        const sheet = _getOrCreateSheet(QUIZ_GENERAL_SHEET_NAME, QUIZ_HEADER);
        sheet.appendRow(_flattenQuiz(payload));
      } else {
        const sheet = _getOrCreateSheet(QUIZ_SHEET_NAME, QUIZ_HEADER);
        sheet.appendRow(_flattenQuiz(payload));
      }
    } else {
      const sheet = _getOrCreateSheet(SHEET_NAME, HEADER);
      sheet.appendRow(_flattenExercise(payload));
    }
    return _json({ ok: true });
  } catch (err) {
    return _json({ ok: false, error: String(err) });
  }
}

/**
 * GET handler.
 *
 *   - With no params (or just visiting the URL in a browser): a friendly
 *     message confirming the deployment works.
 *   - With ?action=quiz_status&email=...: returns the most recent
 *     QuizSubmissions (code quiz) row for that email.
 *   - With ?action=quiz_status_general&email=...: same, for the
 *     QuizSubmissionsGeneral (general-purpose quiz) sheet.
 *   Each returns { completed: true, score, max_score, timestamp,
 *   trainer_name, answers } or { completed: false } if no row exists.
 */
function doGet(e) {
  try {
    const params = (e && e.parameter) || {};
    if (params.action === "quiz_status") {
      return _json(_quizStatusForEmail(params.email || ""));
    }
    if (params.action === "quiz_status_general") {
      return _json(_quizStatusForSheet(QUIZ_GENERAL_SHEET_NAME, params.email || ""));
    }
    return ContentService
      .createTextOutput("Preference Ranking webhook is live. POST JSON to submit.")
      .setMimeType(ContentService.MimeType.TEXT);
  } catch (err) {
    return _json({ ok: false, error: String(err) });
  }
}

/**
 * Original code-quiz status lookup — reads the QuizSubmissions sheet.
 * Kept exactly as before so the existing quiz is untouched.
 */
function _quizStatusForEmail(emailRaw) {
  return _quizStatusForSheet(QUIZ_SHEET_NAME, emailRaw);
}

/**
 * Generic per-email completion lookup for any quiz sheet (same row shape:
 * QUIZ_HEADER). Returns the most recent matching row for the email.
 */
function _quizStatusForSheet(sheetName, emailRaw) {
  const email = String(emailRaw || "").trim().toLowerCase();
  if (!email) return { completed: false };

  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const sheet = ss.getSheetByName(sheetName);
  if (!sheet || sheet.getLastRow() < 2) return { completed: false };

  const values = sheet.getDataRange().getValues();
  const header = values[0];
  const emailCol = header.indexOf("trainer_email");
  if (emailCol === -1) return { completed: false };

  // Walk from bottom up so we return the most recent matching row.
  for (let i = values.length - 1; i >= 1; i--) {
    const row = values[i];
    const cellEmail = String(row[emailCol] || "").trim().toLowerCase();
    if (cellEmail === email) {
      const record = {};
      for (let j = 0; j < header.length; j++) record[header[j]] = row[j];
      let answers = {};
      try {
        answers = JSON.parse(record.answers_json || "{}");
      } catch (_) {
        answers = {};
      }
      return {
        completed: true,
        score: record.total_score,
        max_score: record.max_score,
        timestamp: record.timestamp_utc,
        trainer_name: record.trainer_name,
        answers: answers,
      };
    }
  }
  return { completed: false };
}

function _getOrCreateSheet(name, header) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);
  if (!sheet) {
    sheet = ss.insertSheet(name);
    sheet.appendRow(header);
    sheet.getRange(1, 1, 1, header.length).setFontWeight("bold");
    sheet.setFrozenRows(1);
  } else if (sheet.getLastRow() === 0) {
    sheet.appendRow(header);
    sheet.getRange(1, 1, 1, header.length).setFontWeight("bold");
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function _flattenExercise(p) {
  const r = p.ratings || {};
  const ra = r.A || {}, rb = r.B || {}, rc = r.C || {};
  const pairs = p.pairs || {};
  return [
    p.submission_id || "",
    p.timestamp_utc || "",
    p.trainer_name || "",
    p.trainer_email || "",
    p.task_id || "",
    ra.following || "", ra.concision || "", ra.concision_dir || "", ra.truthful || "", ra.satisfaction || "",
    rb.following || "", rb.concision || "", rb.concision_dir || "", rb.truthful || "", rb.satisfaction || "",
    rc.following || "", rc.concision || "", rc.concision_dir || "", rc.truthful || "", rc.satisfaction || "",
    pairs.B_vs_A || "",
    pairs.C_vs_A || "",
    pairs.C_vs_B || "",
    p.overall_comment || "",
    p.elapsed_seconds || "",
  ];
}

function _flattenQuiz(p) {
  const answers = p.answers || {};
  const correctness = p.correctness || {};
  const blob = JSON.stringify({ answers: answers, correctness: correctness });
  return [
    p.submission_id || "",
    p.timestamp_utc || "",
    p.trainer_name || "",
    p.trainer_email || "",
    p.total_score != null ? p.total_score : "",
    p.max_score != null ? p.max_score : "",
    p.elapsed_seconds != null ? p.elapsed_seconds : "",
    p.quiz_version || "",
    blob,
  ];
}

function _json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
