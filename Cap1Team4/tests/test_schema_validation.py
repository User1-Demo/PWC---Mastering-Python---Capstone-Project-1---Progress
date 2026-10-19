from sqlalchemy import (
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
)

from app.db.schema_validation import validate_database


def _expected_metadata() -> MetaData:
    metadata = MetaData()
    Table("parents", metadata, Column("id", Integer, primary_key=True))
    Table(
        "children",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parents.id"), nullable=False),
        Column("code", String(20), nullable=False),
        Column("state", Enum("open", "closed", native_enum=False), nullable=False),
        Column("amount", Integer, nullable=False),
        UniqueConstraint("code", name="uq_children_code"),
        CheckConstraint("amount > 0", name="ck_children_positive_amount"),
    )
    return metadata


def test_validator_accepts_matching_schema_and_data():
    metadata = _expected_metadata()
    engine = create_engine("sqlite://")
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(metadata.tables["parents"].insert(), {"id": 1})
        connection.execute(
            metadata.tables["children"].insert(),
            {"id": 1, "parent_id": 1, "code": "A", "state": "open", "amount": 1},
        )
        report = validate_database(connection, metadata)

    assert report.is_valid
    engine.dispose()


def test_validator_reports_schema_and_existing_row_mismatches():
    metadata = _expected_metadata()
    engine = create_engine("sqlite://")

    with engine.begin() as connection:
        connection.exec_driver_sql("CREATE TABLE parents (id INTEGER PRIMARY KEY)")
        connection.exec_driver_sql(
            "CREATE TABLE children ("
            "id INTEGER PRIMARY KEY, parent_id INTEGER, code VARCHAR(20), "
            "state VARCHAR(20), amount INTEGER)"
        )
        connection.exec_driver_sql(
            "INSERT INTO children (id, parent_id, code) VALUES "
            "(1, 999, 'duplicate'), (2, 999, 'duplicate'), (3, NULL, NULL)"
        )
        connection.exec_driver_sql(
            "UPDATE children SET state = 'invalid', amount = -1 WHERE id = 1"
        )

        report = validate_database(connection, metadata)

    assert report.schema_differences
    assert any("NULL value" in violation for violation in report.data_violations)
    assert any(
        "without a matching parents record" in violation for violation in report.data_violations
    )
    assert any("duplicate values" in violation for violation in report.data_violations)
    assert any("outside the model enum" in violation for violation in report.data_violations)
    assert any("violates check constraint" in violation for violation in report.data_violations)
    engine.dispose()
