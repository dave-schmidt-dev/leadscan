import requests
import os
import time
from app.models.config import AppConfig

def search_nearby(lat, lng, radius, keyword="business"):
    """
    Searches for places using Google Places Nearby Search API.
    radius in meters.
    Returns a list of simplified place dictionaries.
    """
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_PLACES_API_KEY not found in environment variables")

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    
    # Common chains to exclude
    CHAIN_BLOCKLIST = [
        'walmart', 'target', 'mcdonald', 'starbucks', 'cvs', 'walgreens', 
        'subway', 'dunkin', 'domino', 'pizza hut', 'burger king', 'wendy',
        'taco bell', 'kfc', 'lowe', 'home depot', 'best buy', 'costco',
        'kroger', 'whole foods', 'safeway', '7-eleven', 'shell', 'bp', 'exxon',
        'sheetz', 'wawa', 'fedex', 'ups', 'usps', 'bank of america', 'wells fargo',
        'papa john', 'little caesar', 'checkers', 'sonic', 'arby', 'chipotle',
        'panda express', 'jersey mike', 'jimmy john', 'five guys', 'panera',
        'buffalo wild wings', 'dairy queen', 'popeye', 'bruster', 'firehouse',
        'ihop', 'applebee', 'denny', 'outback', 'red lobster', 'olive garden'
    ]
    
    # Types to exclude (big box stores, etc)
    TYPE_BLOCKLIST = [
        'supermarket', 'department_store', 'shopping_mall', 'gas_station', 'atm'
    ]

    results = []
    params = {
        'location': f"{lat},{lng}",
        'radius': radius,
        'keyword': keyword,
        'key': api_key
    }

    try:
        while True:
            # Track API usage
            try:
                AppConfig.increment('google_api_nearby')
            except Exception:
                pass # Don't fail search if stats fail
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Check for API-level errors
            if data.get('status') not in ['OK', 'ZERO_RESULTS']:
                print(f"❌ Google API Error: {data.get('status')} - {data.get('error_message', 'No details')}")
                break # Stop searching this keyword
            
            if 'results' in data:
                for place in data['results']:
                    name_lower = place.get('name', '').lower()
                    place_types = place.get('types', [])
                    
                    # 1. Filter Chains
                    if any(chain in name_lower for chain in CHAIN_BLOCKLIST):
                        continue
                        
                    # 2. Filter Types
                    if any(b_type in place_types for b_type in TYPE_BLOCKLIST):
                        continue

                    results.append({
                        'place_id': place.get('place_id'),
                        'name': place.get('name'),
                        'address': place.get('vicinity'), # Nearby search uses 'vicinity'
                        'rating': place.get('rating'),
                        'types': place_types
                    })
            
            # Handle pagination
            if 'next_page_token' in data:
                params = {'pagetoken': data['next_page_token'], 'key': api_key}
                # Must wait a short time for token to become valid
                time.sleep(2) 
            else:
                break
                
    except Exception as e:
        print(f"Error fetching places: {e}")
        return []

    return results

def get_place_details(place_id):
    """
    Fetches full details (website, phone) for a specific place.
    """
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    
    params = {
        'place_id': place_id,
        'fields': 'name,formatted_phone_number,website,url,formatted_address',
        'key': api_key
    }
    
    try:
        # Track API usage
        try:
            AppConfig.increment('google_api_details')
        except Exception:
            pass

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get('result', {})
    except Exception as e:
        print(f"Error fetching place details: {e}")
        return {}