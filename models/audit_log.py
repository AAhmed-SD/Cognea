from sqlalchemy import Column, String, DateTime, Enum, JSON, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from models.database import Base

class AuditAction(str, enum.Enum):
    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    EXPORT = "export"
    OTHER = "other"

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(Enum(AuditAction), nullable=False)
    resource = Column(String, nullable=False)  # e.g. "diary_entry", "user_settings"
    resource_id = Column(String, nullable=True)  # UUID or int as string
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    details = Column(JSON, nullable=True)  # Arbitrary extra info

    user = relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "resource": self.resource,
            "resource_id": self.resource_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details,
        } 