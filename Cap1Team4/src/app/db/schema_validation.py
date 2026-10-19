"""Read-only database schema and stored-data validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pprint import pformat

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import (
    CheckConstraint,
    Enum as SqlEnum,
    MetaData,
    UniqueConstraint,
    and_,
    func,
    inspect,
    select,
    text,
)
from sqlalchemy.engine import Connection

import app.models  # noqa: F401 - register all mapped tables
from app.db.base import Base


@dataclass(frozen=True)
class ValidationReport:
    schema_differences: tuple[str, ...]
    data_violations: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.schema_differences and not self.data_violations


def validate_database(
    connection: Connection, metadata: MetaData = Base.metadata
) -> ValidationReport:
    """Compare live schema and persisted rows to model constraints without writing."""
    migration_context = MigrationContext.configure(
        connection,
        opts={"compare_type": True, "compare_server_default": True},
    )
    differences = [
        pformat(difference, width=100)
        for difference in compare_metadata(migration_context, metadata)
    ]
    differences.extend(_check_constraint_differences(connection, metadata))
    data_violations = _validate_rows(connection, metadata)
    return ValidationReport(tuple(differences), tuple(data_violations))


def _check_constraint_differences(connection: Connection, metadata: MetaData) -> list[str]:
    inspector = inspect(connection)
    database_tables = set(inspector.get_table_names())
    differences: list[str] = []

    for table in metadata.sorted_tables:
        if table.name not in database_tables:
            continue
        expected = {
            _normalize_expression(constraint.sqltext)
            for constraint in table.constraints
            if isinstance(constraint, CheckConstraint)
        }
        actual = {
            _normalize_expression(constraint["sqltext"])
            for constraint in inspector.get_check_constraints(table.name)
            if constraint.get("sqltext")
        }
        for expression in sorted(expected - actual):
            differences.append(
                f"{table.name} is missing check constraint equivalent to {expression}"
            )
        for expression in sorted(actual - expected):
            differences.append(f"{table.name} has an unmodeled check constraint: {expression}")
    return differences


def _normalize_expression(expression: object) -> str:
    return re.sub(r'[\s\[\]`()"]', "", str(expression)).upper()


def _validate_rows(connection: Connection, metadata: MetaData) -> list[str]:
    inspector = inspect(connection)
    database_tables = set(inspector.get_table_names())
    violations: list[str] = []

    for table in metadata.sorted_tables:
        if table.name not in database_tables:
            continue

        database_columns = {column["name"]: column for column in inspector.get_columns(table.name)}
        for column in table.columns:
            actual_column = database_columns.get(column.name)
            if actual_column is None or column.nullable or not actual_column["nullable"]:
                continue
            null_count = connection.scalar(
                select(func.count()).select_from(table).where(column.is_(None))
            )
            if null_count:
                violations.append(
                    f"{table.name}.{column.name} contains {null_count} NULL value(s); "
                    "the model requires non-NULL values"
                )

        for constraint in table.foreign_key_constraints:
            local_columns = tuple(element.parent.name for element in constraint.elements)
            remote_columns = tuple(element.column.name for element in constraint.elements)
            referred_table = next(iter(constraint.elements)).column.table
            if referred_table.name not in database_tables:
                continue
            parent_columns = {
                column["name"] for column in inspector.get_columns(referred_table.name)
            }
            if (
                not set(local_columns) <= set(database_columns)
                or not set(remote_columns) <= parent_columns
            ):
                continue
            parent = referred_table
            match_parent = and_(
                *(
                    parent.c[remote_name] == table.c[local_name]
                    for local_name, remote_name in zip(local_columns, remote_columns)
                )
            )
            has_no_parent = ~select(1).select_from(parent).where(match_parent).exists()
            all_values_present = and_(*(table.c[name].is_not(None) for name in local_columns))
            orphan_count = connection.scalar(
                select(func.count()).select_from(table).where(all_values_present, has_no_parent)
            )
            if orphan_count:
                violations.append(
                    f"{table.name} foreign key ({', '.join(local_columns)}) has "
                    f"{orphan_count} row(s) without a matching {parent.name} record"
                )

        unique_keys = {
            tuple(column.name for column in constraint.columns)
            for constraint in table.constraints
            if isinstance(constraint, UniqueConstraint)
        }
        unique_keys.update(
            tuple(column.name for column in index.columns)
            for index in table.indexes
            if index.unique
        )
        for columns in unique_keys:
            if not set(columns) <= set(database_columns):
                continue
            duplicate = connection.execute(
                select(*[table.c[name] for name in columns])
                .group_by(*[table.c[name] for name in columns])
                .having(func.count() > 1)
                .limit(1)
            ).first()
            if duplicate is not None:
                violations.append(
                    f"{table.name} has duplicate values for unique key ({', '.join(columns)})"
                )

        for constraint in table.constraints:
            if not isinstance(constraint, CheckConstraint):
                continue
            check_columns = {column.name for column in constraint.columns}
            if not check_columns <= set(database_columns):
                continue
            invalid_count = connection.scalar(
                select(func.count()).select_from(table).where(text(f"NOT ({constraint.sqltext})"))
            )
            if invalid_count:
                violations.append(
                    f"{table.name} violates check constraint "
                    f"{constraint.name or str(constraint.sqltext)!r} "
                    f"for {invalid_count} row(s)"
                )

        for column in table.columns:
            if not isinstance(column.type, SqlEnum) or not column.type.enums:
                continue
            if column.name not in database_columns:
                continue
            invalid_count = connection.scalar(
                select(func.count())
                .select_from(table)
                .where(column.is_not(None), column.not_in(column.type.enums))
            )
            if invalid_count:
                violations.append(
                    f"{table.name}.{column.name} contains {invalid_count} value(s) "
                    "outside the model enum"
                )

    return violations


def main() -> int:
    from app.db.session import engine

    with engine.connect() as connection:
        report = validate_database(connection)

    if report.is_valid:
        print("Database schema and stored data match the project models.")
        return 0

    if report.schema_differences:
        print("Schema differences:")
        for difference in report.schema_differences:
            print(f"- {difference}")
    if report.data_violations:
        print("Stored-data violations:")
        for violation in report.data_violations:
            print(f"- {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
