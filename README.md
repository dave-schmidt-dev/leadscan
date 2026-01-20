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

## 🔑 Configuration

Create a `.env` file in the root directory:
```ini
GOOGLE_PLACES_API_KEY=your_key_here
SECRET_KEY=dev_secret
DATABASE_URI=sqlite:///leadscan.db
```

## 🛠 Features

- **Omni-Search**: Typing "business" triggers a multi-category scan (Plumbers, Electricians, Dentists, etc.) to maximize lead discovery.
- **Smart Filtering**: Automatically ignores major chains (Walmart, Starbucks, etc.) and gas stations.
- **Web Analysis Engine**:
    - Checks if website exists (DNS/404).
    - Checks for SSL/HTTPS.
    - **Heuristics**: Scans for "Mobile Viewport" tags and easy-to-find contact info.
- **CRM Lite**:
    - Tracks status: `Scraped` → `Analyzed` → `Contacted` → `Won` / `Lost` / `Good Condition`.
    - **Ignored** status hides junk leads permanently.
    - **Reset DB**: Danger zone feature to wipe leads while preserving API stats.
- **API Quota Management**: Tracks monthly usage for "Nearby Search" vs "Place Details" limits.

## 📂 Project Structure

- `app/routes`: Web endpoints.
- `app/services`: Core logic (Google API, HTML Parsing, Pipeline).
- `app/models`: Database schema (SQLite/SQLAlchemy).
- `app/templates`: HTML frontend (Dark Mode, Bootstrap 5).

See [docs/DESIGN.md](docs/DESIGN.md) for architectural details.

## ⚠️ Disclaimer

This tool is designed for personal workflow optimization. It relies on the Google Places API, which has monthly quotas. Always monitor your API usage to avoid unexpected costs.

