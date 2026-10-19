import argparse
import hashlib
import random
import shutil
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.claim import Claim, ClaimStatusHistory
from app.models.document import Document, DocumentChunk
from app.models.enums import (
    ClaimStatus,
    DocumentStatus,
    DocumentType,
    PolicyStatus,
    PolicyType,
)
from app.models.policy import Policy
from app.models.user import Region, User
from app.rag.chunker import chunk_pages
from app.services.audit_service import log_action

_REGIONS = [
    ("NORTH", "North Region"),
    ("SOUTH", "South Region"),
    ("EAST", "East Region"),
    ("WEST", "West Region"),
]
_NAMES = [
    "Alex Morgan", "Jordan Taylor", "Casey Parker", "Riley Jordan",
    "Avery Chen", "Sam Patel", "Taylor Kim", "Morgan Reed",
    "Jamie Rivera", "Cameron Brooks", "Drew Bailey", "Robin Ellis",
]
_STATUSES = [
    ClaimStatus.SUBMITTED,
    ClaimStatus.UNDER_REVIEW,
    ClaimStatus.APPROVED,
    ClaimStatus.REJECTED,
    ClaimStatus.CLOSED,
]
_SAMPLE_DOCUMENTS = Path("data/sample_documents")


def _get_or_create_region(db, code: str, name: str) -> Region:
    region = db.scalar(select(Region).where(Region.code == code))
    if region is None:
        region = Region(code=code, name=name)
        db.add(region)
        db.flush()
    return region


def _seed_policies(db, regions: list[Region]) -> list[Policy]:
    policies: list[Policy] = []
    types = list(PolicyType)
    today = date.today()
    for index in range(5):
        number = f"DEMO-POL-{index + 1:04d}"
        policy = db.scalar(select(Policy).where(Policy.policy_number == number))
        if policy is None:
            policy = Policy(
                policy_number=number,
                policy_type=types[index % len(types)],
                policyholder_name=_NAMES[index],
                policyholder_email=f"policyholder{index + 1}@example.test",
                coverage_amount=Decimal("2500000.00"),
                premium_amount=Decimal("24000.00"),
                deductible_amount=Decimal("1000.00"),
                region_id=regions[index % len(regions)].id,
                start_date=today - timedelta(days=365),
                end_date=today + timedelta(days=365),
                status=PolicyStatus.ACTIVE,
            )
            db.add(policy)
            db.flush()
        policies.append(policy)
    return policies


def _seed_claims(db, admin: User, policies: list[Policy]) -> int:
    randomizer = random.Random(42)
    created = 0
    for index in range(1, 501):
        number = f"DEMO-CLM-{index:05d}"
        if db.scalar(select(Claim.id).where(Claim.claim_number == number)):
            continue
        policy = policies[(index - 1) % len(policies)]
        status = _STATUSES[(index - 1) % len(_STATUSES)]
        submitted = datetime.now(UTC) - timedelta(days=randomizer.randint(0, 180))
        amount = Decimal(randomizer.randrange(500, 1_250_000)).quantize(Decimal("0.01"))
        claim = Claim(
            claim_number=number,
            policy_id=policy.id,
            region_id=policy.region_id,
            claim_type=policy.policy_type,
            status=status,
            claimant_name=_NAMES[index % len(_NAMES)],
            claimant_email=None,
            claimant_phone=None,
            incident_date=policy.start_date + timedelta(days=randomizer.randint(1, 300)),
            description="Synthetic training claim; contains no real customer data.",
            claimed_amount=amount,
            approved_amount=amount if status in (ClaimStatus.APPROVED, ClaimStatus.CLOSED) else None,
            is_high_value=amount >= Decimal(str(settings.HIGH_VALUE_THRESHOLD)),
            assigned_adjuster_id=None,
            created_by=admin.id,
            submitted_at=submitted,
            sla_due_at=submitted + timedelta(days=settings.SLA_DEFAULT_DAYS),
            decided_at=(
                submitted + timedelta(days=randomizer.randint(1, 6))
                if status in (ClaimStatus.APPROVED, ClaimStatus.REJECTED, ClaimStatus.CLOSED)
                else None
            ),
            closed_at=(
                submitted + timedelta(days=10)
                if status == ClaimStatus.CLOSED
                else None
            ),
            fraud_score=0,
            fraud_flags=[],
        )
        db.add(claim)
        db.flush()
        db.add(
            ClaimStatusHistory(
                claim_id=claim.id,
                from_status=None,
                to_status=ClaimStatus.SUBMITTED,
                changed_by=admin.id,
                changed_at=submitted,
            )
        )
        if status != ClaimStatus.SUBMITTED:
            db.add(
                ClaimStatusHistory(
                    claim_id=claim.id,
                    from_status=ClaimStatus.SUBMITTED,
                    to_status=ClaimStatus.UNDER_REVIEW,
                    changed_by=admin.id,
                    changed_at=submitted + timedelta(days=1),
                )
            )
        final_status = (
            ClaimStatus.APPROVED if status == ClaimStatus.CLOSED else status
        )
        if final_status in (ClaimStatus.APPROVED, ClaimStatus.REJECTED):
            db.add(
                ClaimStatusHistory(
                    claim_id=claim.id,
                    from_status=ClaimStatus.UNDER_REVIEW,
                    to_status=final_status,
                    changed_by=admin.id,
                    changed_at=submitted + timedelta(days=2),
                )
            )
        if status == ClaimStatus.CLOSED:
            db.add(
                ClaimStatusHistory(
                    claim_id=claim.id,
                    from_status=ClaimStatus.APPROVED,
                    to_status=ClaimStatus.CLOSED,
                    changed_by=admin.id,
                    changed_at=submitted + timedelta(days=5),
                )
            )
        created += 1
    return created


def _seed_documents(db, admin: User) -> int:
    created = 0
    storage_dir = Path(settings.DOCUMENT_STORAGE_DIR)
    storage_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted(_SAMPLE_DOCUMENTS.glob("*.md")):
        content = source.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        if db.scalar(select(Document.id).where(Document.file_hash == file_hash)):
            continue
        text = content.decode("utf-8")
        indexed = chunk_pages(
            [(None, text)],
            chunk_size=settings.RAG_CHUNK_SIZE,
            overlap=settings.RAG_CHUNK_OVERLAP,
        )
        stored = storage_dir / f"{file_hash}.md"
        shutil.copyfile(source, stored)
        doc = Document(
            title=source.stem.replace("_", " ").title(),
            original_filename=source.name,
            storage_path=str(stored),
            file_hash=file_hash,
            mime_type="text/markdown",
            size_bytes=len(content),
            doc_type=DocumentType.GUIDELINE,
            applies_to=None,
            version="1.0",
            status=DocumentStatus.ACTIVE,
            is_active=True,
            chunk_count=len(indexed),
            uploaded_by=admin.id,
        )
        db.add(doc)
        db.flush()
        for chunk_index, (chunk, heading, page) in enumerate(indexed):
            db.add(
                DocumentChunk(
                    document_id=doc.id,
                    chunk_index=chunk_index,
                    content=chunk,
                    section_heading=heading,
                    page_number=page,
                    token_count=len(chunk.split()),
                    is_active=True,
                )
            )
        created += 1
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Create synthetic ClaimsIQ demo data.")
    parser.add_argument("--admin-email", required=True)
    args = parser.parse_args()
    with SessionLocal() as db:
        admin = db.scalar(
            select(User).where(
                User.email == args.admin_email.lower(),
                User.is_active.is_(True),
            )
        )
        if admin is None:
            parser.error("An active administrator with --admin-email must already exist.")
        if admin.role.value != "admin":
            parser.error("--admin-email must belong to an administrator.")
        regions = [_get_or_create_region(db, code, name) for code, name in _REGIONS]
        policies = _seed_policies(db, regions)
        claim_count = _seed_claims(db, admin, policies)
        document_count = _seed_documents(db, admin)
        log_action(
            db,
            action="DEMO_DATA_SEEDED",
            entity_type="dataset",
            actor=admin,
            new={
                "claims_created": claim_count,
                "documents_created": document_count,
            },
        )
        db.commit()
    print(
        f"Demo data is ready: 5 policies, {claim_count} new claims, "
        f"{document_count} new documents."
    )


if __name__ == "__main__":
    main()
