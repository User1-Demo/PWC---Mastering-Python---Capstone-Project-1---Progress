from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    CLAIMS_MANAGER = "claims_manager"
    CLAIMS_ADJUSTER = "claims_adjuster"
    SUPPORT_AGENT = "support_agent"


class PolicyType(StrEnum):
    MOTOR = "motor"
    HEALTH = "health"
    PROPERTY = "property"


class PolicyStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


class ClaimStatus(StrEnum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CLOSED = "closed"


class NoteType(StrEnum):
    ADJUSTER_NOTE = "adjuster_note"
    MANAGER_NOTE = "manager_note"
    SYSTEM = "system"


class DocumentType(StrEnum):
    POLICY_WORDING = "policy_wording"
    ENDORSEMENT = "endorsement"
    GUIDELINE = "guideline"


class DocumentStatus(StrEnum):
    PROCESSING = "processing"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
