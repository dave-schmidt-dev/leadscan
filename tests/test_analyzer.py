"""
Tests for the website analyzer service.
Critical path: SSL verification, heuristics detection.
"""

from unittest.mock import MagicMock, patch

from app.services.analyzer import analyze_url, check_ssl_valid


class TestSSLVerification:
    """Tests for SSL certificate verification."""

    def test_check_ssl_valid_returns_false_for_invalid_host(self):
        """SSL check should return False for non-existent hosts."""
        result = check_ssl_valid("invalid.host.that.does.not.exist.example")
        assert result is False

    @patch("app.services.analyzer.socket.create_connection")
    @patch("app.services.analyzer.ssl.create_default_context")
    def test_check_ssl_valid_returns_true_for_valid_cert(self, mock_context, mock_conn):
        """SSL check should return True when certificate validates."""
        mock_sock = MagicMock()
        mock_conn.return_value.__enter__ = MagicMock(return_value=mock_sock)
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)

        mock_ssl_sock = MagicMock()
        mock_context.return_value.wrap_socket.return_value.__enter__ = MagicMock(return_value=mock_ssl_sock)
        mock_context.return_value.wrap_socket.return_value.__exit__ = MagicMock(return_value=False)

        result = check_ssl_valid("example.com")
        assert result is True


class TestAnalyzeUrl:
    """Tests for the main URL analysis function."""

    def test_analyze_url_returns_error_for_empty_url(self):
        """Should return error dict for empty URL."""
        result = analyze_url("")
        assert result["exists"] is False
        assert result["error"] == "No URL provided"

    def test_analyze_url_returns_error_for_none_url(self):
        """Should return error dict for None URL."""
        result = analyze_url(None)
        assert result["exists"] is False
        assert result["error"] == "No URL provided"

    def test_analyze_url_adds_http_scheme(self):
        """Should add http:// to URLs without scheme."""
        with patch("app.services.analyzer.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.url = "http://example.com"
            mock_response.text = "<html></html>"
            mock_get.return_value = mock_response

            analyze_url("example.com")

            # First call should be to http://example.com
            call_args = mock_get.call_args_list[0]
            assert call_args[0][0] == "http://example.com"

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_detects_wordpress(self, mock_get):
        """Should detect WordPress from wp-content in HTML."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://example.com"
        mock_response.text = '<html><link href="/wp-content/themes/theme.css"></html>'
        mock_get.return_value = mock_response

        result = analyze_url("http://example.com")

        assert "WordPress" in result["tech_stack"]

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_detects_wix(self, mock_get):
        """Should detect Wix from wix.com in HTML."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://example.com"
        mock_response.text = '<html><script src="https://static.wix.com/script.js"></script></html>'
        mock_get.return_value = mock_response

        result = analyze_url("http://example.com")

        assert "Wix" in result["tech_stack"]

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_detects_mobile_viewport(self, mock_get):
        """Should detect mobile-optimized viewport meta tag."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://example.com"
        mock_response.text = (
            '<html><head><meta name="viewport" content="width=device-width, initial-scale=1"></head></html>'
        )
        mock_get.return_value = mock_response

        result = analyze_url("http://example.com")

        assert result["mobile_viewport"] is True

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_detects_contact_email(self, mock_get):
        """Should detect email addresses in page content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://example.com"
        mock_response.text = "<html><body>Contact us at info@example.com</body></html>"
        mock_get.return_value = mock_response

        result = analyze_url("http://example.com")

        assert result["contact_info_found"] is True

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_detects_contact_phone(self, mock_get):
        """Should detect phone numbers in page content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://example.com"
        mock_response.text = "<html><body>Call us: (555) 123-4567</body></html>"
        mock_get.return_value = mock_response

        result = analyze_url("http://example.com")

        assert result["contact_info_found"] is True

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_extracts_copyright_year(self, mock_get):
        """Should extract copyright year from page footer."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.url = "http://example.com"
        mock_response.text = "<html><body><footer>© 2024 Example Corp</footer></body></html>"
        mock_get.return_value = mock_response

        result = analyze_url("http://example.com")

        assert result["copyright_year"] == 2024

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_handles_connection_error(self, mock_get):
        """Should handle connection errors gracefully."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = analyze_url("http://example.com")

        assert result["exists"] is False
        assert "Connection failed" in result["error"]

    @patch("app.services.analyzer.requests.get")
    def test_analyze_url_handles_timeout(self, mock_get):
        """Should handle timeout errors gracefully."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()

        result = analyze_url("http://example.com")

        assert result["exists"] is False
        assert result["error"] == "Timeout"
