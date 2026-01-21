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
        'tech_stack': None,
        'load_time': None,
        'error': None,
        'logs': []
    }

    try:
        results['logs'].append(f"📡 Connecting to {url}...")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        start_time = time.time()
        response = requests.get(url, timeout=10, verify=False, headers=headers)
        duration = int((time.time() - start_time) * 1000)
        results['load_time'] = duration
        
        # Fallback: If deep link is 404, try root domain
        if response.status_code == 404:
            results['logs'].append("❌ Deep link returned 404. Trying root...")
            parsed_initial = urlparse(url)
            root_url = f"{parsed_initial.scheme}://{parsed_initial.netloc}/"
            if root_url != url:
                try:
                    root_response = requests.get(root_url, timeout=10, verify=False, headers=headers)
                    if root_response.status_code == 200:
                        results['logs'].append("✅ Root domain found.")
                        response = root_response
                        url = root_url
                    else:
                        results['logs'].append(f"❌ Root domain failed ({root_response.status_code}).")
                except:
                    pass

        results['exists'] = True
        results['status_code'] = response.status_code
        results['final_url'] = response.url
        results['logs'].append(f"✅ Status: {response.status_code} | Speed: {duration}ms")

        # Check SSL
        parsed = urlparse(results['final_url'])
        if parsed.scheme == 'https':
            try:
                requests.get(results['final_url'], timeout=5, headers=headers)
                results['ssl_active'] = True
                results['logs'].append("🟢 SSL: Valid Certificate")
            except:
                results['logs'].append("🔴 SSL: Invalid/Self-Signed")
        else:
            results['logs'].append("🔓 SSL: Not Secure (HTTP)")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            html_content = response.text.lower()
            
            # 1. Tech Stack Detection
            results['logs'].append("🔍 Analyzing Tech Stack...")
            stack = []
            if 'wp-content' in html_content: stack.append("WordPress")
            if 'wix.com' in html_content or '_wix_' in html_content: stack.append("Wix")
            if 'squarespace' in html_content: stack.append("Squarespace")
            if 'shopify' in html_content: stack.append("Shopify")
            if 'go daddy' in html_content or 'godaddy' in html_content: stack.append("GoDaddy")
            
            results['tech_stack'] = ", ".join(stack) if stack else "Custom/Other"
            results['logs'].append(f"🛠️ Tech: {results['tech_stack']}")

            # 2. Mobile Viewport
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport and 'width=device-width' in str(viewport.get('content', '')).lower():
                results['mobile_viewport'] = True
                results['logs'].append("📱 Mobile: Optimized (Viewport found)")
            else:
                results['logs'].append("📵 Mobile: Not Optimized")
            
            # 3. Contact Info
            text_content = soup.get_text()
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            
            if re.search(email_pattern, text_content) or re.search(phone_pattern, text_content):
                results['contact_info_found'] = True
                results['logs'].append("✉️ Contact: Found on homepage")
            else:
                results['logs'].append("❓ Contact: Not found in text")
                
            # 4. Copyright
            footer_text = text_content[-2000:]
            match = re.search(r'(?:Copyright|©).*?(\d{4})', footer_text, re.IGNORECASE | re.DOTALL)
            if match:
                results['copyright_year'] = int(match.group(1))
                results['logs'].append(f"📅 Copyright: {results['copyright_year']}")

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
