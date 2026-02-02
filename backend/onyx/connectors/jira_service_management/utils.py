"""Utility functions for Jira Service Management connector."""

from typing import Any

from jira import JIRA
from jira.resources import Issue

from onyx.utils.logger import setup_logger

logger = setup_logger()


def get_service_desk_info(jira_client: JIRA, service_desk_id: str) -> dict[str, Any] | None:
    """Get information about a service desk.
    
    Args:
        jira_client: Authenticated Jira client
        service_desk_id: ID of the service desk
        
    Returns:
        Service desk information or None if unavailable
    """
    try:
        # Use Service Desk API to get service desk info
        url = f"{jira_client._options['server']}/rest/servicedeskapi/servicedesk/{service_desk_id}"
        response = jira_client._session.get(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Failed to fetch service desk info: {response.status_code}")
            return None
            
    except Exception as e:
        logger.debug(f"Error fetching service desk info: {e}")
        return None


def get_request_type_info(jira_client: JIRA, issue_key: str) -> dict[str, Any] | None:
    """Get request type information for an issue.
    
    Args:
        jira_client: Authenticated Jira client
        issue_key: Key of the issue
        
    Returns:
        Request type information or None if unavailable
    """
    try:
        # Use Service Desk API to get request info
        url = f"{jira_client._options['server']}/rest/servicedeskapi/request/{issue_key}"
        response = jira_client._session.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if 'requestTypeId' in data:
                return {
                    'id': data['requestTypeId'],
                    'name': data.get('requestType', {}).get('name', 'Unknown')
                }
        return None
        
    except Exception as e:
        logger.debug(f"Error fetching request type for {issue_key}: {e}")
        return None


def is_service_desk_project(jira_client: JIRA, project_key: str) -> bool:
    """Check if a project is a service desk project.
    
    Args:
        jira_client: Authenticated Jira client
        project_key: Key of the project to check
        
    Returns:
        True if the project is a service desk, False otherwise
    """
    try:
        # Try to access the project via Service Desk API
        url = f"{jira_client._options['server']}/rest/servicedeskapi/servicedesk"
        response = jira_client._session.get(url)
        
        if response.status_code == 200:
            service_desks = response.json().get('values', [])
            for sd in service_desks:
                if sd.get('projectKey') == project_key:
                    return True
        return False
        
    except Exception as e:
        logger.debug(f"Error checking if {project_key} is a service desk: {e}")
        return False


def extract_customer_email(issue: Issue) -> str | None:
    """Extract customer email from a JSM issue.
    
    Args:
        issue: The Jira issue
        
    Returns:
        Customer email or None if not available
    """
    try:
        # In JSM, the reporter is typically the customer
        if hasattr(issue.fields, 'reporter') and issue.fields.reporter:
            if hasattr(issue.fields.reporter, 'emailAddress'):
                return issue.fields.reporter.emailAddress
            elif hasattr(issue.fields.reporter, 'email'):
                return issue.fields.reporter.email
        return None
    except Exception as e:
        logger.debug(f"Error extracting customer email: {e}")
        return None


def get_service_desk_queues(jira_client: JIRA, service_desk_id: str) -> list[dict[str, Any]]:
    """Get all queues for a service desk.
    
    Args:
        jira_client: Authenticated Jira client
        service_desk_id: ID of the service desk
        
    Returns:
        List of queue information dictionaries
    """
    try:
        url = f"{jira_client._options['server']}/rest/servicedeskapi/servicedesk/{service_desk_id}/queue"
        response = jira_client._session.get(url)
        
        if response.status_code == 200:
            return response.json().get('values', [])
        return []
        
    except Exception as e:
        logger.debug(f"Error fetching queues for service desk {service_desk_id}: {e}")
        return []
