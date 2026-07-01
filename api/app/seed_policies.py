"""Sample HR policy documents used by seed.py.

These double as the agent's RAG grounding source once ingested (Milestone 4).
Content is illustrative demo policy — not legal advice.
"""

from __future__ import annotations

SAMPLE_POLICIES: list[dict] = [
    {
        "title": "Annual Leave (PTO) Policy",
        "category": "Leave",
        "version": 3,
        "status": "published",
        "body": (
            "PeopleDesk provides full-time employees with 20 days of paid annual leave "
            "(PTO) per calendar year, accrued monthly. Leave requests must be submitted "
            "through the PeopleDesk portal and require manager approval before the leave "
            "is taken. Employees should give at least 5 business days' notice for planned "
            "leave of 3 days or more. Up to 5 unused annual leave days may be carried over "
            "into the next calendar year; any balance above 5 days is forfeited on Dec 31. "
            "Annual leave cannot be taken as negative balance without HR approval."
        ),
    },
    {
        "title": "Sick Leave Policy",
        "category": "Leave",
        "version": 2,
        "status": "published",
        "body": (
            "Employees accrue 10 days of paid sick leave per calendar year. Sick leave may "
            "be used for personal illness, medical appointments, or caring for an immediate "
            "family member. For absences of 3 or more consecutive days, a doctor's note may "
            "be requested by HR. Notify your manager as early as possible on the first day "
            "of a sick absence. Unused sick leave does not carry over between years and is "
            "not paid out on termination."
        ),
    },
    {
        "title": "Parental & Maternity Leave Policy",
        "category": "Leave",
        "version": 1,
        "status": "published",
        "body": (
            "PeopleDesk offers 16 weeks of fully paid maternity leave to birthing parents "
            "and 8 weeks of fully paid parental leave to non-birthing parents, to be taken "
            "within 12 months of the birth or adoption of a child. Employees must notify HR "
            "at least 30 days before the intended start of leave where reasonably possible. "
            "Health benefits continue during the leave period. On return, employees are "
            "guaranteed their previous role or an equivalent position. Requests for "
            "accommodation related to pregnancy should be raised with HR directly."
        ),
    },
    {
        "title": "Remote & Hybrid Work Policy",
        "category": "Workplace",
        "version": 2,
        "status": "published",
        "body": (
            "PeopleDesk operates a remote-first model. Employees may work fully remotely or "
            "adopt a hybrid schedule in coordination with their manager. Core collaboration "
            "hours are 10:00-15:00 in the employee's local time zone, during which employees "
            "should be reachable. Home-office equipment stipends of up to $500 per year are "
            "available and reimbursed through Finance. Employees working from a location "
            "outside their country of employment for more than 30 days must notify HR for "
            "tax and compliance reasons."
        ),
    },
    {
        "title": "Code of Conduct & Anti-Harassment Policy",
        "category": "Conduct",
        "version": 4,
        "status": "published",
        "body": (
            "PeopleDesk is committed to a workplace free of harassment, discrimination, and "
            "retaliation. Harassment based on race, gender, age, disability, religion, sexual "
            "orientation, or any protected characteristic is strictly prohibited. Any employee "
            "who experiences or witnesses harassment or discrimination should report it to HR "
            "or their manager, or through the confidential reporting channel. All reports are "
            "investigated promptly and confidentially. Retaliation against anyone who reports "
            "in good faith is itself a serious violation. Concerns of this nature are always "
            "handled by a human HR representative."
        ),
    },
    {
        "title": "Expense Reimbursement Policy",
        "category": "Finance",
        "version": 1,
        "status": "published",
        "body": (
            "Employees may be reimbursed for reasonable, pre-approved business expenses. "
            "Submit expense claims with itemized receipts through the portal within 30 days "
            "of the expense. Travel bookings above $1,000 require manager pre-approval. "
            "Reimbursements are processed with the next payroll cycle after approval. "
            "Personal expenses, alcohol beyond client entertainment limits, and fines are "
            "not reimbursable."
        ),
    },
    {
        "title": "Performance Review Cycle (Draft)",
        "category": "Performance",
        "version": 1,
        "status": "draft",
        "body": (
            "This draft outlines the semi-annual performance review process. Reviews occur "
            "in June and December. This document is not yet published and is subject to "
            "change. Performance decisions are always made by managers and HR, never "
            "automatically."
        ),
    },
    {
        "title": "Information Security & Acceptable Use Policy",
        "category": "Security",
        "version": 2,
        "status": "published",
        "body": (
            "All employees must use company-approved tools for handling PeopleDesk data, "
            "enable multi-factor authentication, and never share credentials. Confidential "
            "employee data, including personal information and compensation, must not be "
            "shared outside its intended audience. Report suspected security incidents to IT "
            "immediately. Company devices must have full-disk encryption and automatic screen "
            "lock enabled."
        ),
    },
]
