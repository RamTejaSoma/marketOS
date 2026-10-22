import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import cron from "node-cron";
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

dotenv.config();
const here = path.dirname(fileURLToPath(import.meta.url));
const root = process.env.PROJECT_ROOT
  ? path.resolve(process.env.PROJECT_ROOT)
  : path.resolve(here, "..");
const reportsDir = path.join(root, "reports");
const runScript = path.join(root, "run.py");
const port = Number(process.env.PORT || 5000);
const app = express();
app.use(cors({ origin: ["http://localhost:5173", "http://127.0.0.1:5173"] }));
app.use(express.json());
let job = {
  status: "idle",
  message: "No run in this backend session.",
  startedAt: null,
  finishedAt: null,
  exitCode: null,
  output: "",
};

function getReports() {
  if (!fs.existsSync(reportsDir)) return [];
  return fs
    .readdirSync(reportsDir)
    .filter((n) => /^morning_report_\d{4}-\d{2}-\d{2}\.md$/.test(n))
    .map((filename) => {
      const date = filename.match(/\d{4}-\d{2}-\d{2}/)[0];
      const pdf = filename.replace(/\.md$/, ".pdf");
      const mdPath = path.join(reportsDir, filename),
        pdfPath = path.join(reportsDir, pdf);
      return {
        filename,
        date,
        markdownBytes: fs.statSync(mdPath).size,
        pdfAvailable: fs.existsSync(pdfPath),
        pdfBytes: fs.existsSync(pdfPath) ? fs.statSync(pdfPath).size : null,
      };
    })
    .sort((a, b) => b.date.localeCompare(a.date));
}
function safeReport(name, ext) {
  if (!new RegExp(`^morning_report_\\d{4}-\\d{2}-\\d{2}\\.${ext}$`).test(name))
    return null;
  const full = path.resolve(reportsDir, name);
  return full.startsWith(path.resolve(reportsDir) + path.sep) ? full : null;
}
function startRun(trigger = "manual") {
  if (job.status === "running") return false;
  if (!fs.existsSync(runScript))
    throw new Error(
      `run.py not found: ${runScript}. Set PROJECT_ROOT in backend/.env.`,
    );
  const venvPython =
    process.platform === "win32"
      ? path.join(root, ".venv", "Scripts", "python.exe")
      : path.join(root, ".venv", "bin", "python");
  const python = fs.existsSync(venvPython)
    ? venvPython
    : process.platform === "win32"
      ? "python"
      : "python3";
  job = {
    status: "running",
    trigger,
    message: `Started (${trigger})`,
    startedAt: new Date().toISOString(),
    finishedAt: null,
    exitCode: null,
    output: "",
  };
  const child = spawn(python, [runScript], {
    cwd: root,
    env: {
  ...process.env,
  PYTHONUNBUFFERED: "1",
  PYTHONIOENCODING: "utf-8"
},
    windowsHide: true,
  });
  child.stdout.on(
    "data",
    (d) => (job.output = (job.output + d.toString()).slice(-30000)),
  );
  child.stderr.on(
    "data",
    (d) => (job.output = (job.output + d.toString()).slice(-30000)),
  );
  child.on("error", (e) => {
    job.status = "failed";
    job.message = e.message;
    job.finishedAt = new Date().toISOString();
  });
  child.on("close", (code) => {
    job.status = code === 0 ? "completed" : "failed";
    job.exitCode = code;
    job.finishedAt = new Date().toISOString();
    job.message =
      code === 0
        ? "Report generation completed."
        : `Pipeline exited with code ${code}; inspect job output.`;
  });
  return true;
}
app.get("/api/health", (_req, res) =>
  res.json({
    status: "ok",
    projectRoot: root,
    pythonPipelineFound: fs.existsSync(runScript),
    schedulerEnabled: process.env.ENABLE_SCHEDULER === "true",
  }),
);
app.get("/api/reports", (_req, res) => res.json({ reports: getReports() }));
app.get("/api/jobs/current", (_req, res) => res.json({ job }));
app.get("/api/reports/:filename", (req, res) => {
  const file = safeReport(req.params.filename, "md");
  if (!file) return res.status(400).json({ error: "Invalid report filename." });
  if (!fs.existsSync(file))
    return res.status(404).json({ error: "Report not found." });
  res.type("text/markdown; charset=utf-8").send(fs.readFileSync(file, "utf8"));
});
app.get("/api/reports/:filename/pdf", (req, res) => {
  const name = req.params.filename.endsWith(".md")
    ? req.params.filename.replace(/\.md$/, ".pdf")
    : req.params.filename;
  const file = safeReport(name, "pdf");
  if (!file) return res.status(400).json({ error: "Invalid PDF filename." });
  if (!fs.existsSync(file))
    return res.status(404).json({ error: "PDF not found." });
  res.download(file, name);
});
app.post("/api/reports/generate", (_req, res) => {
  try {
    if (!startRun("manual"))
      return res
        .status(409)
        .json({ error: "A report is already running.", job });
    res.status(202).json({ message: "Generation started.", job });
  } catch (e) {
    res.status(500).json({ error: e.message });
  }
});
if (process.env.ENABLE_SCHEDULER === "true") {
  const expression = process.env.SCHEDULE_CRON || "30 6 * * *";
  if (!cron.validate(expression))
    throw new Error(`Invalid cron expression: ${expression}`);
  cron.schedule(
    expression,
    () => {
      try {
        if (!startRun("scheduled"))
          console.warn("Scheduled run skipped: another job is running.");
      } catch (e) {
        console.error("Scheduled run failed:", e);
      }
    },
    { timezone: process.env.SCHEDULE_TIMEZONE || "Asia/Kolkata" },
  );
  console.log(
    `Scheduler enabled: ${expression} (${process.env.SCHEDULE_TIMEZONE || "Asia/Kolkata"})`,
  );
} else console.log("Scheduler disabled; set ENABLE_SCHEDULER=true to enable.");
app.listen(port, () =>
  console.log(
    `API listening at http://localhost:${port}\nProject root: ${root}`,
  ),
);
