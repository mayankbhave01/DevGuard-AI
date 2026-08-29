# DevGuard AI — Interview Preparation

## 30-Second Pitch

DevGuard AI is a full-stack developer-security product that analyzes source code for security and maintainability risks. I designed it around a deterministic scanning engine so the main findings are reproducible, fast and usable without a paid API. The platform adds JWT authentication, persisted scan history, analytics, explainable remediation, multi-format reports, SQLite/PostgreSQL persistence and an optional LLM deep-review layer.

## 90-Second Architecture Answer

The frontend is React and TypeScript and communicates with a FastAPI backend through REST APIs protected by JWT authentication. When code is submitted, the backend runs a deterministic analyzer that applies security and quality rules and, for Python, AST-based inspection. Findings are normalized into rule ID, severity, description, source evidence and suggestion, then a transparent health score is calculated. SQLAlchemy persists users, scans and issues. SQLite is used for the easiest local demo and Docker can run PostgreSQL. An optional LLM adapter supports Ollama or an OpenAI-compatible endpoint, but LLM output is not required for the main scanner. A reporting service exports scan results in PDF, HTML, Markdown, JSON, CSV, TXT or an all-formats ZIP.

## Why deterministic-first instead of only an LLM?

Because security tooling needs repeatability. The same vulnerable code should produce the same core finding. Deterministic rules are cheap, testable and predictable. An LLM is useful as an enhancement for explanation or contextual review, but should not be the only source of truth.

## Example Finding

In the final demo, a vulnerable Python sample triggered:

- Hard-coded credential — Critical
- SQL injection risk — High
- Command injection / dangerous command execution — High
- Debug logging — Low

The resulting health score was 45/100.

## How is the score calculated?

Each severity level has a penalty. Critical and high findings reduce the score much more than low-severity maintainability issues. The scoring system is intentionally a transparent heuristic rather than an opaque ML score.

## Why persist scans?

Persistence creates an audit trail and makes historical analytics, comparisons, dashboard aggregates and regenerated reports possible. Without persistence, the project would only be a one-time code checker.

## Why SQLite and PostgreSQL?

SQLite removes setup friction for local demos. PostgreSQL represents the more realistic deployment path for concurrency, indexing and production persistence. SQLAlchemy keeps the application logic portable between them.

## How is user isolation handled?

Protected scan operations are tied to the authenticated JWT user. Reads, deletes and exports validate ownership rather than allowing arbitrary scan IDs to expose another user's data.

## What does the optional AI layer add?

It can provide deeper contextual review or richer explanation. It is intentionally optional because provider latency, cost and hallucination should not make the core product unreliable.

## What would you build next?

1. GitHub/GitLab repository ingestion
2. Pull-request diff scanning
3. Semgrep / Bandit / ESLint / tree-sitter adapters
4. Async scan jobs with a queue
5. Organization workspaces and RBAC
6. Baseline comparisons between commits
7. Dependency vulnerability scanning
8. SARIF output for CI tooling
9. Rate limiting and observability
10. Managed database/backups for hosted deployment

## Limitations

- Lightweight rules do not replace mature enterprise SAST.
- Repository-level data/control-flow analysis is not implemented.
- The current health score is a product heuristic.
- Optional LLM output can be imperfect and should not override deterministic evidence.
- The current portfolio build is optimized for a clear local/product demo rather than multi-tenant enterprise scale.

## Common Interview Question: “Where is the AI?”

The project uses AI as an **optional deep-review layer**, while its primary security engine is deterministic. This is deliberate. The product is AI-assisted rather than pretending every security decision requires an LLM. That architecture makes it more reliable and easier to demonstrate even without network access or API credits.
