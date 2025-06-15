import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from models.audit_log import AuditLog, AuditAction
from models.database import SessionLocal
from main import app

@pytest.mark.asyncio
async def test_diary_create_audit_log(async_client: AsyncClient, db_session: AsyncSession):
    # Create a diary entry
    payload = {
        "user_id": 123,
        "text": "Test entry",
        "mood": "happy",
        "tags": ["test"],
        "date": "2024-06-01"
    }
    response = await async_client.post("/diary/entry", json=payload)
    assert response.status_code == 200
    # Check audit log
    async with db_session.bind.connect() as conn:
        result = await conn.execute(
            AuditLog.__table__.select().where(
                AuditLog.action == AuditAction.CREATE,
                AuditLog.resource == "diary_entry",
                AuditLog.user_id.isnot(None)
            )
        )
        logs = result.fetchall()
        assert len(logs) > 0, "No audit log entry found for diary create"
        log = logs[-1]
        assert log.action == AuditAction.CREATE
        assert log.resource == "diary_entry"
        assert str(log.user_id) == str(payload["user_id"]) 