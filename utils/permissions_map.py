"""
ALL ROLES:
"owner",
"admin",
"finance_manager",
"operations_manager",
"support_agent",
"auditor",
"developer",
"member"
-----
Access is scoped by Database tables and on few occasion actions.
"""

ROLE_PERMISSIONS = {
    # Corresponds to "Organization Settings" and "User Onboarding & Access"
    "organization": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer"
        ],
        "write": [
            "owner",
            "admin",
            "operations_manager"
        ],
    },
    "invitation": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer"
        ],
        "write": [
            "owner",
            "admin",
            "operations_manager"
        ],
    },
    "membership": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer"
        ],
        "write": [
            "owner",
            "admin",
            "operations_manager"
        ],
    },
    # Corresponds to "Meter Management"
    "meter": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer",
            "member"
        ],
        "write": [
            "owner",
            "admin",
            "operations_manager"
        ],
    },
    # Corresponds to "Vending (Utility Tokens)"
    "vending": {
        "read": [
            "owner",
            "admin",
            "operations_manager",
            "support_agent",
            "auditor"
        ],
        "write": [
            "owner",
            "admin",
            "operations_manager",
            "support_agent"  # Has "Basic Vending" permissions
        ],
    },
    # Corresponds to "Wallet Management"
    "wallet": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer",
            "member"
        ],
        "write": [
            "owner",
            "admin",
            "finance_manager"
        ],
    },
    "transaction": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "support_agent",
            "auditor",
        ],
        "write": [
            "owner",
            "admin",
            "finance_manager",
            "support_agent",
            "auditor",
        ],
    },
    # Corresponds to "Financial Reports" and "Reporting & Analytics"
    "reports": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer"
        ],
        "write": [
            "owner",
            "admin",
            "finance_manager" # "Full Access" for Financial Reports
        ],
    },
    # Corresponds to "Developer Settings (API Keys, Webhooks)"
    "developer": {
        "read": [
            "owner",
            "admin",
            "developer"
        ],
        "write": [
            "owner",
            "admin",
            "developer"
        ],
    },
    # Corresponds to "Profile Management"
    "profile": {
        "read": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer",
            "member"
        ],
        "write": [
            "owner",
            "admin",
            "finance_manager",
            "operations_manager",
            "support_agent",
            "auditor",
            "developer",
            "member"
        ],
    },
}