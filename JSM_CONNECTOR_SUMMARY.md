# Jira Service Management Connector - Implementation Summary

## Issue #2281 - $250 Bounty

### Goal
Pull in all tickets from a specified Jira Service Management project.

### Solution
Create a dedicated JSM connector that extends the existing Jira connector with JSM-specific features.

## Why Not Just Use Existing Jira Connector?

While JSM tickets ARE Jira issues and the existing connector technically works, a dedicated JSM connector provides:

1. **Clear JSM Support** - Users know JSM is officially supported
2. **JSM-Specific Metadata** - SLA info, request types, customer data
3. **Better UX** - Service desk terminology instead of generic "project"
4. **Simplified Setup** - JSM-focused configuration options

## Implementation Approach

### Simple & Effective Strategy

**Extend, Don't Rewrite:**
- Inherit from existing `JiraConnector` class
- Reuse all the battle-tested Jira API logic
- Add JSM-specific metadata extraction on top

**Hybrid API Approach:**
- Use standard Jira API for ticket retrieval (reliable, gets ALL tickets)
- Optionally enrich with Service Desk API for JSM-specific data

### Code Structure

```
backend/onyx/connectors/jira_service_management/
├── __init__.py
├── connector.py    # JiraServiceManagementConnector extends JiraConnector
└── utils.py        # JSM-specific helper functions
```

### Key Differences from Jira Connector

| Feature | Jira Connector | JSM Connector |
|---------|---------------|---------------|
| Terminology | "Project" | "Service Desk" |
| Metadata | Basic issue fields | + SLA, Request Type, Customer Org |
| Configuration | project_key | service_desk_id or project_key |
| Use Case | Software development | IT service management |

## JSM-Specific Metadata Captured

1. **Request Type** - Incident, Service Request, Change, etc.
2. **SLA Information** - Time to resolution, breached/met status
3. **Customer Organization** - Which org the request is from
4. **Service Desk Name** - Which service desk owns the ticket

## Implementation Steps

1. ✅ Create implementation plan
2. ⏳ Create JSM connector class (extends JiraConnector)
3. ⏳ Add JSM metadata extraction utilities
4. ⏳ Update backend configuration (DocumentSource, factory)
5. ⏳ Update frontend (source metadata, connector config)
6. ⏳ Add tests
7. ⏳ Create documentation
8. ⏳ Record demo video
9. ⏳ Submit PR

## Testing Checklist

- [ ] Can connect to JSM instance
- [ ] Retrieves all tickets from service desk
- [ ] Captures JSM-specific metadata
- [ ] Works with both Cloud and Server/DC
- [ ] Handles permissions correctly
- [ ] UI shows JSM connector option
- [ ] Configuration form works
- [ ] End-to-end indexing works

## Benefits

✅ **For Users**: Clear JSM support with rich metadata
✅ **For Onyx**: Expands connector ecosystem, addresses bounty
✅ **For Maintainers**: Minimal code (inherits from Jira), easy to maintain

## Timeline

- **Day 1**: Backend implementation (connector + utils)
- **Day 2**: Frontend implementation (UI + config)
- **Day 3**: Testing + documentation
- **Day 4**: PR submission

Let's build this! 🚀
