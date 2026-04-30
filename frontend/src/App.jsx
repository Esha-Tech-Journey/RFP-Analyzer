import { useState } from "react";
import FileUploadForm from "./components/FileUploadForm";
import JobList from "./components/JobList";
import JobDetail from "./components/JobDetail";

/**
 * App — root component managing current view and selected job.
 * Views: "list" | "upload" | "detail"
 */
export default function App() {
  const [view, setView] = useState("list");
  const [selectedJobId, setSelectedJobId] = useState(null);

  function handleSelectJob(jobId) {
    setSelectedJobId(jobId);
    setView("detail");
  }

  function handleJobCreated(job) {
    setSelectedJobId(job.id);
    setView("detail");
  }

  return (
    <div className="app-shell">
      <nav className="nav">
        <span className="nav__brand">
          <span className="nav__epam-logo">
            <span className="nav__epam-badge">EPAM</span>
          </span>
          <span className="nav__divider" />
          <span className="nav__app-name">RFP Insight &amp; Risk Analyzer</span>
        </span>
        <div className="nav__actions">
          <button
            className={`nav__link${view === "list" ? " nav__link--active" : ""}`}
            onClick={() => setView("list")}
          >
            All Jobs
          </button>
          <button
            className={`nav__link${view === "upload" ? " nav__link--active" : ""}`}
            onClick={() => setView("upload")}
          >
            Upload RFP
          </button>
        </div>
      </nav>

      <div className="main-content">
        {view === "list" && (
          <JobList onSelectJob={handleSelectJob} onUpload={() => setView("upload")} />
        )}
        {view === "upload" && (
          <FileUploadForm onJobCreated={handleJobCreated} />
        )}
        {view === "detail" && selectedJobId && (
          <JobDetail jobId={selectedJobId} onBack={() => setView("list")} />
        )}
      </div>
    </div>
  );
}
