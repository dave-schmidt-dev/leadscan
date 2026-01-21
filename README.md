# LeadScan 🕵️‍♂️

**LeadScan** is a specialized "Lead Finder" tool designed to automate the discovery of local businesses with poor or missing web presence. It is built to streamline the sales pipeline for freelance web development.

**Current Version**: v1.40

## 🚀 Quick Start

1.  **Prerequisites**: Python 3.8+, Google Places API Key.
2.  **Setup**:
    ```bash
    # Run the automated setup script (macOS/Linux)
    chmod +x setup.sh
    ./setup.sh
    ```
3.  **Manual Start**:
    ```bash
    source venv/bin/activate
    python run.py
    ```
4.  **Access**: Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

## 🛠 Features

- **Expanded Omni-Search**: Search for "business" to trigger a multi-category scan across 26+ high-value trades (Plumbers, Lawyers, Solar, etc.). Categories are now configurable via `OMNI_SEARCH_CATEGORIES` environment variable.
- **Live Progress Modal**: Real-time terminal-style logging during area scans.
- **Bulk Web Analysis**:
    - **Tech Stack Detection**: Identifies WordPress, Wix, Squarespace, Shopify, and more.
    - **Performance Metrics**: Measures Time-to-First-Byte (TTFB).
    - **Security Analysis**: Proper SSL certificate verification with fallback handling.
    - **Heuristics**: Mobile Viewport detection and Contact Info regex.
- **CRM Workflow**: Track status from `Scraped` to `Won` with automatic timestamps.
- **Advanced Technical Logs**: Deep-dive analysis logs showing exact scan results and fallback attempts.
- **Input Validation**: Radius bounds (100m-50km) and keyword sanitization for security.

## 🔐 Configuration

Create a `.env` file in the root directory:
```ini
GOOGLE_PLACES_API_KEY=your_key_here
SECRET_KEY=dev_secret
DATABASE_URI=sqlite:///leadscan.db
DEFAULT_LAT=38.8118   # Your search center latitude
DEFAULT_LNG=-77.6372  # Your search center longitude

# Optional: Customize Omni-Search categories (comma-separated)
OMNI_SEARCH_CATEGORIES=plumber,electrician,hvac,dentist
```

## 🚀 Running Locally

1. **Setup**: Run `./setup.sh` to initialize the virtual environment and database.
2. **Start**: Run `./run.sh`.
3. **Access**: Open **`https://127.0.0.1:5000`** (Self-signed certificate is expected).

*Note: The app runs on HTTPS by default to support modern browsers like DuckDuckGo. You may need to click 'Advanced' -> 'Proceed' in your browser.*

## 📂 Project Structure

- `app/routes`: Web endpoints with input validation.
- `app/services`: Core logic (Google API, HTML Parsing, Pipeline) with comprehensive logging.
- `app/models`: Database schema (SQLite/SQLAlchemy) with indexed fields and timestamps.
- `app/templates`: HTML frontend (Dark Mode, Bootstrap 5).
- `tests/`: Comprehensive test suite (34 tests covering critical paths).

See [docs/DESIGN.md](docs/DESIGN.md) for architectural details.

## 🧪 Development

### Testing

Run the test suite:
```bash
source venv/bin/activate
pytest tests/ -v
```

Run tests with coverage:
```bash
pytest tests/ --cov=app --cov-report=term
```

**Test Coverage**:
- `test_analyzer.py`: 13 tests (SSL verification, heuristics detection)
- `test_google_places.py`: 9 tests (filtering, deduplication, API handling)
- `test_pipeline.py`: 7 tests (scoring, status transitions, error handling)
- `test_config.py`: 5 tests (atomic increment, monthly reset)

### Linting

The project uses [Ruff](https://github.com/astral-sh/ruff) for fast Python linting and formatting:

```bash
# Check code quality
ruff check app/ tests/

# Auto-fix issues
ruff check app/ tests/ --fix

# Format code
ruff format app/ tests/
```

### Git Hooks

Git hooks are automatically set up to maintain code quality:

- **Pre-commit**: Runs `ruff check` on staged Python files
- **Pre-push**: Runs full test suite before pushing to remote

These hooks prevent committing broken or poorly formatted code.

## 🔧 Recent Improvements (v1.40)

### Critical Security Fixes
- ✅ **SSL Verification**: Now properly validates SSL certificates (previously disabled with `verify=False`)
- ✅ **SSL Detection**: Uses socket-based verification instead of superficial checks
- ✅ **Race Condition Fix**: `AppConfig.increment()` now uses atomic SQL updates

### Key Enhancements
- ✅ **Input Validation**: Radius bounds (100m-50km) and keyword sanitization
- ✅ **Database Indexing**: Added index to `place_id` for faster queries
- ✅ **Comprehensive Logging**: Replaced silent exception handling with structured logging
- ✅ **Timestamps**: Added `created_at` and `analyzed_at` to Lead model
- ✅ **Configurable Categories**: Omni-Search categories now externalized to environment variables

## ⚠️ Disclaimer

This tool is designed for personal workflow optimization. It relies on the Google Places API, which has monthly quotas. Always monitor your API usage to avoid unexpected costs.
