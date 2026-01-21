"""
Tests for the analysis pipeline.
Critical path: Scoring, status transitions.
"""
from unittest.mock import MagicMock, patch

from app.models.lead import LeadStatus


class TestPipelineScoring:
    """Tests for lead scoring logic."""

    @patch('app.db_session')
    @patch('app.services.pipeline.get_place_details')
    @patch('app.services.pipeline.analyze_url')
    @patch('app.services.pipeline.Lead')
    def test_calculates_full_score_for_good_site(
        self, mock_lead_class, mock_analyze, mock_details, mock_db
    ):
        """Should give 100 score for site with all positive signals."""
        from app.services.pipeline import process_lead_analysis

        # Set up mock lead
        mock_lead = MagicMock()
        mock_lead.place_id = 'test-id'
        mock_lead.website_url = 'https://example.com'
        mock_lead.status = LeadStatus.SCRAPED
        mock_lead_class.query.get.return_value = mock_lead

        mock_details.return_value = {'website': 'https://example.com'}
        mock_analyze.return_value = {
            'exists': True,
            'ssl_active': True,
            'mobile_viewport': True,
            'contact_info_found': True,
            'logs': [],
        }

        process_lead_analysis(1)

        # Score should be 100 (25 * 4)
        assert mock_lead.content_heuristic_score == 100

    @patch('app.db_session')
    @patch('app.services.pipeline.get_place_details')
    @patch('app.services.pipeline.analyze_url')
    @patch('app.services.pipeline.Lead')
    def test_calculates_partial_score_for_poor_site(
        self, mock_lead_class, mock_analyze, mock_details, mock_db
    ):
        """Should give lower score for site missing features."""
        from app.services.pipeline import process_lead_analysis

        mock_lead = MagicMock()
        mock_lead.place_id = 'test-id'
        mock_lead.website_url = 'http://example.com'
        mock_lead.status = LeadStatus.SCRAPED
        mock_lead_class.query.get.return_value = mock_lead

        mock_details.return_value = {'website': 'http://example.com'}
        mock_analyze.return_value = {
            'exists': True,
            'ssl_active': False,  # No SSL
            'mobile_viewport': False,  # Not mobile optimized
            'contact_info_found': True,
            'logs': [],
        }

        process_lead_analysis(1)

        # Score should be 50 (exists=25 + contact=25)
        assert mock_lead.content_heuristic_score == 50


class TestPipelineStatusTransition:
    """Tests for lead status workflow."""

    @patch('app.db_session')
    @patch('app.services.pipeline.get_place_details')
    @patch('app.services.pipeline.analyze_url')
    @patch('app.services.pipeline.Lead')
    def test_transitions_scraped_to_analyzed(
        self, mock_lead_class, mock_analyze, mock_details, mock_db
    ):
        """Should move lead from Scraped to Analyzed status."""
        from app.services.pipeline import process_lead_analysis

        mock_lead = MagicMock()
        mock_lead.place_id = 'test-id'
        mock_lead.website_url = 'https://example.com'
        mock_lead.status = LeadStatus.SCRAPED
        mock_lead_class.query.get.return_value = mock_lead

        mock_details.return_value = {}
        mock_analyze.return_value = {'exists': True, 'logs': []}

        process_lead_analysis(1)

        assert mock_lead.status == LeadStatus.ANALYZED

    @patch('app.db_session')
    @patch('app.services.pipeline.get_place_details')
    @patch('app.services.pipeline.analyze_url')
    @patch('app.services.pipeline.Lead')
    def test_does_not_change_non_scraped_status(
        self, mock_lead_class, mock_analyze, mock_details, mock_db
    ):
        """Should not change status if already past Scraped."""
        from app.services.pipeline import process_lead_analysis

        mock_lead = MagicMock()
        mock_lead.place_id = 'test-id'
        mock_lead.website_url = 'https://example.com'
        mock_lead.status = LeadStatus.CONTACTED  # Already advanced
        mock_lead_class.query.get.return_value = mock_lead

        mock_details.return_value = {}
        mock_analyze.return_value = {'exists': True, 'logs': []}

        process_lead_analysis(1)

        # Status should remain CONTACTED
        assert mock_lead.status == LeadStatus.CONTACTED

    @patch('app.db_session')
    @patch('app.services.pipeline.get_place_details')
    @patch('app.services.pipeline.analyze_url')
    @patch('app.services.pipeline.Lead')
    def test_sets_analyzed_at_timestamp(
        self, mock_lead_class, mock_analyze, mock_details, mock_db
    ):
        """Should set analyzed_at timestamp."""
        from app.services.pipeline import process_lead_analysis

        mock_lead = MagicMock()
        mock_lead.place_id = 'test-id'
        mock_lead.website_url = 'https://example.com'
        mock_lead.status = LeadStatus.SCRAPED
        mock_lead.analyzed_at = None
        mock_lead_class.query.get.return_value = mock_lead

        mock_details.return_value = {}
        mock_analyze.return_value = {'exists': True, 'logs': []}

        process_lead_analysis(1)

        assert mock_lead.analyzed_at is not None


class TestPipelineErrorHandling:
    """Tests for pipeline error handling."""

    @patch('app.db_session')
    @patch('app.services.pipeline.Lead')
    def test_returns_false_for_missing_lead(self, mock_lead_class, mock_db):
        """Should return False if lead doesn't exist."""
        from app.services.pipeline import process_lead_analysis

        mock_lead_class.query.get.return_value = None

        result = process_lead_analysis(999)

        assert result is False

    @patch('app.db_session')
    @patch('app.services.pipeline.get_place_details')
    @patch('app.services.pipeline.analyze_url')
    @patch('app.services.pipeline.Lead')
    def test_handles_commit_failure(
        self, mock_lead_class, mock_analyze, mock_details, mock_db
    ):
        """Should rollback and return False on commit failure."""
        from app.services.pipeline import process_lead_analysis

        mock_lead = MagicMock()
        mock_lead.place_id = 'test-id'
        mock_lead.website_url = 'https://example.com'
        mock_lead.status = LeadStatus.SCRAPED
        mock_lead_class.query.get.return_value = mock_lead

        mock_details.return_value = {}
        mock_analyze.return_value = {'exists': True, 'logs': []}
        mock_db.commit.side_effect = Exception('Database error')

        result = process_lead_analysis(1)

        assert result is False
        mock_db.rollback.assert_called_once()
