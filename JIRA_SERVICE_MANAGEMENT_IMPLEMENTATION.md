# Jira Service Management Connector Implementation Plan

## Issue
Fixes #2281 ($250 bounty)

## Overview
Create a dedicated Jira Service Management (JSM) connector that extends the existing Jira connector with service desk-specific features and metadata.

## Key Insights

### JSM vs Jira Software
- **JSM tickets ARE Jira issues** - they can be queried using standard Jira API
- **JSM has specialized API** (`/rest/servicedeskapi/`) for service desk-specific operations
- **Existing Jira connector already works** for JSM projects, but lacks JSM-specific features

### Why a Dedicated Connector?
1. **Better UX**: Dedicated connector makes it clear JSM is supported
2. **JSM-specific metadata**: Capture SLA, customer info, request types, etc.
3. **Service desk features**: Organizations, queues, approvals
4. **Simplified configuration**: JSM-specific terminology and options

## Implementation Strategy

### Approach: Extend Existing Jira Connector
The JSM connector will:
1. **Inherit** from the existing `JiraConnector` class
2. **Add** JSM-specific metadata extraction
3. **Use** standard Jira API for issue retrieval (more reliable)
4. **Enhance** with Service Desk API for JSM-specific data

### Why Not Pure Service Desk API?
- `/rest/servicedeskapi/request` only returns requests where user participated
- Standard Jira API `/rest/api/3/search` returns ALL issues (requires "Browse Projects" permission)
- Hybrid approach: Jira API for retrieval + Service Desk API for enrichment

## JSM-Specific Features to Implement

### 1. Service Desk Metadata
- Service Desk ID and name
- Request Type (e.g., "Incident", "Service Request", "Change")
- Customer organization
- Portal/channel (email, portal, API)

### 2. SLA Information
- SLA name and description
- Time to first response
- Time to resolution
- SLA status (met, breached, paused)
- Remaining time

### 3. Customer Information
- Customer name and email (reporter)
- Customer organization
- Request participants

### 4. Approval Information
- Approval status
- Approvers
- Approval decisions

### 5. Queue Information
- Queue name
- Queue JQL

## Technical Implementation

### File Structure
```
backend/onyx/connectors/jira_service_management/
├── __init__.py
├── connector.py          # Main JSM connector class
├── utils.py             # JSM-specific utility functions
└── access.py            # JSM permission handling
```

### Key Classes

#### JiraServiceManagementConnector
```python
class JiraServiceManagementConnector(JiraConnector):
    def __init__(
        self,
        jira_base_url: str,
        service_desk_id: str | None = None,  # NEW: Service desk filter
        project_key: str | None = None,
        include_sla_info: bool = True,        # NEW: Include SLA data
        include_approvals: bool = True,       # NEW: Include approval data
        **kwargs
    ):
        super().__init__(jira_base_url, project_key, **kwargs)
        self.service_desk_id = service_desk_id
        self.include_sla_info = include_sla_info
        self.include_approvals = include_approvals
```

### API Integration

#### 1. Issue Retrieval (Standard Jira API)
```python
# Use existing JiraConnector logic
# JQL: project = "SERVICE_DESK_PROJECT"
```

#### 2. Service Desk Enrichment
```python
# GET /rest/servicedeskapi/servicedesk/{serviceDeskId}
# GET /rest/servicedeskapi/request/{issueIdOrKey}
# GET /rest/servicedeskapi/request/{issueIdOrKey}/sla
# GET /rest/servicedeskapi/request/{issueIdOrKey}/approval
```

### Metadata Extraction

```python
def _extract_jsm_metadata(issue: Issue, jira_client: JIRA) -> dict:
    metadata = {}
    
    # Service Desk info
    if service_desk := get_service_desk_info(issue, jira_client):
        metadata["service_desk_name"] = service_desk["name"]
        metadata["service_desk_id"] = service_desk["id"]
    
    # Request Type
    if request_type := get_request_type(issue):
        metadata["request_type"] = request_type["name"]
    
    # SLA info
    if sla_info := get_sla_information(issue, jira_client):
        metadata["sla_status"] = sla_info["status"]
        metadata["sla_time_remaining"] = sla_info["remaining_time"]
    
    # Customer organization
    if org := get_customer_organization(issue, jira_client):
        metadata["customer_organization"] = org["name"]
    
    # Approval info
    if approvals := get_approval_info(issue, jira_client):
        metadata["approval_status"] = approvals["status"]
        metadata["approvers"] = [a["name"] for a in approvals["approvers"]]
    
    return metadata
```

## Configuration

### Backend Changes

#### 1. Add DocumentSource
```python
# backend/onyx/configs/constants.py
class DocumentSource(str, Enum):
    # ... existing sources ...
    JIRA_SERVICE_MANAGEMENT = "jira_service_management"
```

#### 2. Update Factory
```python
# backend/onyx/connectors/factory.py
from onyx.connectors.jira_service_management.connector import JiraServiceManagementConnector

CONNECTOR_MAP = {
    # ... existing connectors ...
    DocumentSource.JIRA_SERVICE_MANAGEMENT: JiraServiceManagementConnector,
}
```

### Frontend Changes

#### 1. Source Metadata
```typescript
// web/src/lib/sources.ts
export const SOURCE_METADATA_MAP: Record<ValidSources, SourceMetadata> = {
  // ... existing sources ...
  jira_service_management: {
    displayName: "Jira Service Management",
    category: SourceCategory.TicketingTool,
    icon: JiraServiceManagementIcon,
    docs: "https://docs.onyx.app/connectors/jira_service_management",
  },
};
```

#### 2. Connector Config
```typescript
// web/src/lib/connectors/connectors.ts
export const connectorConfigs: Record<ValidSources, ConnectorConfig<any>> = {
  // ... existing connectors ...
  jira_service_management: {
    name: "Jira Service Management",
    source: "jira_service_management",
    fields: [
      {
        name: "jira_base_url",
        label: "Jira Base URL",
        type: "text",
        required: true,
      },
      {
        name: "service_desk_id",
        label: "Service Desk ID (optional)",
        type: "text",
        description: "Leave empty to index all service desks",
      },
      {
        name: "project_key",
        label: "Project Key (optional)",
        type: "text",
        description: "Leave empty to index all projects",
      },
      {
        name: "include_sla_info",
        label: "Include SLA Information",
        type: "checkbox",
        default: true,
      },
      {
        name: "include_approvals",
        label: "Include Approval Information",
        type: "checkbox",
        default: true,
      },
    ],
    credential: {
      type: "oauth",
      // ... OAuth config ...
    },
  },
};
```

## Testing Plan

### 1. Unit Tests
```python
# backend/tests/daily/connectors/jira_service_management/test_jsm_basic.py
def test_jsm_connector_basic():
    # Test basic JSM ticket retrieval
    pass

def test_jsm_sla_extraction():
    # Test SLA metadata extraction
    pass

def test_jsm_approval_extraction():
    # Test approval metadata extraction
    pass
```

### 2. Integration Tests
- Connect to real JSM instance
- Verify all tickets are retrieved
- Verify JSM-specific metadata is captured
- Verify permissions work correctly

## Benefits

### For Users
✅ Clear indication that JSM is supported
✅ Rich JSM-specific metadata (SLA, approvals, etc.)
✅ Better search and filtering capabilities
✅ Service desk-specific terminology

### For Onyx
✅ Expands connector ecosystem
✅ Addresses $250 bounty issue
✅ Leverages existing Jira connector code
✅ Minimal maintenance overhead (inherits from Jira)

## Backward Compatibility

✅ **Existing Jira connector unchanged** - users can still use it for JSM
✅ **New connector is additive** - doesn't break existing functionality
✅ **Shared codebase** - JSM connector inherits from Jira connector

## Implementation Checklist

- [ ] Create JSM connector directory structure
- [ ] Implement JiraServiceManagementConnector class
- [ ] Add JSM-specific utility functions
- [ ] Add JSM metadata extraction
- [ ] Update DocumentSource enum
- [ ] Update connector factory
- [ ] Add frontend source metadata
- [ ] Add frontend connector config
- [ ] Create unit tests
- [ ] Create integration tests
- [ ] Test end-to-end with real JSM instance
- [ ] Create documentation
- [ ] Record demo video
- [ ] Submit PR

## Timeline

- **Phase 1** (Day 1): Backend implementation
- **Phase 2** (Day 2): Frontend implementation
- **Phase 3** (Day 3): Testing and documentation
- **Phase 4** (Day 4): PR submission and review

## Notes

- JSM connector will be a thin wrapper around Jira connector
- Most complexity is in metadata extraction
- Service Desk API calls should be optional (graceful degradation)
- Focus on Cloud API first, Server/DC support can come later
