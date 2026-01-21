import logging
import os
import time

import requests

from app.models.config import AppConfig

logger = logging.getLogger(__name__)

# Default high-value trade categories for Omni-Search
DEFAULT_OMNI_CATEGORIES = [
    "plumber",
    "electrician",
    "hvac",
    "dentist",
    "roofer",
    "landscaper",
    "lawyer",
    "accountant",
    "pest control",
    "locksmith",
    "painter",
    "general contractor",
    "cleaning service",
    "auto repair",
    "veterinarian",
    "chiropractor",
    "physical therapy",
    "tree service",
    "fencing",
    "pool service",
    "handyman",
    "carpet cleaning",
    "moving company",
    "restoration service",
    "window cleaning",
    "solar installation",
]


def get_omni_categories():
    """
    Returns the list of categories for Omni-Search.
    Can be overridden via OMNI_SEARCH_CATEGORIES environment variable.
    """
    env_categories = os.environ.get("OMNI_SEARCH_CATEGORIES")
    if env_categories:
        return [c.strip() for c in env_categories.split(",") if c.strip()]
    return DEFAULT_OMNI_CATEGORIES


def search_nearby(lat, lng, radius, keyword="business"):
    """
    Searches for places using Google Places Nearby Search API.
    If keyword is 'business', performs an Omni-Search across high-value categories.
    Yields: ('log', message) OR ('result', place_dict) for real-time progress.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_PLACES_API_KEY not found in environment variables")

    # --- Search Configuration ---
    keywords_to_search = [keyword]
    if keyword.lower() == "business":
        keywords_to_search = get_omni_categories()

    # --- Blocklists (Chains & Junk) ---
    CHAIN_BLOCKLIST = [
        "walmart",
        "target",
        "mcdonald",
        "starbucks",
        "cvs",
        "walgreens",
        "subway",
        "dunkin",
        "domino",
        "pizza hut",
        "burger king",
        "wendy",
        "taco bell",
        "kfc",
        "lowe",
        "home depot",
        "best buy",
        "costco",
        "kroger",
        "whole foods",
        "safeway",
        "7-eleven",
        "shell",
        "bp",
        "exxon",
        "sheetz",
        "wawa",
        "fedex",
        "ups",
        "usps",
        "bank of america",
        "wells fargo",
        "papa john",
        "little caesar",
        "checkers",
        "sonic",
        "arby",
        "chipotle",
        "panda express",
        "jersey mike",
        "jimmy john",
        "five guys",
        "panera",
        "buffalo wild wings",
        "dairy queen",
        "popeye",
        "bruster",
        "firehouse",
        "ihop",
        "applebee",
        "denny",
        "outback",
        "red lobster",
        "olive garden",
    ]

    TYPE_BLOCKLIST = ["supermarket", "department_store", "shopping_mall", "gas_station", "atm"]

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    processed_pids = set()  # Track place_ids to prevent duplicates across categories

    # --- Search Loop ---
    for kw in keywords_to_search:
        yield ("log", f"🔍 Scanning category: {kw.title()}...")
        params = {"location": f"{lat},{lng}", "radius": radius, "keyword": kw, "key": api_key}

        try:
            while True:
                # Track API usage statistics
                try:
                    AppConfig.increment("google_api_nearby")
                except Exception as e:
                    logger.warning(f"Failed to increment API counter: {e}")

                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                if data.get("status") not in ["OK", "ZERO_RESULTS"]:
                    yield ("log", f"❌ Google API Error ({kw}): {data.get('status')}")
                    break

                found_in_batch = 0
                if "results" in data:
                    for place in data["results"]:
                        pid = place.get("place_id")
                        if pid in processed_pids:
                            continue

                        name_lower = place.get("name", "").lower()
                        place_types = place.get("types", [])

                        # Apply filtering
                        if any(chain in name_lower for chain in CHAIN_BLOCKLIST):
                            continue
                        if any(b_type in place_types for b_type in TYPE_BLOCKLIST):
                            continue

                        processed_pids.add(pid)
                        found_in_batch += 1
                        yield (
                            "result",
                            {
                                "place_id": pid,
                                "name": place.get("name"),
                                "address": place.get("vicinity"),
                                "rating": place.get("rating"),
                                "types": place_types,
                            },
                        )

                if found_in_batch > 0:
                    yield ("log", f"  ✨ Found {found_in_batch} unique leads")

                # Handle Google API pagination
                if "next_page_token" in data:
                    params = {"pagetoken": data["next_page_token"], "key": api_key}
                    time.sleep(2)  # Mandatory delay for token activation
                else:
                    break

        except Exception as e:
            yield ("log", f"⚠️ Error fetching {kw}: {str(e)}")
            continue

    yield ("log", "🏁 Scan complete.")


def get_place_details(place_id):
    """
    Fetches full contact details (website, phone) for a specific place.
    """
    api_key = os.environ.get("GOOGLE_PLACES_API_KEY")
    url = "https://maps.googleapis.com/maps/api/place/details/json"

    params = {
        "place_id": place_id,
        "fields": "name,formatted_phone_number,website,url,formatted_address",
        "key": api_key,
    }

    try:
        # Track API usage statistics
        try:
            AppConfig.increment("google_api_details")
        except Exception as e:
            logger.warning(f"Failed to increment API counter: {e}")

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("result", {})
    except Exception as e:
        logger.error(f"Failed to fetch place details for {place_id}: {e}")
        return {}
