/**
 * Preference Ranking — Apps Script webhook backend.
 *
 * Paste this file into your Google Sheet's Apps Script editor and deploy
 * it as a Web App (see trainer_app/README.md → "No-GCP setup").
 *
 * It accepts POST requests with a JSON body matching the payload built
 * by storage._build_payload() in the Streamlit app, and appends one row
 * to the active spreadsheet's "Submissions" sheet.
 *
 * On first deploy Apps Script will ask you to authorize:
 *   - "See, edit, create, and delete your spreadsheets in Google Drive"
 * That permission is scoped only to YOUR sheets (because the script is
 * bound to this one sheet).
 */

const SHEET_NAME = "Submissions";

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

/**
 * Entry point. Apps Script automatically calls this on every POST to the
 * deployed web-app URL. The Streamlit app's storage layer hits this URL.
 */
function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents);
    const sheet = _getOrCreateSheet();
    sheet.appendRow(_flatten(payload));
    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/** GET handler — visiting the URL in a browser confirms the deploy worked. */
function doGet() {
  return ContentService
    .createTextOutput("Preference Ranking webhook is live. POST JSON to submit.")
    .setMimeType(ContentService.MimeType.TEXT);
}

function _getOrCreateSheet() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = ss.insertSheet(SHEET_NAME);
    sheet.appendRow(HEADER);
    sheet.getRange(1, 1, 1, HEADER.length).setFontWeight("bold");
    sheet.setFrozenRows(1);
  } else if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADER);
    sheet.getRange(1, 1, 1, HEADER.length).setFontWeight("bold");
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function _flatten(p) {
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
