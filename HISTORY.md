# History

> Back-filled from git history on 2026-06-27 — entries below are reconstructed from commit messages, not contemporaneous notes.

## 2026-01-20 — Project inception

- Initial commit: Flask-based "Lead Finder" tool to discover local businesses with poor or missing web presence, for a freelance web-dev sales pipeline.
- Switched location configuration to environment-based settings (`DEFAULT_LAT`/`DEFAULT_LNG`) and updated docs accordingly.

## 2026-01-21 — Primary build-out

Nearly all feature work landed in a single intensive day. Grouped by area:

### Search & pipeline
- Implemented **Omni-Search** multi-category area scanning with search debug logging; ensured search results persist to the database.
- Expanded Omni-Search category coverage from a starter set to 26 high-value business categories.
- Added a **bulk analysis** tool with a range slider and an "analyze all" option; fixed a circular import that broke bulk analysis.
- Added real-time streaming scan logs surfaced through a live modal dashboard.

### Web analysis
- Added tech-stack detection (WordPress, Wix, Squarespace, Shopify, etc.), load-speed measurement, and improved analysis logging.
- Added descriptive analysis logs and deep technical-details output, including fallback-attempt reporting.

### Dashboard & UX
- Enhanced dashboard with clickable links and detailed analysis info; surfaced analyzed leads at the top for visibility.
- Improved dashboard actions: individual analyze button, renamed hide/details actions, status icons, and analyze-button feedback.
- Implemented a distinct color scheme for lead statuses.

### Fixes & hardening
- Added a root-domain fallback for 404 deep links; added a favicon route to quiet console logs.
- Fixed a missing `time` import in `analyzer.py` and a `TypeError` in the lead-detail template (load-time formatting).
- Resolved a "Method Not Allowed" error on DB reset and addressed SQLite locking.
- Prevented technical-details from auto-dismissing and increased flash-message duration.

### HTTPS / security / tooling
- Enabled adhoc SSL for local development to support HTTPS-only browsers.
- Added Flask-Talisman to enforce HTTPS and security headers, then removed it and reverted to manual HTTPS management.
- Made `setup.sh` robust against venv path mismatches; updated shell scripts to use direct venv paths.

### Project rename & cleanup
- Renamed all references from `webscan` to `leadscan`; removed a temporary migration script.
- Final project cleanup, documentation updates, and signpost comments.

### Release v1.40
- Security fixes: real SSL certificate verification (replacing `verify=False`), socket-based SSL detection, and an atomic `AppConfig.increment()` to fix a race condition.
- Input validation (radius bounds 100m–50km, keyword sanitization), `place_id` database indexing, structured logging in place of silent exception handling, and `created_at`/`analyzed_at` timestamps on the Lead model.
- Added testing infrastructure (34 tests across analyzer, Google Places, pipeline, and config) and applied ruff formatting.

### Release v1.41
- Expanded Omni-Search to 81+ comprehensive business categories.

## Notes

- Last commit on record: 2026-01-21 (v1.41). The repo has been dormant since.
- Version drift reconciled 2026-06-27: `README.md` and `docs/DESIGN.md` "Current Version" bumped v1.40 → v1.41 to match `app/templates/base.html` and the final commit.
