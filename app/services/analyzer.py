import requests
from urllib.parse import urlparse
import socket
import ssl
from bs4 import BeautifulSoup
import re
import datetime

def analyze_url(url):
    """
    Analyzes a URL for connectivity, SSL, and basic heuristics.
    Returns a dictionary of results.
    """
    if not url:
        return {
            'exists': False,
            'error': 'No URL provided'
        }

    # Ensure schema
    if not url.startswith(('http://', 'https://')):
        url = 'http://' + url

    results = {
        'url': url,
        'exists': False,
        'ssl_active': False,
        'status_code': None,
        'final_url': None,
        'mobile_viewport': False,
        'contact_info_found': False,
        'copyright_year': None,
        'error': None,
        'logs': []
    }

    try:
        results['logs'].append(f"📡 Initiating connection to {url}")
        # Check basic connectivity and follow redirects
        # Headers to mimic browser (avoids some 403s)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=10, verify=False, headers=headers)
        
        # Fallback: If deep link is 404, try root domain
        if response.status_code == 404:
            results['logs'].append("❌ Deep link returned 404")
            parsed_initial = urlparse(url)
            root_url = f"{parsed_initial.scheme}://{parsed_initial.netloc}/"
            if root_url != url:
                results['logs'].append(f"🔄 Falling back to root domain: {root_url}")
                try:
                    root_response = requests.get(root_url, timeout=10, verify=False, headers=headers)
                    if root_response.status_code == 200:
                        results['logs'].append("✅ Root domain connection successful")
                        response = root_response
                        url = root_url
                    else:
                        results['logs'].append(f"❌ Root domain also failed with status {root_response.status_code}")
                except Exception as e:
                    results['logs'].append(f"⚠️ Root domain fallback failed: {str(e)}")

        results['exists'] = True
        results['status_code'] = response.status_code
        results['final_url'] = response.url
        results['logs'].append(f"✅ Connection established (Status: {response.status_code})")

        # Check SSL on final URL
        parsed = urlparse(results['final_url'])
        if parsed.scheme == 'https':
            results['logs'].append("🔐 Checking SSL certificate...")
            try:
                # Explicitly verify SSL handshake
                requests.get(results['final_url'], timeout=5, headers=headers)
                results['ssl_active'] = True
                results['logs'].append("🟢 SSL verified and valid")
            except requests.exceptions.SSLError:
                results['ssl_active'] = False
                results['logs'].append("🔴 SSL certificate invalid or self-signed")
        else:
            results['logs'].append("🔓 Site is running on insecure HTTP")
        
        # --- Heuristics Analysis ---
        if response.status_code == 200:
            results['logs'].append("📄 Parsing HTML for heuristics...")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Mobile Viewport
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport and 'width=device-width' in str(viewport.get('content', '')).lower():
                results['mobile_viewport'] = True
                results['logs'].append("📱 Mobile viewport tag found")
            else:
                results['logs'].append("📵 No mobile viewport tag detected")
            
            # 2. Contact Info (Email/Phone)
            text_content = soup.get_text()
            # Simple regex for email
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            # Simple regex for phone (US formats)
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            
            email_found = re.search(email_pattern, text_content)
            phone_found = re.search(phone_pattern, text_content)
            
            if email_found or phone_found:
                results['contact_info_found'] = True
                contact_type = []
                if email_found: contact_type.append("Email")
                if phone_found: contact_type.append("Phone")
                results['logs'].append(f"✉️ Contact info found: {', '.join(contact_type)}")
            else:
                results['logs'].append("❓ No easy-to-find contact info detected in text")
                
            # 3. Copyright Year
            # Look for "Copyright" or "©" followed by 4 digits
            footer_text = text_content[-2000:] # Check last 2000 chars roughly
            copyright_pattern = r'(?:Copyright|©).*?(\d{4})'
            match = re.search(copyright_pattern, footer_text, re.IGNORECASE | re.DOTALL)
            if match:
                results['copyright_year'] = int(match.group(1))
                results['logs'].append(f"📅 Copyright year detected: {results['copyright_year']}")

    except requests.exceptions.ConnectionError:
        err = 'Connection failed (DNS or Server down)'
        results['error'] = err
        results['logs'].append(f"❌ {err}")
    except requests.exceptions.Timeout:
        err = 'Timeout'
        results['error'] = err
        results['logs'].append(f"❌ {err}")
    except Exception as e:
        results['error'] = str(e)
        results['logs'].append(f"💥 Unexpected error: {str(e)}")

    return results
