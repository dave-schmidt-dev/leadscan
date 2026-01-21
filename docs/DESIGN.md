# LeadScan Design & Architecture

## Core Philosophy
The goal of LeadScan is to translate **agentic development capabilities** into **real-world income**. It does this by automating the tedious top-of-funnel work in sales: finding leads and qualifying them.

**Philosophy**: 
1.  **Low Cost**: Use heuristic scripts (Regex/Soup) instead of expensive LLM calls for basic filtering.
2.  **Local First**: Data lives in a local SQLite file. No cloud bills.
3.  **Action-Oriented**: The UI focuses on moving a lead from "Scraped" to "Contacted".

## Project Protocols

### Build Versioning
- Every developer/agent modification task MUST be accompanied by a version increment in `app/templates/base.html`.
- Format: `v1.x` where `x` is incremented.
- **Current Version**: v1.40

### Code Quality Standards (v1.40+)
- **Linting**: All code must pass `ruff check` before commit (enforced by pre-commit hook).
- **Testing**: New features require tests; all tests must pass before push (enforced by pre-push hook).
- **Logging**: Use `logger.warning/error/info` instead of silent exception handling.
- **Security**: SSL verification enabled by default; input validation for all user inputs.

## Architecture

### The Monolith
We chose a **Flask Monolith** pattern.
- **Why?** Simplifies deployment and development. Logic and UI live together.
- **State**: Managed via server-side rendering (Jinja2) and SQLite.

### The Pipeline
Data flows through the system in this order:

1.  **Ingestion (`google_places.py`)**
    - **Location**: Default coordinates are pulled from `DEFAULT_LAT` and `DEFAULT_LNG` in the `.env` file.
    - **Omni-Search**: If keyword="business", iterates through **100+ local service categories** covering ~95% of non-franchise small businesses (configurable via `OMNI_SEARCH_CATEGORIES` env var). Categories span home services, medical, professional, automotive, personal services, and specialty contractors. See `docs/CATEGORIES.md` for complete breakdown.
    - **Streaming Results**: Progress is yielded via generator to allow real-time UI logging.
    - **Filtering**: Checks result against `CHAIN_BLOCKLIST` and `TYPE_BLOCKLIST`.
    - **Deduplication**: Checks DB for existing `place_id` (indexed for performance).
    - **Input Validation**: Radius bounded to 100-50,000 meters; keyword sanitized.

2.  **Enrichment (`pipeline.py` & `analyzer.py`)**
    - Triggered manually (Individual) or in Batch (Bulk).
    - **Deep Fetch**: Call Google Details API for Phone/Website.
    - **Connectivity**: `requests.get()` with a 10s timeout and root-domain fallback.
    - **Performance**: Captures TTFB (Time to First Byte).
    - **Security**: **Proper SSL certificate verification** (v1.40):
        - Primary attempt with `verify=True` for secure connections.
        - Fallback to `verify=False` only on SSL errors, with explicit logging.
        - Socket-based SSL validation using `ssl.create_default_context()`.
    - **Heuristics**:
        - `Tech Stack`: Signature scanning for WP, Wix, Shopify, etc.
        - `Mobile`: Viewport tag detection.
        - `Contact`: Multi-pattern regex for emails/phones.
        - `Freshness`: Copyright year extraction.
    - **Status Update**: Automatically moves lead from `Scraped` -> `Analyzed`.
    - **Timestamps**: Records `analyzed_at` timestamp for tracking.

3.  **Presentation (UI)**
    - Leads grouped by Status (Analyzed at the top).
    - Technical Analysis logs provide transparency into failed or successful checks.
    - Responsive dark-mode dashboard with real-time modal progress.

## Database Schema (`Lead` Model)

- **Identity**: `place_id` (Google Unique ID, indexed).
- **Contact**: `name`, `phone`, `address`, `website_url`.
- **Metrics**: `ssl_active`, `mobile_viewport`, `contact_info_found`, `copyright_year`, `content_heuristic_score`, `load_time`.
- **Workflow**: `status` (Enum), `notes` (Text).
- **Timestamps**: `created_at`, `analyzed_at` (v1.40+).

## API Quota Management (`AppConfig` Model)
- Tracks `google_api_nearby` and `google_api_details` separately.
- **Atomic Increment** (v1.40): Uses SQL `UPDATE` for thread-safe counter increments.
- Auto-resets on the 1st of every month.
- Stats persist even if "Reset DB" is clicked (via backup/restore logic).

## Testing Strategy (v1.40+)

### Test Suite (34 tests)
- **Analyzer Tests** (13): SSL verification, heuristics detection, error handling.
- **Google Places Tests** (9): Filtering, deduplication, API error handling.
- **Pipeline Tests** (7): Scoring logic, status transitions, timestamp updates.
- **Config Tests** (5): Atomic increment, monthly reset, get/set operations.

### Coverage Focus
- Critical paths: SSL verification, scoring, deduplication.
- Error handling: Connection failures, timeouts, malformed responses.
- Concurrency: Atomic operations, race conditions.

### Git Hooks
- **Pre-commit**: `ruff check` on staged files (prevents committing bad code).
- **Pre-push**: Full test suite (prevents pushing broken code).

## Security Improvements (v1.40)

1. **SSL Certificate Validation**: Now properly validates certificates instead of blindly trusting all connections.
2. **Input Sanitization**: Radius bounds, keyword length limits, type validation.
3. **Atomic Operations**: Race condition fix in API counter increments.
4. **Comprehensive Logging**: All errors logged for security auditing.

## Future Scalability
- **Async Processing**: If scanning takes too long, we can move `pipeline.py` to a background task (Celery/RQ).
- **LLM Integration**: We intentionally reserved LLM usage for *generating the pitch email*, not analyzing the HTML. This keeps the "scan" cheap and the "pitch" high-quality.
- **Database Migrations**: Ready for Flask-Migrate integration when schema evolves beyond v1.40.