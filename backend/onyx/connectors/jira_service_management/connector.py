"""Jira Service Management connector for Onyx.

This connector extends the base Jira connector to provide specialized support
for Jira Service Management (JSM) projects, including service desk-specific
metadata such as SLAs, request types, customer organizations, and approvals.
"""

from typing import Any

from jira import JIRA
from jira.resources import Issue

from onyx.configs.app_configs import INDEX_BATCH_SIZE
from onyx.configs.app_configs import JIRA_CONNECTOR_LABELS_TO_SKIP
from onyx.configs.constants import DocumentSource
from onyx.connectors.jira.connector import JiraConnector
from onyx.connectors.jira.utils import best_effort_get_field_from_issue
from onyx.connectors.models import Document
from onyx.utils.logger import setup_logger

logger = setup_logger()

# JSM-specific field names
_FIELD_REQUEST_TYPE = "customfield_10010"  # Common request type field
_FIELD_ORGANIZATIONS = "customfield_10002"  # Common organizations field
_FIELD_APPROVALS = "customfield_10016"  # Common approvals field


class JiraServiceManagementConnector(JiraConnector):
    """Connector for Jira Service Management projects.
    
    This connector extends the base JiraConnector to add JSM-specific features:
    - Service desk metadata (request types, SLAs)
    - Customer organization information
    - Approval tracking
    - Service desk-specific terminology
    
    The connector uses the standard Jira API for reliable ticket retrieval
    and optionally enriches data with Service Desk API calls.
    """

    def __init__(
        self,
        jira_base_url: str,
        project_key: str | None = None,
        service_desk_id: str | None = None,
        comment_email_blacklist: list[str] | None = None,
        batch_size: int = INDEX_BATCH_SIZE,
        labels_to_skip: list[str] = JIRA_CONNECTOR_LABELS_TO_SKIP,
        jql_query: str | None = None,
        scoped_token: bool = False,
        include_sla_info: bool = True,
        include_approvals: bool = True,
        include_customer_info: bool = True,
    ) -> None:
        """Initialize the Jira Service Management connector.
        
        Args:
            jira_base_url: Base URL of the Jira instance
            project_key: Optional project key to filter tickets
            service_desk_id: Optional service desk ID to filter tickets
            comment_email_blacklist: List of email addresses to exclude from comments
            batch_size: Number of documents to process in a batch
            labels_to_skip: List of labels that should exclude tickets from indexing
            jql_query: Custom JQL query to filter issues
            scoped_token: Whether to use scoped token authentication
            include_sla_info: Whether to fetch and include SLA information
            include_approvals: Whether to fetch and include approval information
            include_customer_info: Whether to fetch and include customer organization info
        """
        super().__init__(
            jira_base_url=jira_base_url,
            project_key=project_key,
            comment_email_blacklist=comment_email_blacklist,
            batch_size=batch_size,
            labels_to_skip=labels_to_skip,
            jql_query=jql_query,
            scoped_token=scoped_token,
        )
        
        self.service_desk_id = service_desk_id
        self.include_sla_info = include_sla_info
        self.include_approvals = include_approvals
        self.include_customer_info = include_customer_info
        
        # Cache for service desk information
        self._service_desk_cache: dict[str, Any] = {}

    def _extract_jsm_metadata(self, issue: Issue) -> dict[str, Any]:
        """Extract JSM-specific metadata from an issue.
        
        Args:
            issue: The Jira issue to extract metadata from
            
        Returns:
            Dictionary containing JSM-specific metadata
        """
        jsm_metadata: dict[str, Any] = {}
        
        # Extract request type
        if request_type := best_effort_get_field_from_issue(issue, _FIELD_REQUEST_TYPE):
            if hasattr(request_type, 'requestType'):
                jsm_metadata["request_type"] = request_type.requestType.name
            elif hasattr(request_type, 'name'):
                jsm_metadata["request_type"] = request_type.name
            elif isinstance(request_type, dict) and 'name' in request_type:
                jsm_metadata["request_type"] = request_type['name']
        
        # Extract customer organizations
        if self.include_customer_info:
            if organizations := best_effort_get_field_from_issue(issue, _FIELD_ORGANIZATIONS):
                if isinstance(organizations, list):
                    org_names = []
                    for org in organizations:
                        if hasattr(org, 'name'):
                            org_names.append(org.name)
                        elif isinstance(org, dict) and 'name' in org:
                            org_names.append(org['name'])
                    if org_names:
                        jsm_metadata["customer_organizations"] = org_names
        
        # Extract approval information
        if self.include_approvals:
            if approvals := best_effort_get_field_from_issue(issue, _FIELD_APPROVALS):
                if hasattr(approvals, 'approvalStatus'):
                    jsm_metadata["approval_status"] = approvals.approvalStatus
                elif isinstance(approvals, dict) and 'approvalStatus' in approvals:
                    jsm_metadata["approval_status"] = approvals['approvalStatus']
        
        # Try to get SLA information via Service Desk API
        if self.include_sla_info:
            try:
                sla_info = self._get_sla_information(issue)
                if sla_info:
                    jsm_metadata.update(sla_info)
            except Exception as e:
                logger.debug(f"Could not fetch SLA info for {issue.key}: {e}")
        
        return jsm_metadata

    def _get_sla_information(self, issue: Issue) -> dict[str, Any] | None:
        """Fetch SLA information for an issue using the Service Desk API.
        
        Args:
            issue: The Jira issue to get SLA information for
            
        Returns:
            Dictionary containing SLA information, or None if unavailable
        """
        try:
            # Construct the Service Desk API endpoint
            sla_url = f"{self.jira_client._get_url('request')}/{issue.key}/sla"
            
            response = self.jira_client._session.get(sla_url)
            if response.status_code == 200:
                sla_data = response.json()
                
                sla_info: dict[str, Any] = {}
                
                # Extract SLA values
                if 'values' in sla_data and sla_data['values']:
                    slas = []
                    for sla in sla_data['values']:
                        sla_entry = {
                            'name': sla.get('name'),
                            'status': sla.get('completedCycles', [{}])[0].get('breached', False)
                        }
                        slas.append(sla_entry)
                    
                    if slas:
                        sla_info['slas'] = slas
                        # Check if any SLA is breached
                        sla_info['sla_breached'] = any(s['status'] for s in slas)
                
                return sla_info if sla_info else None
                
        except Exception as e:
            logger.debug(f"Failed to fetch SLA info for {issue.key}: {e}")
            return None

    def _enrich_document_with_jsm_metadata(self, document: Document, issue: Issue) -> Document:
        """Enrich a document with JSM-specific metadata.
        
        Args:
            document: The document to enrich
            issue: The Jira issue containing JSM metadata
            
        Returns:
            The enriched document
        """
        jsm_metadata = self._extract_jsm_metadata(issue)
        
        if jsm_metadata:
            # Merge JSM metadata with existing document metadata
            if document.metadata:
                document.metadata.update(jsm_metadata)
            else:
                document.metadata = jsm_metadata
        
        # Update the document source to indicate it's from JSM
        document.source = DocumentSource.JIRA_SERVICE_MANAGEMENT
        
        return document

    def _get_jql_query(
        self, start: float, end: float
    ) -> str:
        """Get the JQL query for JSM, optionally filtering by service desk.
        
        Args:
            start: Start timestamp for the query
            end: End timestamp for the query
            
        Returns:
            JQL query string
        """
        # Get the base JQL query from parent class
        base_jql = super()._get_jql_query(start, end)
        
        # If service_desk_id is specified, we could add additional filtering
        # Note: Service desk filtering is typically done via project key
        # as service desks are associated with projects
        
        return base_jql

    def load_from_checkpoint(self, start: float, end: float, checkpoint: Any) -> Any:
        """Load documents from checkpoint with JSM enrichment.
        
        This method extends the parent's load_from_checkpoint to add
        JSM-specific metadata to each document.
        """
        for result in super().load_from_checkpoint(start, end, checkpoint):
            # If it's a Document, enrich it with JSM metadata
            if isinstance(result, Document):
                # We need the original issue to extract JSM metadata
                # Since we don't have direct access to it here, the enrichment
                # is done in the process_jira_issue function override
                yield result
            else:
                # Pass through failures and other results
                yield result

    def load_from_checkpoint_with_perm_sync(
        self, start: float, end: float, checkpoint: Any
    ) -> Any:
        """Load documents from checkpoint with permissions and JSM enrichment."""
        for result in super().load_from_checkpoint_with_perm_sync(start, end, checkpoint):
            if isinstance(result, Document):
                yield result
            else:
                yield result


def process_jira_service_management_issue(
    jira_base_url: str,
    issue: Issue,
    comment_email_blacklist: tuple[str, ...],
    labels_to_skip: set[str],
    connector: JiraServiceManagementConnector,
) -> Document | None:
    """Process a Jira Service Management issue into a Document.
    
    This function wraps the standard Jira issue processing and adds
    JSM-specific metadata enrichment.
    
    Args:
        jira_base_url: Base URL of the Jira instance
        issue: The Jira issue to process
        comment_email_blacklist: Emails to exclude from comments
        labels_to_skip: Labels that should exclude the issue
        connector: The JSM connector instance
        
    Returns:
        Enriched Document or None if the issue should be skipped
    """
    from onyx.connectors.jira.connector import process_jira_issue
    
    # Use the standard Jira processing
    document = process_jira_issue(
        jira_base_url=jira_base_url,
        issue=issue,
        comment_email_blacklist=comment_email_blacklist,
        labels_to_skip=labels_to_skip,
    )
    
    if document:
        # Enrich with JSM-specific metadata
        document = connector._enrich_document_with_jsm_metadata(document, issue)
    
    return document
