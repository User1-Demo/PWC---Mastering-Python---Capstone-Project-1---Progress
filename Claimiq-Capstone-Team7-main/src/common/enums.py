"""
enums.py (common)

Purpose: Shared enums used across multiple modules. Defining these once
here (instead of duplicating strings everywhere) means Policies, Claims,
and validation logic all reference the SAME allowed values.
"""

import enum


class PolicyType(str, enum.Enum):
    MOTOR = "motor"
    HEALTH = "health"
    PROPERTY = "property"


class PolicyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    ADJUSTER = "adjuster"
    SUPPORT_AGENT = "support_agent"

class ClaimStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    VALIDATION = "validation"
    ASSIGNED = "assigned"
    UNDER_REVIEW = "under_review"
    AI_MANAGER_REVIEW = "ai_manager_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"