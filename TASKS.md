# Tasks

> Live queue for **current, pending, and future** work — never history. Completed work belongs in `HISTORY.md`. See `~/.agent/AGENTS.md` → Required Documents.

Status key: `pending | in progress | done | blocked`

## Rules

- Never trample another session's in-flight or pending work.
- Update status as work progresses.
- Only mark `done` after verification (tests pass, behavior confirmed).
- `done` is **transient**: after verification, port the row's substance into `HISTORY.md` and delete the row from `TASKS.md` in the same change.
- If a completed task is worth remembering, that's a `HISTORY.md` entry — not a `TASKS.md` preservation.
- Smell test: if `done` rows outnumber open rows, the file has drifted into a log. Clean it up.
- Keep tasks small and actionable — one unit of work each.

## Open

> Source: `docs/ROADMAP.md`. Repo is dormant (last commit 2026-01-21). Roadmap items already shipped (Tech Stack Detection, Speed Test/TTFB, Analyze All batch analysis) are intentionally omitted — they are recorded in `HISTORY.md`. The items below are the roadmap entries with no corresponding implementation in git history or `README.md`.

### Task 1: Broken Link Checker (Phase 2)
- **Status:** pending
- **Description:** Scan a lead's landing page for 404 links to use as a sales pitch point.
- **Blocked by:** none
- **Tests:** add coverage in `tests/test_analyzer.py`
- **Done when:**
  - The analyzer reports broken/404 links found on a scanned page.
  - Results surface in the lead detail / technical logs.

### Task 2: LLM Pitch Generation (Phase 3)
- **Status:** pending
- **Description:** Add a "Pitch" button on the Lead Detail page that sends lead data to an LLM and drafts a personalized outreach email; persist the draft.
- **Blocked by:** none
- **Tests:** unit-test prompt assembly and draft storage; mock the LLM call
- **Done when:**
  - Lead Detail has a button that generates an email draft from lead data.
  - The generated draft is saved to `notes` or a dedicated field.

### Task 3: CSV Export (Phase 4)
- **Status:** pending
- **Description:** Add a button to export leads to CSV for import into Google Sheets/Excel.
- **Blocked by:** none
- **Tests:** unit-test CSV serialization of leads
- **Done when:**
  - A user can download the current leads as a CSV file.

### Task 4: Calendar / follow-up reminders (Phase 4)
- **Status:** pending
- **Description:** Add follow-up reminder capability ("remind me to call on Tuesday") per lead.
- **Blocked by:** none
- **Tests:** unit-test reminder date handling
- **Done when:**
  - A lead can have a follow-up reminder set and viewed.
