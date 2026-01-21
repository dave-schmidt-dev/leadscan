import logging
import re
import socket
import ssl
import time
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# --- SSL Verification Helper ---
def check_ssl_valid(hostname, port=443, timeout=5):
    """
    Performs proper SSL certificate verification using socket connection.
    Returns True if the certificate is valid and trusted.
    """
    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname):
                return True
    except ssl.SSLCertVerificationError:
        return False
    except Exception as e:
        logger.debug(f"SSL check failed for {hostname}: {e}")
        return False


def analyze_url(url):
    """
    Analyzes a URL for connectivity, security, and technical heuristics.
    Returns a dictionary of results including status codes, tech stack, and load times.
    """
    if not url:
        return {"exists": False, "error": "No URL provided"}

    # Ensure URL has a schema
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    results = {
        "url": url,
        "exists": False,
        "ssl_active": False,
        "status_code": None,
        "final_url": None,
        "mobile_viewport": False,
        "contact_info_found": False,
        "copyright_year": None,
        "tech_stack": None,
        "load_time": None,
        "error": None,
        "logs": [],
    }

    try:
        # --- Phase 1: Connectivity & Performance ---
        results["logs"].append(f"📡 Connecting to {url}...")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        # First attempt with SSL verification enabled
        start_time = time.time()
        ssl_fetch_failed = False
        try:
            response = requests.get(url, timeout=10, verify=True, headers=headers)
        except requests.exceptions.SSLError:
            # Fallback: fetch without verification but note the SSL issue
            ssl_fetch_failed = True
            response = requests.get(url, timeout=10, verify=False, headers=headers)
            results["logs"].append("⚠️ SSL certificate verification failed during fetch")

        duration = int((time.time() - start_time) * 1000)
        results["load_time"] = duration

        # Fallback Logic: If deep link is 404, attempt to scan the root domain
        if response.status_code == 404:
            results["logs"].append("❌ Deep link returned 404. Trying root...")
            parsed_initial = urlparse(url)
            root_url = f"{parsed_initial.scheme}://{parsed_initial.netloc}/"
            if root_url != url:
                try:
                    root_response = requests.get(root_url, timeout=10, verify=not ssl_fetch_failed, headers=headers)
                    if root_response.status_code == 200:
                        results["logs"].append("✅ Root domain found.")
                        response = root_response
                        url = root_url
                    else:
                        results["logs"].append(f"❌ Root domain failed ({root_response.status_code}).")
                except requests.exceptions.SSLError:
                    root_response = requests.get(root_url, timeout=10, verify=False, headers=headers)
                    if root_response.status_code == 200:
                        results["logs"].append("✅ Root domain found (SSL issues).")
                        response = root_response
                        url = root_url
                        ssl_fetch_failed = True
                except Exception as e:
                    logger.warning(f"Root domain fallback failed: {e}")

        results["exists"] = True
        results["status_code"] = response.status_code
        results["final_url"] = response.url
        results["logs"].append(f"✅ Status: {response.status_code} | Speed: {duration}ms")

        # --- Phase 2: Security (SSL) - Proper Verification ---
        parsed = urlparse(results["final_url"])
        if parsed.scheme == "https":
            if ssl_fetch_failed:
                # We already know SSL verification failed
                results["ssl_active"] = False
                results["logs"].append("🔴 SSL: Invalid/Self-Signed Certificate")
            elif check_ssl_valid(parsed.netloc):
                results["ssl_active"] = True
                results["logs"].append("🟢 SSL: Valid Certificate")
            else:
                results["ssl_active"] = False
                results["logs"].append("🔴 SSL: Certificate Verification Failed")
        else:
            results["logs"].append("🔓 SSL: Not Secure (HTTP)")

        # --- Phase 3: Content & Heuristics ---
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            html_content = response.text.lower()

            # Tech Stack Detection
            results["logs"].append("🔍 Analyzing Tech Stack...")
            stack = []
            if "wp-content" in html_content:
                stack.append("WordPress")
            if "wix.com" in html_content or "_wix_" in html_content:
                stack.append("Wix")
            if "squarespace" in html_content:
                stack.append("Squarespace")
            if "shopify" in html_content:
                stack.append("Shopify")
            if "go daddy" in html_content or "godaddy" in html_content:
                stack.append("GoDaddy")

            results["tech_stack"] = ", ".join(stack) if stack else "Custom/Other"
            results["logs"].append(f"🛠️ Tech: {results['tech_stack']}")

            # Mobile Responsiveness
            viewport = soup.find("meta", attrs={"name": "viewport"})
            if viewport and "width=device-width" in str(viewport.get("content", "")).lower():
                results["mobile_viewport"] = True
                results["logs"].append("📱 Mobile: Optimized")
            else:
                results["logs"].append("📵 Mobile: Not Optimized")

            # Contact Information
            text_content = soup.get_text()
            email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
            phone_pattern = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"

            if re.search(email_pattern, text_content) or re.search(phone_pattern, text_content):
                results["contact_info_found"] = True
                results["logs"].append("✉️ Contact: Found on homepage")
            else:
                results["logs"].append("❓ Contact: Not found in text")

            # Copyright / Freshness
            footer_text = text_content[-2000:]
            match = re.search(r"(?:Copyright|©).*?(\d{4})", footer_text, re.IGNORECASE | re.DOTALL)
            if match:
                results["copyright_year"] = int(match.group(1))
                results["logs"].append(f"📅 Copyright: {results['copyright_year']}")

    except requests.exceptions.ConnectionError:
        results["error"] = "Connection failed (DNS or Server down)"
        results["logs"].append(f"❌ {results['error']}")
    except requests.exceptions.Timeout:
        results["error"] = "Timeout"
        results["logs"].append(f"❌ {results['error']}")
    except Exception as e:
        results["error"] = str(e)
        results["logs"].append(f"💥 Unexpected error: {str(e)}")

    return results
