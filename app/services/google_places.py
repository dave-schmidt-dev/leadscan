import requests
import os
import time
from app.models.config import AppConfig

def search_nearby(lat, lng, radius, keyword="business"):
    """
    Searches for places using Google Places Nearby Search API.
    radius in meters.
    If keyword is "business", performs an "Omni-Search" across multiple categories.
    Returns a list of simplified place dictionaries.
    """
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_PLACES_API_KEY not found in environment variables")

    # Omni-Search Logic
    keywords_to_search = [keyword]
    if keyword.lower() == "business":
        keywords_to_search = [
            "plumber", "electrician", "hvac", "dentist", "roofer", 
            "landscaper", "lawyer", "accountant", "pest control", "locksmith",
            "painter", "general contractor", "cleaning service", "auto repair",
            "veterinarian", "chiropractor", "physical therapy", "tree service",
            "fencing", "pool service", "handyman", "carpet cleaning",
            "moving company", "restoration service", "window cleaning", "solar installation"
        ]

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

    all_results = {} # Use dict for deduplication by place_id

    for kw in keywords_to_search:
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'keyword': kw,
            'key': api_key
        }

        try:
            while True:
                # Track API usage
                try:
                    AppConfig.increment('google_api_nearby')
                except Exception:
                    pass
                
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') not in ['OK', 'ZERO_RESULTS']:
                    print(f"❌ Google API Error ({kw}): {data.get('status')} - {data.get('error_message', 'No details')}")
                    break
                
                if 'results' in data:
                    for place in data['results']:
                        pid = place.get('place_id')
                        if pid in all_results:
                            continue

                        name_lower = place.get('name', '').lower()
                        place_types = place.get('types', [])
                        
                        if any(chain in name_lower for chain in CHAIN_BLOCKLIST):
                            continue
                            
                        if any(b_type in place_types for b_type in TYPE_BLOCKLIST):
                            continue

                        all_results[pid] = {
                            'place_id': pid,
                            'name': place.get('name'),
                            'address': place.get('vicinity'),
                            'rating': place.get('rating'),
                            'types': place_types
                        }
                
                if 'next_page_token' in data:
                    params = {'pagetoken': data['next_page_token'], 'key': api_key}
                    time.sleep(2) 
                else:
                    break
                    
        except Exception as e:
            print(f"Error fetching places for '{kw}': {e}")
            continue

    return list(all_results.values())

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