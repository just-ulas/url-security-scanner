from sqlalchemy import inspect

from app.db import Base
from app.models import ProviderResult, Scan, ScanMetadata, Target


def test_schema_contains_target_scan_metadata_and_provider_history(test_session_factory):
    bind = test_session_factory.kw["bind"]
    inspector = inspect(bind)
    assert {"targets", "scans", "scan_metadata", "provider_results"}.issubset(set(inspector.get_table_names()))
    assert "uq_scan_provider" in {item["name"] for item in inspector.get_unique_constraints("provider_results")}
    assert "uq_scans_active_target" in {item["name"] for item in inspector.get_indexes("scans")}
    assert Base.metadata.tables[Scan.__tablename__] is not None
    assert Base.metadata.tables[Target.__tablename__] is not None
    assert Base.metadata.tables[ScanMetadata.__tablename__] is not None
    assert Base.metadata.tables[ProviderResult.__tablename__] is not None
