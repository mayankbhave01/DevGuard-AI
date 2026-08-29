# DevGuard AI — 3-Minute Demo Script

## 0:00–0:25 — Dashboard
Open the dashboard.

Say:
“DevGuard AI is a full-stack code-security review product. The dashboard summarizes code-health scores, severity distribution, issue categories and historical scans.”

## 0:25–1:00 — New Scan
Open **New Scan**.

Use the vulnerable Python sample and keep AI deep review disabled.

Say:
“The main scanner is deterministic and does not require a paid API, so core findings remain reproducible and fast.”

Run the scan.

## 1:00–1:45 — Result
Show the health score and findings.

Highlight:
- hard-coded credential
- SQL injection risk
- command injection / dangerous execution
- debug logging

Open one finding and point to:
- severity
- rule ID
- source evidence
- suggested fix

## 1:45–2:15 — Reports
Click **Download report**.

Show:
- PDF
- HTML
- Markdown
- JSON
- CSV
- TXT
- All Formats ZIP

Mention that report depth and included content can be customized.

## 2:15–2:40 — History
Open **Scan History** and show that both scans remain persisted.

Say:
“This is not just a one-time script. Results are tied to the authenticated user and create an audit trail.”

## 2:40–3:00 — Architecture
Close with:

“The frontend is React/TypeScript, the backend is FastAPI/SQLAlchemy with JWT auth, SQLite is used for a zero-config local demo, PostgreSQL is available through Docker, and Ollama/OpenAI-compatible AI review is optional.”
