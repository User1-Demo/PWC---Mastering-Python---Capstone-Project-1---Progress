from src.db.base import Base
from src.db.session import engine

# Import models so SQLAlchemy knows about them
from src.models.user import User
from src.models.policy import Policy
from src.models.claim import Claim
from src.models.document import Document
from src.models.document_chunk import DocumentChunk


def init_db():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
