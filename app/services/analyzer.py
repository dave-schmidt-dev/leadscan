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
        'error': None
    }

    try:
        # Check basic connectivity and follow redirects
        # Headers to mimic browser (avoids some 403s)
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=10, verify=False, headers=headers)
        results['exists'] = True
        results['status_code'] = response.status_code
        results['final_url'] = response.url

        # Check SSL on final URL
        parsed = urlparse(results['final_url'])
        if parsed.scheme == 'https':
            try:
                # Explicitly verify SSL handshake
                requests.get(results['final_url'], timeout=5, headers=headers)
                results['ssl_active'] = True
            except requests.exceptions.SSLError:
                results['ssl_active'] = False
        
        # --- Heuristics Analysis ---
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. Mobile Viewport
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            if viewport and 'width=device-width' in str(viewport.get('content', '')).lower():
                results['mobile_viewport'] = True
            
            # 2. Contact Info (Email/Phone)
            text_content = soup.get_text()
            # Simple regex for email
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            # Simple regex for phone (US formats)
            phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
            
            if re.search(email_pattern, text_content) or re.search(phone_pattern, text_content):
                results['contact_info_found'] = True
                
            # 3. Copyright Year
            # Look for "Copyright" or "©" followed by 4 digits
            footer_text = text_content[-2000:] # Check last 2000 chars roughly
            copyright_pattern = r'(?:Copyright|©).*?(\d{4})'
            match = re.search(copyright_pattern, footer_text, re.IGNORECASE | re.DOTALL)
            if match:
                results['copyright_year'] = int(match.group(1))

    except requests.exceptions.ConnectionError:
        results['error'] = 'Connection failed (DNS or Server down)'
    except requests.exceptions.Timeout:
        results['error'] = 'Timeout'
    except Exception as e:
        results['error'] = str(e)

    return results
