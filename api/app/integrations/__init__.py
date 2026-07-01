"""External integrations, all MOCKED for local-only operation.

Each provider implements a clean interface so a real vendor (Okta, Slack,
a payroll API, Google/Outlook Calendar) can be dropped in later without
touching call sites. Nothing here makes a real network call.
"""

from app.integrations.calendar import CalendarProvider, MockCalendarProvider
from app.integrations.payroll import MockPayrollProvider, PayrollProvider
from app.integrations.slack import MockSlackProvider, SlackProvider
from app.integrations.sso import MockSSOProvider, SSOProvider

# Wired to mock implementations. Swap these for real providers later.
sso: SSOProvider = MockSSOProvider()
slack: SlackProvider = MockSlackProvider()
payroll: PayrollProvider = MockPayrollProvider()
calendar: CalendarProvider = MockCalendarProvider()

__all__ = [
    "sso",
    "slack",
    "payroll",
    "calendar",
    "SSOProvider",
    "SlackProvider",
    "PayrollProvider",
    "CalendarProvider",
]
