# Patch for backend/onyx/configs/constants.py

## Change 1: Add to DocumentSource enum (around line 183)

**Before:**
```python
    JIRA = "jira"
    SLAB = "slab"
```

**After:**
```python
    JIRA = "jira"
    JIRA_SERVICE_MANAGEMENT = "jira_service_management"
    SLAB = "slab"
```

## Change 2: Add to DocumentSourceDescription dict (around line 615)

**Before:**
```python
    DocumentSource.JIRA: "jira data (issues, tickets, projects, etc.)",
    DocumentSource.SLAB: "slab data",
```

**After:**
```python
    DocumentSource.JIRA: "jira data (issues, tickets, projects, etc.)",
    DocumentSource.JIRA_SERVICE_MANAGEMENT: "jira service management - IT service desk tickets, requests, incidents, and SLA tracking",
    DocumentSource.SLAB: "slab data",
```

These changes add the JIRA_SERVICE_MANAGEMENT document source to support the new JSM connector.
