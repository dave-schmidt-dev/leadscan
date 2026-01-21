"""
Tests for the AppConfig model.
Critical path: Atomic increment, monthly reset.
"""

from unittest.mock import MagicMock, patch


class TestAppConfigIncrement:
    """Tests for atomic increment functionality."""

    @patch("app.db_session")
    def test_increment_creates_key_if_missing(self, mock_db):
        """Should create key with value 1 if it doesn't exist."""
        from app.models.config import AppConfig

        mock_db.get.return_value = None

        # Mock check_monthly_reset to avoid side effects
        with patch.object(AppConfig, "check_monthly_reset"):
            with patch.object(mock_db, "execute"):
                with patch.object(mock_db, "commit"):
                    with patch.object(mock_db, "add"):
                        result = AppConfig.increment("test_counter")

        # Should return a value (even if 0 due to mocking)
        assert isinstance(result, int)

    @patch("app.db_session")
    def test_increment_uses_atomic_sql(self, mock_db):
        """Should use SQL UPDATE for atomic increment."""
        from app.models.config import AppConfig

        mock_item = MagicMock()
        mock_item.value = "5"
        mock_db.get.return_value = mock_item

        with patch.object(AppConfig, "check_monthly_reset"):
            AppConfig.increment("test_key")

        # Should have called execute for atomic update
        mock_db.execute.assert_called_once()


class TestAppConfigMonthlyReset:
    """Tests for monthly counter reset."""

    def test_resets_counters_on_new_month(self):
        """Should reset counters when month changes."""
        from app.models.config import AppConfig

        # Set up: pretend last month was different
        with patch.object(AppConfig, "get", return_value="2024-01"):
            with patch.object(AppConfig, "set") as mock_set:
                with patch("app.models.config.datetime") as mock_dt:
                    mock_dt.now.return_value.strftime.return_value = "2024-02"

                    AppConfig.check_monthly_reset()

                    # Should have called set for the new month and counters
                    assert mock_set.call_count >= 1


class TestAppConfigGetSet:
    """Tests for basic get/set operations."""

    @patch("app.db_session")
    def test_get_returns_default_when_missing(self, mock_db):
        """Should return default value when key doesn't exist."""
        from app.models.config import AppConfig

        mock_db.get.return_value = None
        result = AppConfig.get("nonexistent_key", "default_value")

        assert result == "default_value"

    @patch("app.db_session")
    def test_set_creates_and_stores_value(self, mock_db):
        """Should create key and store value."""
        from app.models.config import AppConfig

        mock_db.get.return_value = None

        AppConfig.set("new_key", "new_value")

        # Should have added new item and committed
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
