"""Seed the database with realistic demo data.

Generates ~200 employees across departments with a manager hierarchy,
leave types + balances, user accounts (RBAC roles), and sample policy docs.

Run inside the container:  python -m app.seed
Idempotent: refuses to run twice unless PEOPLEDESK_SEED_FORCE=true (which wipes).

NOTE: All demo employees share one password (`Passw0rd!`) so we hash it ONCE
and reuse the hash — Argon2 per-user hashing of 200 rows would be needlessly
slow for throwaway seed data. The seed admin gets its own password.
"""

from __future__ import annotations

import os
import random
from datetime import date, timedelta

from faker import Faker
from sqlalchemy import select, text

from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal, engine
from app.models import (
    Department,
    Employee,
    LeaveBalance,
    LeaveType,
    PolicyDocument,
    User,
)
from app.models.enums import EmploymentStatus, PolicyStatus, RBACRole
from app.seed_policies import SAMPLE_POLICIES

fake = Faker()
Faker.seed(42)
random.seed(42)

DEMO_PASSWORD = "Passw0rd!"

DEPARTMENTS = [
    "Engineering",
    "Product",
    "Design",
    "Sales",
    "Marketing",
    "Customer Success",
    "Finance",
    "People & HR",
    "Legal",
    "IT",
]

LEAVE_TYPES = [
    {"name": "Annual Leave", "code": "ANNUAL", "annual_accrual_days": 20, "description": "Paid vacation / PTO."},
    {"name": "Sick Leave", "code": "SICK", "annual_accrual_days": 10, "description": "Paid sick time."},
    {"name": "Casual Leave", "code": "CASUAL", "annual_accrual_days": 5, "description": "Short-notice personal time."},
]

TITLES_BY_LEVEL = {
    "head": ["Head", "Director", "VP"],
    "manager": ["Manager", "Lead", "Senior Manager"],
    "ic": ["Associate", "Specialist", "Engineer", "Analyst", "Coordinator", "Senior Associate"],
}

TOTAL_EMPLOYEES = 200


def already_seeded(db) -> bool:
    return db.scalar(select(Department).limit(1)) is not None


def wipe(db) -> None:
    # Order respects FKs; TRUNCATE ... CASCADE is simplest for a full reset.
    db.execute(
        text(
            "TRUNCATE audit_log, hr_ticket, agent_message, agent_conversation, "
            "policy_chunk, policy_document, leave_request, leave_balance, "
            "leave_type, user_account, employee, department "
            "RESTART IDENTITY CASCADE"
        )
    )
    db.commit()


def _email(first: str, last: str, taken: set[str]) -> str:
    base = f"{first}.{last}".lower().replace(" ", "").replace("'", "")
    email = f"{base}@peopledesk.io"
    i = 1
    while email in taken:
        email = f"{base}{i}@peopledesk.io"
        i += 1
    taken.add(email)
    return email


def seed() -> None:
    force = os.getenv("PEOPLEDESK_SEED_FORCE", "false").lower() == "true"
    db = SessionLocal()
    try:
        # Ensure pgvector extension exists (migrations also do this; harmless).
        db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        db.commit()

        if already_seeded(db):
            if not force:
                print("[seed] database already seeded; set PEOPLEDESK_SEED_FORCE=true to reset.")
                return
            print("[seed] PEOPLEDESK_SEED_FORCE=true -> wiping existing data")
            wipe(db)

        # --- Departments ---
        departments = {name: Department(name=name) for name in DEPARTMENTS}
        db.add_all(departments.values())
        db.flush()

        # --- Leave types ---
        leave_types = [LeaveType(**lt) for lt in LEAVE_TYPES]
        db.add_all(leave_types)
        db.flush()

        emails: set[str] = set()
        demo_hash = hash_password(DEMO_PASSWORD)

        def make_employee(dept: Department, level: str, manager: Employee | None) -> Employee:
            first, last = fake.first_name(), fake.last_name()
            title_word = random.choice(TITLES_BY_LEVEL[level])
            title = f"{dept.name} {title_word}" if level != "ic" else f"{title_word}, {dept.name}"
            emp = Employee(
                first_name=first,
                last_name=last,
                work_email=_email(first, last, emails),
                title=title,
                location=random.choice(["Remote", "New York", "London", "Bangalore", "Berlin", "Austin"]),
                hire_date=fake.date_between(start_date="-8y", end_date="-30d"),
                employment_status=EmploymentStatus.active,
                department=dept,
                manager=manager,
            )
            db.add(emp)
            return emp

        # --- CEO (top of the org, no manager) ---
        ceo = make_employee(departments["People & HR"], "head", None)
        ceo.title = "Chief Executive Officer"
        db.flush()

        # --- Department heads report to the CEO ---
        heads: dict[str, Employee] = {}
        for name, dept in departments.items():
            head = make_employee(dept, "head", ceo)
            heads[name] = head
        db.flush()

        # per-department pool of people who can manage others (heads first)
        manager_pool: dict[str, list[Employee]] = {name: [heads[name]] for name in DEPARTMENTS}
        all_employees: list[Employee] = [ceo, *heads.values()]

        # --- Fill the rest ---
        remaining = TOTAL_EMPLOYEES - len(all_employees)
        dept_names = list(DEPARTMENTS)
        for i in range(remaining):
            dept_name = dept_names[i % len(dept_names)]
            dept = departments[dept_name]
            pool = manager_pool[dept_name]
            manager = random.choice(pool)
            # ~30% become sub-managers so the tree has depth
            level = "manager" if random.random() < 0.3 and len(pool) < 8 else "ic"
            emp = make_employee(dept, level, manager)
            all_employees.append(emp)
            if level == "manager":
                pool.append(emp)
        db.flush()

        # --- Leave balances for everyone (deterministic accrual math) ---
        today = date.today()
        for emp in all_employees:
            tenure_years = max((today - emp.hire_date).days / 365.25, 0.1)
            for lt in leave_types:
                # accrued = min(annual entitlement, prorated by tenure this year)
                accrued = float(lt.annual_accrual_days)
                used = round(random.uniform(0, min(accrued, 8)), 1)
                db.add(
                    LeaveBalance(
                        employee=emp,
                        leave_type=lt,
                        accrued=accrued,
                        used=used,
                    )
                )
        db.flush()

        # --- User accounts + RBAC roles ---
        # Everyone gets a login. Managers (anyone with reports) -> manager role.
        managed_ids = {e.manager_id for e in all_employees if e.manager_id is not None}
        for emp in all_employees:
            if emp is ceo:
                role = RBACRole.super_admin
            elif emp.department and emp.department.name == "People & HR" and emp in heads.values():
                role = RBACRole.hr_admin
            elif emp.id in managed_ids:
                role = RBACRole.manager
            else:
                role = RBACRole.employee
            db.add(
                User(
                    email=emp.work_email,
                    password_hash=demo_hash,
                    rbac_role=role,
                    employee=emp,
                )
            )

        # Give the whole People & HR department hr_admin for a richer demo.
        for emp in all_employees:
            if emp.department and emp.department.name == "People & HR" and emp is not ceo:
                pass  # heads already hr_admin; ICs stay employee for realistic RBAC tests

        # --- Dedicated super_admin login from .env ---
        admin_emp = make_employee(departments["IT"], "head", ceo)
        admin_emp.first_name, admin_emp.last_name = "Site", "Admin"
        admin_emp.title = "Platform Administrator"
        admin_emp.work_email = settings.seed_admin_email
        db.flush()
        for lt in leave_types:
            db.add(LeaveBalance(employee=admin_emp, leave_type=lt, accrued=float(lt.annual_accrual_days), used=0))
        db.add(
            User(
                email=settings.seed_admin_email,
                password_hash=hash_password(settings.seed_admin_password),
                rbac_role=RBACRole.super_admin,
                employee=admin_emp,
            )
        )

        # --- Policy documents (published + a couple drafts). Chunking/embedding is M4. ---
        for p in SAMPLE_POLICIES:
            db.add(
                PolicyDocument(
                    title=p["title"],
                    category=p["category"],
                    body=p["body"],
                    version=p.get("version", 1),
                    status=PolicyStatus(p.get("status", "published")),
                    effective_date=today - timedelta(days=90),
                )
            )

        db.commit()

        # Summary
        print("[seed] done.")
        print(f"[seed]   employees: {len(all_employees) + 1}")
        print(f"[seed]   departments: {len(departments)}")
        print(f"[seed]   leave types: {len(leave_types)}")
        print(f"[seed]   policies: {len(SAMPLE_POLICIES)}")
        print(f"[seed]   demo password for all seeded employees: {DEMO_PASSWORD}")
        print(f"[seed]   super_admin: {settings.seed_admin_email} / (SEED_ADMIN_PASSWORD)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
