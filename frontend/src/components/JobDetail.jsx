import { useState, useEffect, useRef } from "react";
import { getJob } from "../api/rfpClient";

const POLL_MS = 3000;
const TERMINAL = ["completed", "failed"];

const STATUS_CLASS = {
  pending:    "badge badge--pending",
  processing: "badge badge--processing",
  completed:  "badge badge--completed",
  failed:     "badge badge--failed",
};

const RISK_CLASS = {
  Low:    "badge badge--risk-low",
  Medium: "badge badge--risk-medium",
  High:   "badge badge--risk-high",
};

const EFFORT_CLASS = {
  Small:  "badge badge--effort-small",
  Medium: "badge badge--effort-medium",
  Large:  "badge badge--effort-large",
};

const REC_CLASS = {
  "Go":               "badge badge--rec-go",
  "No-Go":            "badge badge--rec-nogo",
  "Needs Discussion": "badge badge--rec-discuss",
};

/**
 * JobDetail — full analysis view for a single job, with 3-second polling.
 * Props:
 *   jobId  — UUID string of the job.
 *   onBack — callback to return to the list view.
 */
export default function JobDetail({ jobId, onBack }) {
  const [job, setJob]       = useState(null);
  const [error, setError]   = useState(null);
  const [showAI, setShowAI] = useState(false);
  const intervalRef         = useRef(null);

  async function fetchJob() {
    try {
      const data = await getJob(jobId);
      setJob(data);
      if (TERMINAL.includes(data.status)) {
        clearInterval(intervalRef.current);
      }
    } catch (err) {
      setError(err.message);
      clearInterval(intervalRef.current);
    }
  }

  useEffect(() => {
    fetchJob();
    intervalRef.current = setInterval(fetchJob, POLL_MS);
    return () => clearInterval(intervalRef.current);
  }, [jobId]);

  return (
    <div>
      <button className="btn-back" onClick={onBack}>
        &#8592; Back to all jobs
      </button>

      {error && (
        <div className="alert alert--error" role="alert" style={{ marginTop: "1.5rem" }}>
          <span className="alert__icon">&#9888;</span>
          <div className="alert__body">{error}</div>
        </div>
      )}

      {!error && !job && (
        <div className="loading-row" style={{ marginTop: "1.5rem" }}>
          Loading&hellip;
        </div>
      )}

      {job && (
        <>
          {/* Header */}
          <div className="detail-topbar">
            <div className="detail-topbar__left">
              <div className="detail-filename">{job.original_filename}</div>
              <div className="detail-badges">
                <span className="badge badge--type">
                  {job.file_type.toUpperCase()}
                </span>
                <span className={STATUS_CLASS[job.status] ?? "badge"}>
                  {job.status}
                </span>
                <span className="job-id-mono" style={{ fontSize: "0.75rem" }}>
                  {job.id}
                </span>
              </div>
            </div>
          </div>

          {/* Processing state */}
          {(job.status === "pending" || job.status === "processing") && (
            <div className="processing-card">
              <div className="processing-card__spinner-wrap">
                <div className="spinner" aria-label="Analysing" />
              </div>
              <p className="processing-card__label">
                <strong>Analysing document&hellip;</strong>
                Results will appear automatically when ready.
              </p>
            </div>
          )}

          {/* Failed state */}
          {job.status === "failed" && (
            <div className="error-card">
              <div className="error-card__title">Analysis Failed</div>
              <div className="error-card__body">
                {job.error_message ?? "An unknown error occurred during analysis."}
              </div>
            </div>
          )}

          {/* Completed results */}
          {job.status === "completed" && (
            <>
              {/* Toolbar — AI Analysis toggle button */}
              {job.ai_summary && (
                <div className="result-toolbar">
                  <button
                    className={`btn-ai-toggle${showAI ? " btn-ai-toggle--active" : ""}`}
                    onClick={() => setShowAI(v => !v)}
                    aria-expanded={showAI}
                  >
                    <span className="btn-ai-toggle__icon">&#10024;</span>
                    {showAI ? "Hide AI Analysis" : "View AI Analysis"}
                    <span className="btn-ai-toggle__caret">{showAI ? "▲" : "▼"}</span>
                  </button>
                </div>
              )}

              {/* AI Analysis panel — visible only when toggled on */}
              {job.ai_summary && showAI && (
                <div className="ai-summary-card">
                  <div className="ai-summary-card__header">
                    <span className="ai-summary-card__icon">&#10024;</span>
                    AI Analysis
                  </div>
                  <div className="ai-summary-card__body">
                    {job.ai_summary.split("\n").map((line, i) => {
                      if (line.startsWith("## ")) {
                        return <h3 key={i} className="ai-summary-card__h3">{line.slice(3)}</h3>;
                      }
                      if (line.match(/^\d+\.\s/)) {
                        return <p key={i} className="ai-summary-card__numbered">{line}</p>;
                      }
                      if (line.startsWith("- ") || line.startsWith("• ")) {
                        return <p key={i} className="ai-summary-card__bullet">{line}</p>;
                      }
                      if (line.trim() === "") {
                        return <div key={i} className="ai-summary-card__spacer" />;
                      }
                      return <p key={i} className="ai-summary-card__p">{line}</p>;
                    })}
                  </div>
                </div>
              )}

              <div className="result-grid">
              <Section label="Summary">
                <ul className="result-list">
                  {job.summary?.map((b, i) => <li key={i}>{b}</li>)}
                </ul>
              </Section>

              <Section label="Key Requirements">
                <ol className="result-list result-list--ordered">
                  {job.requirements?.map((r, i) => <li key={i}>{r}</li>)}
                </ol>
              </Section>

              <Section label="Risk Level">
                <span className={RISK_CLASS[job.risk_level] ?? "badge"}>
                  {job.risk_level}
                </span>
                {job.risk_reasons?.length > 0 && (
                  <ul className="result-list result-list--reasons">
                    {job.risk_reasons.map((r, i) => <li key={i}>{r}</li>)}
                  </ul>
                )}
              </Section>

              <Section label="Effort Estimate">
                <span className={EFFORT_CLASS[job.effort] ?? "badge"}>
                  {job.effort}
                </span>
              </Section>

              <Section label="Recommendation">
                <div className="rec-wrap">
                  <span className={REC_CLASS[job.recommendation] ?? "badge"}>
                    {job.recommendation}
                  </span>
                </div>
              </Section>
            </div>
            </>
          )}
        </>
      )}
    </div>
  );
}

/** Labelled result row in the detail grid. */
function Section({ label, children }) {
  return (
    <div className="result-section">
      <div className="result-section__label">{label}</div>
      <div className="result-section__value">{children}</div>
    </div>
  );
}
