
import { useCallback, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  Activity,
  ArrowDownToLine,
  FileText,
  LoaderCircle,
  Sparkles,
  Zap,
  ShieldAlert,
} from "lucide-react";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000";

const dateLabel = (date) =>
  new Date(`${date}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });

export default function App() {
  const [health, setHealth] = useState(null);
  const [reports, setReports] = useState([]);
  const [selected, setSelected] = useState("");
  const [md, setMd] = useState("");
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [hRes, rRes, jRes] = await Promise.all([
        fetch(`${API}/api/health`),
        fetch(`${API}/api/reports`),
        fetch(`${API}/api/jobs/current`),
      ]);

      if (!hRes.ok || !rRes.ok || !jRes.ok) {
        throw new Error("API request failed.");
      }

      const h = await hRes.json();
      const r = await rRes.json();
      const j = await jRes.json();
      const items = r.reports || [];

      setHealth(h);
      setReports(items);
      setJob(j.job);
      setError("");

      if (!selected && items.length) {
        setSelected(items[0].filename);
      } else if (
        selected &&
        !items.some((item) => item.filename === selected) &&
        items.length
      ) {
        setSelected(items[0].filename);
      }
    } catch {
      setError("Cannot connect to the backend. Start Express on port 5000.");
    }
  }, [selected]);

  const readReport = useCallback(async (filename) => {
    if (!filename) {
      setMd("");
      setSelected("");
      return;
    }

    try {
      const response = await fetch(
        `${API}/api/reports/${encodeURIComponent(filename)}`
      );

      if (!response.ok) throw new Error("Could not load report.");

      setMd(await response.text());
      setSelected(filename);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (selected) readReport(selected);
  }, [selected, readReport]);

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`${API}/api/jobs/current`);
        const data = await response.json();

        setJob(data.job);

        if (data.job?.status !== "running") {
          load();
        }
      } catch {
        // Keep the current dashboard if polling temporarily fails.
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [load]);

  async function generateReport() {
    setError("");

    try {
      const response = await fetch(`${API}/api/reports/generate`, {
        method: "POST",
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Unable to start generation.");
      }

      setJob(data.job);
    } catch (err) {
      setError(err.message);
    }
  }

  const running = job?.status === "running";
  const current = reports.find((r) => r.filename === selected);
  const pdfCount = reports.filter((r) => r.pdfAvailable).length;

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="mark">
            <Activity />
          </span>
          <div>
            <b>
              MARKET<span>OS</span>
            </b>
            <small>INTELLIGENCE TERMINAL</small>
          </div>
        </div>

        <p className="navlabel">WORKSPACE</p>

        <div className="nav active">
          <Activity size={17} />
          Report dashboard
        </div>

        <div className="sidebottom">
          <i className={health?.status === "ok" ? "led" : "led off"} />
          <div>
            <b>
              {health?.status === "ok" ? "API connected" : "Connecting…"}
            </b>
            <small>Local Python engine</small>
          </div>
        </div>
      </aside>

      <main>
        <header>
          <span>
            WORKSPACE <b>/ REPORTS</b>
          </span>
          <label>
            <i />
            LOCAL ENGINE
          </label>
        </header>

        {error && (
          <div className="error">
            <ShieldAlert size={16} />
            {error}
            <button onClick={() => setError("")}>Dismiss</button>
          </div>
        )}

        <section className="workspace">
          {/* LEFT HALF: dashboard controls and report history */}
          <div className="left-column">
            <section className="hero">
              <div>
                <p className="eyebrow">
                  <Sparkles size={13} />
                  AI-POWERED MARKET RESEARCH
                </p>

                <h1>
                  Report <span>dashboard</span>
                </h1>

                <p className="sub">
                  Generate, review, and export your daily market intelligence.
                </p>
              </div>

              <button
                className="primary"
                disabled={running || !health?.pythonPipelineFound}
                onClick={generateReport}
              >
                {running ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Zap size={17} />
                )}
                {running ? "Generating…" : "Generate report"}
              </button>
            </section>

            <section className="stats">
              <div>
                <small>AVAILABLE REPORTS</small>
                <strong>{String(reports.length).padStart(2, "0")}</strong>
                <p>Markdown reports found</p>
              </div>

              <div>
                <small>PDF EXPORTS</small>
                <strong>{String(pdfCount).padStart(2, "0")}</strong>
                <p>Ready to download</p>
              </div>

              <div>
                <small>PIPELINE STATUS</small>
                <strong
                  className={
                    running
                      ? "amber"
                      : health?.pythonPipelineFound
                        ? "green"
                        : "offline"
                  }
                >
                  {running
                    ? "RUNNING"
                    : health?.pythonPipelineFound
                      ? "READY"
                      : "OFFLINE"}
                </strong>
                <p>
                  {running ? "Python pipeline is working" : "Entry point detected"}
                </p>
              </div>

              <div>
                <small>LAST JOB</small>
                <strong>
                  {job?.finishedAt
                    ? new Date(job.finishedAt).toLocaleTimeString("en-IN", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })
                    : "—"}
                </strong>
                <p>{job?.message || "No run in this session"}</p>
              </div>
            </section>

            {running && (
              <div className="running">
                <LoaderCircle className="spin" />
                <div>
                  <b>Building your morning report</b>
                  <p>
                    Collecting market data, processing news, and generating
                    the report.
                  </p>
                </div>
                <span>IN PROGRESS</span>
              </div>
            )}

            <section className="history panel">
              <div className="panelhead">
                <div>
                  <small>YOUR ARCHIVE</small>
                  <h2>Report history</h2>
                </div>
                <span className="count">{reports.length} reports</span>
              </div>

              <div className="reports">
                {reports.length === 0 ? (
                  <div className="empty small-empty">
                    <FileText size={24} />
                    <b>No reports found</b>
                    <p>Generate your first report.</p>
                  </div>
                ) : (
                  reports.map((report) => (
                    <button
                      key={report.filename}
                      onClick={() => readReport(report.filename)}
                      className={`report ${
                        selected === report.filename ? "chosen" : ""
                      }`}
                    >
                      <FileText size={18} />
                      <span>
                        <b>{dateLabel(report.date)}</b>
                        <small>{report.filename}</small>
                        <em>
                          {report.pdfAvailable
                            ? "PDF ready"
                            : "PDF unavailable"}
                        </em>
                      </span>
                    </button>
                  ))
                )}
              </div>
            </section>
          </div>

          {/* RIGHT HALF: large document viewer */}
          <section className="viewer-panel">
            <div className="viewer-toolbar">
              <div className="viewer-title">
                <small>DOCUMENT VIEWER</small>
                <h2>{current ? dateLabel(current.date) : "Report preview"}</h2>
              </div>

              {current?.pdfAvailable && (
                <a
                  className="download"
                  href={`${API}/api/reports/${encodeURIComponent(
                    current.filename
                  )}/pdf`}
                >
                  <ArrowDownToLine size={15} />
                  Download PDF
                </a>
              )}
            </div>

            <div className="docmeta">
              <span>
                <FileText size={12} /> MARKDOWN
              </span>
              <span>{current?.filename || "Select a report from history"}</span>
              {current && (
                <span>{current.pdfAvailable ? "PDF READY" : "PDF NOT AVAILABLE"}</span>
              )}
            </div>

            <div className="markdown">
              {md ? (
                <ReactMarkdown>{md}</ReactMarkdown>
              ) : (
                <div className="empty">
                  <FileText size={28} />
                  <b>Your intelligence report appears here</b>
                  <p>Select a report on the left or generate a new one.</p>
                </div>
              )}
            </div>
          </section>
        </section>

        <footer>
          <span>MARKETOS INTELLIGENCE SYSTEM</span>
          <span>LOCAL-FIRST · PYTHON + NODE + REACT</span>
        </footer>
      </main>
    </div>
  );
}
