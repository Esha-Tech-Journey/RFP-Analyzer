import { useState, useRef } from "react";
import { uploadRFP, submitText } from "../api/rfpClient";

const ACCEPTED_EXTENSIONS = ["pdf", "docx", "txt"];
const FILE_ICONS = { pdf: "📄", docx: "📝", txt: "📃" };
const MIN_TEXT_LENGTH = 50;

function formatFileSize(bytes) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getExtension(filename) {
  return filename.split(".").pop().toLowerCase();
}

function isAccepted(filename) {
  return ACCEPTED_EXTENSIONS.includes(getExtension(filename));
}

/**
 * FileUploadForm — two-tab input: file upload OR plain-text entry.
 * Props:
 *   onJobCreated(job) — called with the new job on successful submit.
 */
export default function FileUploadForm({ onJobCreated }) {
  const [activeTab, setActiveTab] = useState("file"); // "file" | "text"

  return (
    <div>
      <p className="page-heading">Submit RFP for Analysis</p>
      <p className="page-subheading">
        Upload a document or paste the RFP content directly.
      </p>

      <div className="card upload-card">
        {/* Tab switcher */}
        <div className="tab-bar">
          <button
            className={`tab-btn${activeTab === "file" ? " tab-btn--active" : ""}`}
            onClick={() => setActiveTab("file")}
            type="button"
          >
            &#8593; Upload File
          </button>
          <button
            className={`tab-btn${activeTab === "text" ? " tab-btn--active" : ""}`}
            onClick={() => setActiveTab("text")}
            type="button"
          >
            &#9998; Enter Text
          </button>
        </div>

        <div className="tab-panel">
          {activeTab === "file" && (
            <FileTab onJobCreated={onJobCreated} />
          )}
          {activeTab === "text" && (
            <TextTab onJobCreated={onJobCreated} />
          )}
        </div>
      </div>
    </div>
  );
}

/* ── File upload tab ───────────────────────────────────── */

function FileTab({ onJobCreated }) {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragOver, setDragOver]         = useState(false);
  const [uploading, setUploading]       = useState(false);
  const [error, setError]               = useState(null);
  const [createdJob, setCreatedJob]     = useState(null);
  const inputRef = useRef(null);

  function pickFile(file) {
    setError(null);
    setCreatedJob(null);
    if (!isAccepted(file.name)) {
      setError("Unsupported file type. Accepted formats: PDF, DOCX, TXT.");
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
  }

  function handleDragOver(e)  { e.preventDefault(); setDragOver(true); }
  function handleDragLeave()  { setDragOver(false); }
  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) pickFile(file);
  }
  function handleInputChange(e) {
    const file = e.target.files[0];
    if (file) pickFile(file);
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    try {
      const job = await uploadRFP(selectedFile);
      setCreatedJob(job);
      setSelectedFile(null);
      if (inputRef.current) inputRef.current.value = "";
      onJobCreated(job);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  }

  const ext = selectedFile ? getExtension(selectedFile.name) : null;
  const fileIcon = FILE_ICONS[ext] ?? "📎";

  return (
    <form onSubmit={handleSubmit}>
      <div
        className={`drop-zone${dragOver ? " drop-zone--active" : ""}`}
        onClick={() => inputRef.current.click()}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current.click()}
        aria-label="Click or drag a file to upload"
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.docx,.txt"
          style={{ display: "none" }}
          onChange={handleInputChange}
        />
        {selectedFile ? (
          <div className="drop-zone__file-info">
            <span className="drop-zone__file-icon">{fileIcon}</span>
            <div>
              <div className="drop-zone__file-name">{selectedFile.name}</div>
              <div className="drop-zone__file-meta">
                <span className="drop-zone__file-size">
                  {formatFileSize(selectedFile.size)}
                </span>
                <button
                  type="button"
                  className="drop-zone__change"
                  onClick={(e) => { e.stopPropagation(); inputRef.current.click(); }}
                >
                  Change file
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            <span className="drop-zone__icon">&#8593;</span>
            <p className="drop-zone__prompt">
              Drag &amp; drop your file here, or <strong>click to browse</strong>
            </p>
          </>
        )}
      </div>

      <div className="upload-meta-row">
        <span className="upload-hint">Accepted: PDF, DOCX, TXT &mdash; max 10 MB</span>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!selectedFile || uploading}
        >
          {uploading ? "Uploading\u2026" : "Analyse RFP"}
        </button>
      </div>

      {error && (
        <div className="alert alert--error" role="alert">
          <span className="alert__icon">&#9888;</span>
          <div className="alert__body">{error}</div>
        </div>
      )}
      {createdJob && (
        <div className="alert alert--success" role="status">
          <span className="alert__icon">&#10003;</span>
          <div className="alert__body">
            Job queued successfully. Redirecting to results&hellip;
            <span className="alert__id">{createdJob.id}</span>
          </div>
        </div>
      )}
    </form>
  );
}

/* ── Text entry tab ────────────────────────────────────── */

function TextTab({ onJobCreated }) {
  const [title, setTitle]           = useState("");
  const [text, setText]             = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError]           = useState(null);
  const [createdJob, setCreatedJob] = useState(null);

  const charCount   = text.length;
  const tooShort    = charCount > 0 && charCount < MIN_TEXT_LENGTH;
  const canSubmit   = title.trim().length > 0 && charCount >= MIN_TEXT_LENGTH && !submitting;

  async function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const job = await submitText(title.trim(), text.trim());
      setCreatedJob(job);
      setTitle("");
      setText("");
      onJobCreated(job);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      {/* Title field */}
      <div className="text-field">
        <label className="text-field__label" htmlFor="rfp-title">
          Job Title
        </label>
        <input
          id="rfp-title"
          type="text"
          className="text-field__input"
          placeholder="e.g. Acme Corp RFP 2026"
          maxLength={255}
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          autoComplete="off"
        />
      </div>

      {/* Content textarea */}
      <div className="text-field" style={{ marginTop: "1rem" }}>
        <label className="text-field__label" htmlFor="rfp-content">
          RFP Content
        </label>
        <textarea
          id="rfp-content"
          className={`text-field__textarea${tooShort ? " text-field__textarea--error" : ""}`}
          placeholder="Paste or type the full RFP content here…"
          rows={12}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="text-field__meta">
          {tooShort && (
            <span className="text-field__hint text-field__hint--error">
              Minimum {MIN_TEXT_LENGTH} characters required
            </span>
          )}
          {!tooShort && (
            <span className="text-field__hint">
              {charCount > 0 ? `${charCount.toLocaleString()} characters` : `Minimum ${MIN_TEXT_LENGTH} characters`}
            </span>
          )}
        </div>
      </div>

      <div className="upload-meta-row" style={{ marginTop: "1.25rem" }}>
        <span className="upload-hint">Plain text only &mdash; no file size limit</span>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!canSubmit}
        >
          {submitting ? "Submitting\u2026" : "Analyse RFP"}
        </button>
      </div>

      {error && (
        <div className="alert alert--error" role="alert">
          <span className="alert__icon">&#9888;</span>
          <div className="alert__body">{error}</div>
        </div>
      )}
      {createdJob && (
        <div className="alert alert--success" role="status">
          <span className="alert__icon">&#10003;</span>
          <div className="alert__body">
            Job queued successfully. Redirecting to results&hellip;
            <span className="alert__id">{createdJob.id}</span>
          </div>
        </div>
      )}
    </form>
  );
}
