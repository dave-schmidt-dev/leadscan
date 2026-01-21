"""
Tests for the Google Places service.
Critical path: Filtering, deduplication, API tracking.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.google_places import get_omni_categories, get_place_details, search_nearby


class TestOmniCategories:
    """Tests for category configuration."""

    def test_get_omni_categories_returns_default(self):
        """Should return default categories when env var not set."""
        with patch.dict("os.environ", {}, clear=True):
            categories = get_omni_categories()
            assert "plumber" in categories
            assert "electrician" in categories
            assert len(categories) == 81  # Expanded comprehensive list

    def test_get_omni_categories_uses_env_override(self):
        """Should use environment variable when set."""
        with patch.dict("os.environ", {"OMNI_SEARCH_CATEGORIES": "plumber,electrician,hvac"}):
            categories = get_omni_categories()
            assert categories == ["plumber", "electrician", "hvac"]


class TestSearchFiltering:
    """Tests for chain and type blocklist filtering."""

    @patch("app.services.google_places.requests.get")
    @patch("app.services.google_places.AppConfig.increment")
    def test_filters_chain_businesses(self, mock_increment, mock_get):
        """Should filter out chain businesses like McDonald's."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {"place_id": "1", "name": "McDonalds Store #123", "vicinity": "123 Main St", "types": ["restaurant"]},
                {"place_id": "2", "name": "Local Plumber Joe", "vicinity": "456 Oak Ave", "types": ["plumber"]},
            ],
        }
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "test-key"}):
            results = list(search_nearby(37.7749, -122.4194, 1000, "plumber"))

        # Should only yield the local plumber, not McDonald's
        result_items = [r for r in results if r[0] == "result"]
        assert len(result_items) == 1
        assert result_items[0][1]["name"] == "Local Plumber Joe"

    @patch("app.services.google_places.requests.get")
    @patch("app.services.google_places.AppConfig.increment")
    def test_filters_type_blocklist(self, mock_increment, mock_get):
        """Should filter out blocklisted place types."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {
                    "place_id": "1",
                    "name": "Big Supermarket",
                    "vicinity": "123 Main St",
                    "types": ["supermarket", "store"],
                },
                {"place_id": "2", "name": "Corner Store Fix", "vicinity": "456 Oak Ave", "types": ["store"]},
            ],
        }
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "test-key"}):
            results = list(search_nearby(37.7749, -122.4194, 1000, "store"))

        result_items = [r for r in results if r[0] == "result"]
        assert len(result_items) == 1
        assert result_items[0][1]["name"] == "Corner Store Fix"

    @patch("app.services.google_places.requests.get")
    @patch("app.services.google_places.AppConfig.increment")
    def test_deduplicates_across_categories(self, mock_increment, mock_get):
        """Should not return same place_id twice across categories."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "status": "OK",
            "results": [
                {"place_id": "same-id", "name": "Multi-Service Shop", "vicinity": "123 Main St", "types": ["store"]},
            ],
        }
        mock_get.return_value = mock_response

        with patch.dict(
            "os.environ", {"GOOGLE_PLACES_API_KEY": "test-key", "OMNI_SEARCH_CATEGORIES": "plumber,electrician"}
        ):
            results = list(search_nearby(37.7749, -122.4194, 1000, "business"))

        result_items = [r for r in results if r[0] == "result"]
        # Should only appear once despite being searched in 2 categories
        assert len(result_items) == 1


class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_raises_error_without_api_key(self):
        """Should raise ValueError if API key not configured."""
        with patch.dict("os.environ", {}, clear=True):
            if "GOOGLE_PLACES_API_KEY" in __import__("os").environ:
                del __import__("os").environ["GOOGLE_PLACES_API_KEY"]

            with pytest.raises(ValueError, match="GOOGLE_PLACES_API_KEY"):
                list(search_nearby(37.7749, -122.4194, 1000, "plumber"))

    @patch("app.services.google_places.requests.get")
    @patch("app.services.google_places.AppConfig.increment")
    def test_handles_api_error_status(self, mock_increment, mock_get):
        """Should log error and continue on API error status."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "REQUEST_DENIED", "error_message": "Invalid API key"}
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "bad-key"}):
            results = list(search_nearby(37.7749, -122.4194, 1000, "plumber"))

        log_items = [r for r in results if r[0] == "log"]
        assert any("Google API Error" in r[1] for r in log_items)


class TestGetPlaceDetails:
    """Tests for place details fetching."""

    @patch("app.services.google_places.requests.get")
    @patch("app.services.google_places.AppConfig.increment")
    def test_returns_details_on_success(self, mock_increment, mock_get):
        """Should return place details dict on success."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": {"formatted_phone_number": "(555) 123-4567", "website": "https://example.com"}
        }
        mock_get.return_value = mock_response

        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "test-key"}):
            result = get_place_details("test-place-id")

        assert result["formatted_phone_number"] == "(555) 123-4567"
        assert result["website"] == "https://example.com"

    @patch("app.services.google_places.requests.get")
    @patch("app.services.google_places.AppConfig.increment")
    def test_returns_empty_dict_on_error(self, mock_increment, mock_get):
        """Should return empty dict on API error."""
        mock_get.side_effect = Exception("Network error")

        with patch.dict("os.environ", {"GOOGLE_PLACES_API_KEY": "test-key"}):
            result = get_place_details("test-place-id")

        assert result == {}
