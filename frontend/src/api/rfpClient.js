/**
 * Centralised API client for all RFP Analyzer backend calls.
 * All fetch/upload logic lives here — no fetch calls in components.
 */

const BASE_URL = "/api/v1";

/**
 * Upload an RFP file and submit it for analysis.
 * Uses FormData so the browser sets the correct multipart boundary automatically.
 * Do NOT set Content-Type manually.
 *
 * @param {File} file - The file object from the file input or drop event.
 * @returns {Promise<Object>} The newly created job (status: pending).
 */
export async function uploadRFP(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE_URL}/jobs`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail ?? "Upload failed");
  }
  return res.json();
}

/**
 * Submit RFP content as plain text (JSON body).
 *
 * @param {string} title - Job title supplied by the user.
 * @param {string} text  - Full RFP content typed or pasted into the form.
 * @returns {Promise<Object>} The newly created job (status: pending).
 */
export async function submitText(title, text) {
  const res = await fetch(`${BASE_URL}/jobs/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title, text }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Submission failed" }));
    throw new Error(err.detail ?? "Submission failed");
  }
  return res.json();
}

/**
 * Fetch all submitted jobs, ordered newest first.
 *
 * @returns {Promise<Array>} List of job summary objects.
 */
export async function listJobs() {
  const res = await fetch(`${BASE_URL}/jobs`);
  if (!res.ok) throw new Error("Failed to load jobs.");
  return res.json();
}

/**
 * Fetch the full detail of a single job, including analysis results.
 *
 * @param {string} jobId - UUID string of the job to fetch.
 * @returns {Promise<Object>} Full job detail object.
 */
export async function getJob(jobId) {
  const res = await fetch(`${BASE_URL}/jobs/${jobId}`);
  if (!res.ok) throw new Error("Job not found.");
  return res.json();
}
