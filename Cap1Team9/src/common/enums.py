from enum import Enum


class UserRole(str, Enum):

    admin = "admin"

    manager = "manager"

    adjuster = "adjuster"

    support = "support"


class PolicyStatus(str, Enum):

    active = "active"

    inactive = "inactive"

    expired = "expired"


class PolicyType(str, Enum):

    motor = "motor"

    health = "health"

    property = "property"


class ClaimStatus(str, Enum):
    submitted = "submitted"
    under_review = "under_review"
    approved = "approved"
    rejected = "rejected"
    closed = "closed"
