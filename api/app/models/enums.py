"""Shared enums used across models and services."""

from __future__ import annotations

import enum


class RBACRole(str, enum.Enum):
    employee = "employee"
    manager = "manager"
    hr_admin = "hr_admin"
    super_admin = "super_admin"


class EmploymentStatus(str, enum.Enum):
    active = "active"
    on_leave = "on_leave"
    terminated = "terminated"


class LeaveStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class PolicyStatus(str, enum.Enum):
    draft = "draft"
    published = "published"


class TicketCategory(str, enum.Enum):
    harassment = "harassment"
    grievance = "grievance"
    mental_health = "mental_health"
    compensation = "compensation"
    legal = "legal"
    termination = "termination"
    medical_accommodation = "medical_accommodation"
    ungrounded = "ungrounded"
    general = "general"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
