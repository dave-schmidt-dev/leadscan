# LeadScan 🕵️‍♂️

**LeadScan** is a specialized "Lead Finder" tool designed to automate the discovery of local businesses with poor or missing web presence. It is built to streamline the sales pipeline for freelance web development.

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

- **Expanded Omni-Search**: Search for "business" to trigger a multi-category scan across 26 high-value trades (Plumbers, Lawyers, Solar, etc.).
- **Live Progress Modal**: Real-time terminal-style logging during area scans.
- **Bulk Web Analysis**:
    - **Tech Stack Detection**: Identifies WordPress, Wix, Squarespace, Shopify, and more.
    - **Performance Metrics**: Measures Time-to-First-Byte (TTFB).
    - **Heuristics**: SSL validation, Mobile Viewport detection, and Contact Info regex.
- **CRM Workflow**: Track status from `Scraped` to `Won`.
- **Advanced Technical Logs**: Deep-dive analysis logs showing exact scan results and fallback attempts.

## 🔐 Configuration

Create a `.env` file in the root directory:
```ini
GOOGLE_PLACES_API_KEY=your_key_here
SECRET_KEY=dev_secret
DATABASE_URI=sqlite:///leadscan.db
DEFAULT_LAT=38.8118   # Your search center latitude
DEFAULT_LNG=-77.6372  # Your search center longitude
```

## 🚀 Running Locally

1. **Setup**: Run `./setup.sh` to initialize the virtual environment and database.
2. **Start**: Run `./run.sh`.
3. **Access**: Open **`https://127.0.0.1:5000`** (Self-signed certificate is expected).

*Note: The app runs on HTTPS by default to support modern browsers like DuckDuckGo. You may need to click 'Advanced' -> 'Proceed' in your browser.*

## 📂 Project Structure

- `app/routes`: Web endpoints.
- `app/services`: Core logic (Google API, HTML Parsing, Pipeline).
- `app/models`: Database schema (SQLite/SQLAlchemy).
- `app/templates`: HTML frontend (Dark Mode, Bootstrap 5).

See [docs/DESIGN.md](docs/DESIGN.md) for architectural details.

## ⚠️ Disclaimer

This tool is designed for personal workflow optimization. It relies on the Google Places API, which has monthly quotas. Always monitor your API usage to avoid unexpected costs.

