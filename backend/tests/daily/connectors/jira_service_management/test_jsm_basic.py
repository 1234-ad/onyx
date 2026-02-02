"""Basic tests for Jira Service Management connector.

These tests verify that the JSM connector can:
1. Initialize properly
2. Connect to a JSM instance
3. Retrieve service desk tickets
4. Extract JSM-specific metadata
"""

import pytest
from unittest.mock import Mock, patch

from onyx.connectors.jira_service_management.connector import (
    JiraServiceManagementConnector,
)
from onyx.configs.constants import DocumentSource


class TestJSMConnectorBasic:
    """Basic tests for JSM connector initialization and configuration."""

    def test_connector_initialization(self):
        """Test that the connector initializes with correct parameters."""
        connector = JiraServiceManagementConnector(
            jira_base_url="https://test.atlassian.net",
            project_key="SD",
            include_sla_info=True,
            include_approvals=True,
            include_customer_info=True,
        )

        assert connector.jira_base == "https://test.atlassian.net"
        assert connector.jira_project == "SD"
        assert connector.include_sla_info is True
        assert connector.include_approvals is True
        assert connector.include_customer_info is True

    def test_connector_inherits_from_jira(self):
        """Test that JSM connector properly inherits from Jira connector."""
        connector = JiraServiceManagementConnector(
            jira_base_url="https://test.atlassian.net"
        )

        # Should have all Jira connector properties
        assert hasattr(connector, "jira_base")
        assert hasattr(connector, "jira_project")
        assert hasattr(connector, "batch_size")
        assert hasattr(connector, "labels_to_skip")

    def test_jsm_metadata_extraction(self):
        """Test JSM-specific metadata extraction."""
        connector = JiraServiceManagementConnector(
            jira_base_url="https://test.atlassian.net"
        )

        # Mock issue with JSM fields
        mock_issue = Mock()
        mock_issue.fields = Mock()

        # Mock request type
        mock_request_type = Mock()
        mock_request_type.requestType = Mock()
        mock_request_type.requestType.name = "Incident"

        # Test metadata extraction
        with patch(
            "onyx.connectors.jira.utils.best_effort_get_field_from_issue",
            return_value=mock_request_type,
        ):
            metadata = connector._extract_jsm_metadata(mock_issue)
            assert "request_type" in metadata
            assert metadata["request_type"] == "Incident"

    def test_document_source_is_jsm(self):
        """Test that documents are marked with JSM source."""
        from onyx.connectors.models import Document, TextSection

        connector = JiraServiceManagementConnector(
            jira_base_url="https://test.atlassian.net"
        )

        # Create a mock document
        doc = Document(
            id="https://test.atlassian.net/browse/SD-1",
            sections=[TextSection(link="https://test.atlassian.net/browse/SD-1", text="Test")],
            source=DocumentSource.JIRA,  # Initially JIRA
            semantic_identifier="SD-1: Test Issue",
            title="SD-1 Test Issue",
            doc_updated_at=None,
        )

        # Mock issue
        mock_issue = Mock()
        mock_issue.key = "SD-1"
        mock_issue.fields = Mock()

        # Enrich document
        enriched_doc = connector._enrich_document_with_jsm_metadata(doc, mock_issue)

        # Should be marked as JSM source
        assert enriched_doc.source == DocumentSource.JIRA_SERVICE_MANAGEMENT


class TestJSMConnectorIntegration:
    """Integration tests for JSM connector (requires real JSM instance)."""

    @pytest.mark.skip(reason="Requires real JSM instance and credentials")
    def test_connect_to_jsm_instance(self):
        """Test connecting to a real JSM instance.

        To run this test:
        1. Set up a JSM instance
        2. Configure credentials
        3. Remove the skip decorator
        4. Run: pytest backend/tests/daily/connectors/jira_service_management/test_jsm_basic.py
        """
        connector = JiraServiceManagementConnector(
            jira_base_url="https://your-instance.atlassian.net",
            project_key="YOUR_PROJECT_KEY",
        )

        credentials = {
            "jira_user_email": "your-email@example.com",
            "jira_api_token": "your-api-token",
        }

        connector.load_credentials(credentials)

        # Try to fetch some documents
        docs = list(connector.load_from_state())

        assert len(docs) > 0
        # Verify JSM-specific metadata is present
        for doc in docs:
            if hasattr(doc, "metadata"):
                # Should have at least some JSM metadata
                assert doc.source == DocumentSource.JIRA_SERVICE_MANAGEMENT


# Test configuration for pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
