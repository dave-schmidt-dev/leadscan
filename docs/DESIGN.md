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

## Architecture

### The Monolith
We chose a **Flask Monolith** pattern.
- **Why?** Simplifies deployment and development. Logic and UI live together.
- **State**: Managed via server-side rendering (Jinja2) and SQLite.

### The Pipeline
Data flows through the system in this order:

1.  **Ingestion (`google_places.py`)**
    - **Omni-Search**: If keyword="business", iterates through 8+ high-value trade categories.
    - **Filtering**: Checks result against `CHAIN_BLOCKLIST` (Walmart, Starbucks) and `TYPE_BLOCKLIST` (Gas Stations).
    - **Deduplication**: Checks DB for existing `place_id`. If unique -> Create `Lead` (Status: Scraped).

2.  **Enrichment (`pipeline.py` & `analyzer.py`)**
    - Triggered manually via "Analyze" button.
    - **Deep Fetch**: Call Google Details API for Phone/Website.
    - **Connectivity**: `requests.get()` to check if site is up.
    - **Security**: Verify SSL certificate.
    - **Content Analysis**:
        - `Mobile`: Check for `<meta name="viewport" ...>`.
        - `Contact`: Regex scan for emails/phone patterns.
        - `Freshness`: Regex scan for copyright year in footer.
    - **Status Update**: Automatically moves lead from `Scraped` -> `Analyzed`.

3.  **Presentation (UI)**
    - Leads grouped by Status.
    - Badges (Red/Green) allow user to instantly spot "low hanging fruit".
    - "Ignored" leads are hidden but retained in DB to prevent re-scanning.

## Database Schema (`Lead` Model)

- **Identity**: `place_id` (Google Unique ID).
- **Contact**: `name`, `phone`, `address`, `website_url`.
- **Metrics**: `ssl_active`, `mobile_viewport`, `contact_info_found`, `copyright_year`, `content_heuristic_score`.
- **Workflow**: `status` (Enum), `notes` (Text).

## API Quota Management (`AppConfig` Model)
- Tracks `google_api_nearby` and `google_api_details` separately.
- Auto-resets on the 1st of every month.
- Stats persist even if "Reset DB" is clicked (via backup/restore logic).

## Future Scalability
- **Async Processing**: If scanning takes too long, we can move `pipeline.py` to a background task (Celery/RQ).
- **LLM Integration**: We intentionally reserved LLM usage for *generating the pitch email*, not analyzing the HTML. This keeps the "scan" cheap and the "pitch" high-quality.