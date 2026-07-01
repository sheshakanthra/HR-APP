"""Model registry.

Import every model here so Alembic autogenerate and `Base.metadata`
see the full schema.
"""

from app.models.agent import AgentConversation, AgentMessage, HRTicket
from app.models.audit import AuditLog
from app.models.base import Base
from app.models.department import Department
from app.models.employee import Employee
from app.models.enums import (
    EmploymentStatus,
    LeaveStatus,
    PolicyStatus,
    RBACRole,
    TicketCategory,
    TicketStatus,
)
from app.models.leave import LeaveBalance, LeaveRequest, LeaveType
from app.models.policy import PolicyChunk, PolicyDocument
from app.models.user import User

__all__ = [
    "Base",
    "User",
    "Employee",
    "Department",
    "LeaveType",
    "LeaveBalance",
    "LeaveRequest",
    "PolicyDocument",
    "PolicyChunk",
    "AgentConversation",
    "AgentMessage",
    "HRTicket",
    "AuditLog",
    "RBACRole",
    "EmploymentStatus",
    "LeaveStatus",
    "PolicyStatus",
    "TicketCategory",
    "TicketStatus",
]
