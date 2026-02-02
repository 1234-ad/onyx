#!/usr/bin/env python3
"""
Temporary script to add JIRA_SERVICE_MANAGEMENT to DocumentSource enum.
This will be deleted after the constants file is updated.
"""

# This script adds:
# 1. JIRA_SERVICE_MANAGEMENT = "jira_service_management" to DocumentSource enum (after JIRA)
# 2. Entry in DocumentSourceDescription dict

print("Add JIRA_SERVICE_MANAGEMENT after line 183 (after JIRA = 'jira')")
print("JIRA_SERVICE_MANAGEMENT = \"jira_service_management\"")
print()
print("Add to DocumentSourceDescription dict after JIRA entry:")
print("DocumentSource.JIRA_SERVICE_MANAGEMENT: \"jira service management - IT service desk tickets, requests, and incidents\",")
