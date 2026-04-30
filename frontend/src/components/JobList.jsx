import { useState, useEffect } from "react";
import { listJobs } from "../api/rfpClient";

const STATUS_CLASS = {
  pending:    "badge badge--pending",
  processing: "badge badge--processing",
  completed:  "badge badge--completed",
  failed:     "badge badge--failed",
};

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

/**
 * JobList — table of all submitted RFP jobs.
 * Props:
 *   onSelectJob(jobId) — called when a row is clicked.
 *   onUpload()         — called when "Upload RFP" CTA is clicked on empty state.
 */
export default function JobList({ onSelectJob, onUpload }) {
  const [jobs, setJobs]       = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  async function fetchJobs() {
    setLoading(true);
    setError(null);
    try {
      setJobs(await listJobs());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchJobs(); }, []);

  return (
    <div>
      <div className="list-toolbar">
        <div>
          <p className="page-heading">Submitted Jobs</p>
          {!loading && !error && (
            <p className="page-subheading">
              {jobs.length} job{jobs.length !== 1 ? "s" : ""} &mdash; click a row to view results
            </p>
          )}
        </div>
        <button className="btn btn-ghost" onClick={fetchJobs} disabled={loading}>
          &#8635; Refresh
        </button>
      </div>

      {loading && (
        <div className="loading-row">Loading jobs&hellip;</div>
      )}

      {error && (
        <div className="alert alert--error" role="alert">
          <span className="alert__icon">&#9888;</span>
          <div className="alert__body">{error}</div>
        </div>
      )}

      {!loading && !error && jobs.length === 0 && (
        <div className="empty-state">
          <span className="empty-state__icon">&#128196;</span>
          <p className="empty-state__title">No jobs yet</p>
          <p className="empty-state__body">
            Upload an RFP document to get started.{" "}
            <button
              className="btn-back"
              onClick={onUpload}
              style={{ display: "inline", fontSize: "inherit" }}
            >
              Upload now
            </button>
          </p>
        </div>
      )}

      {!loading && jobs.length > 0 && (
        <div className="job-table-wrap">
          <table className="job-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Filename</th>
                <th>Type</th>
                <th>Status</th>
                <th>Submitted</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {jobs.map((job, index) => (
                <tr
                  key={job.id}
                  className="job-table__row"
                  onClick={() => onSelectJob(job.id)}
                  tabIndex={0}
                  onKeyDown={(e) => e.key === "Enter" && onSelectJob(job.id)}
                  role="button"
                  aria-label={`View results for ${job.original_filename}`}
                >
                  <td>
                    <span className="job-id-mono">#{jobs.length - index}</span>
                  </td>
                  <td className="job-table__filename">{job.original_filename}</td>
                  <td>
                    <span className="badge badge--type">
                      {job.file_type.toUpperCase()}
                    </span>
                  </td>
                  <td>
                    <span className={STATUS_CLASS[job.status] ?? "badge"}>
                      {job.status}
                    </span>
                  </td>
                  <td>{formatDate(job.created_at)}</td>
                  <td className="job-table__chevron">&#8250;</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
