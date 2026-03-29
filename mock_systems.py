import asyncio
from uuid import uuid4
from datetime import datetime
import random
from config import settings

# Module-level counter for JIRA error injection
_jira_call_count = 0


def reset_error_injection():
    """Reset error injection counters for demo runs."""
    global _jira_call_count
    _jira_call_count = 0


async def create_ad_account(employee_name: str, email: str, department: str) -> dict:
    """
    Simulate Active Directory account creation.
    Never fails - reliable system.
    """
    await asyncio.sleep(1.0)

    # Generate username from name
    username = email.split('@')[0]

    return {
        "status": "success",
        "username": username,
        "account_id": str(uuid4()),
        "system": "active_directory"
    }


async def create_jira_account(employee_name: str, email: str) -> dict:
    """
    Simulate JIRA account provisioning.
    Error injection: Fails on 1st-3rd calls, succeeds on 4th+ call.
    """
    global _jira_call_count
    _jira_call_count += 1

    await asyncio.sleep(1.5)

    # Error injection logic
    if settings.enable_error_injection and _jira_call_count < 4:
        raise Exception(
            "JIRA API Error 403: Access Denied - License seat limit reached. "
            "Contact admin@company.com"
        )

    # Generate JIRA username
    jira_username = email.split('@')[0].lower()

    return {
        "status": "success",
        "account_id": str(uuid4()),
        "jira_username": jira_username,
        "system": "jira"
    }


async def create_email_account(employee_name: str, domain: str = "company.com") -> dict:
    """
    Simulate email/Google Workspace provisioning.
    """
    await asyncio.sleep(0.8)

    # Generate email from name
    name_parts = employee_name.lower().split()
    if len(name_parts) >= 2:
        email = f"{name_parts[0]}.{name_parts[-1]}@{domain}"
    else:
        email = f"{name_parts[0]}@{domain}"

    return {
        "status": "success",
        "email": email,
        "system": "google_workspace"
    }


async def assign_buddy(department: str, exclude_name: str) -> dict:
    """
    Simulate buddy assignment from team roster.
    """
    await asyncio.sleep(0.5)

    # Hardcoded department rosters
    department_roster = {
        "Engineering": [
            {"name": "Alice Wong", "email": "alice.wong@company.com"},
            {"name": "Bob Martinez", "email": "bob.martinez@company.com"},
            {"name": "Charlie Lee", "email": "charlie.lee@company.com"}
        ],
        "Marketing": [
            {"name": "Diana Ross", "email": "diana.ross@company.com"},
            {"name": "Eric Johnson", "email": "eric.johnson@company.com"}
        ],
        "Sales": [
            {"name": "Frank Wilson", "email": "frank.wilson@company.com"},
            {"name": "Grace Thompson", "email": "grace.thompson@company.com"}
        ],
        "Product": [
            {"name": "Hannah Davis", "email": "hannah.davis@company.com"},
            {"name": "Isaac Brown", "email": "isaac.brown@company.com"}
        ]
    }

    # Get potential buddies (exclude new hire)
    buddies = department_roster.get(department, department_roster["Engineering"])
    available_buddies = [b for b in buddies if b["name"].lower() != exclude_name.lower()]

    # Pick random buddy
    if available_buddies:
        buddy = random.choice(available_buddies)
    else:
        # Fallback if all filtered out
        buddy = {"name": "Alice Wong", "email": "alice.wong@company.com"}

    return {
        "status": "success",
        "buddy_name": buddy["name"],
        "buddy_email": buddy["email"]
    }


async def schedule_meeting(
    title: str,
    attendees: list[str],
    date: str,
    duration_min: int = 60
) -> dict:
    """
    Simulate Google Calendar meeting creation.
    """
    await asyncio.sleep(0.7)

    meeting_id = str(uuid4())
    calendar_link = f"https://calendar.google.com/event?eid={meeting_id}"

    return {
        "status": "success",
        "meeting_id": meeting_id,
        "calendar_link": calendar_link,
        "title": title,
        "attendees": attendees,
        "duration_min": duration_min
    }


async def send_email(to: list[str], subject: str, body: str) -> dict:
    """
    Simulate sending email.
    """
    await asyncio.sleep(0.3)

    return {
        "status": "sent",
        "message_id": str(uuid4()),
        "recipients": to,
        "subject": subject
    }


async def send_slack_message(channel: str, message: str) -> dict:
    """
    Simulate Slack message sending.
    """
    await asyncio.sleep(0.2)

    timestamp = datetime.utcnow().isoformat()

    return {
        "status": "sent",
        "channel": channel,
        "ts": timestamp,
        "message": message
    }


async def create_task(
    title: str,
    assignee: str,
    description: str,
    priority: str = "medium",
    project: str = "General"
) -> dict:
    """
    Simulate project tracker task creation.
    """
    await asyncio.sleep(0.6)

    task_id = str(uuid4())[:8].upper()
    task_url = f"https://tracker.company.com/task/{task_id}"

    return {
        "status": "created",
        "task_id": task_id,
        "title": title,
        "assignee": assignee,
        "description": description,
        "priority": priority,
        "project": project,
        "url": task_url
    }


async def get_approval_status(request_id: str) -> dict:
    """
    Simulate checking approval status.
    Returns a stuck approval scenario.
    """
    await asyncio.sleep(0.4)

    return {
        "request_id": request_id,
        "status": "stuck",
        "approver": "David Kim",
        "stuck_since_hours": 52,
        "approver_status": "on_leave",
        "delegate": "Sarah Chen",
        "sla_deadline": "2026-03-28T17:00:00Z"
    }


async def reroute_approval(request_id: str, new_approver: str, reason: str) -> dict:
    """
    Simulate rerouting an approval to a different approver.
    """
    await asyncio.sleep(1.0)

    return {
        "status": "rerouted",
        "request_id": request_id,
        "new_approver": new_approver,
        "reason": reason,
        "override_id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat()
    }


# System registry for dynamic tool dispatch
SYSTEM_REGISTRY = {
    "active_directory": create_ad_account,
    "jira": create_jira_account,
    "email": create_email_account,
    "google_workspace": create_email_account,
    "buddy_assignment": assign_buddy,
    "calendar": schedule_meeting,
    "email_sender": send_email,
    "slack": send_slack_message,
    "task_tracker": create_task,
    "approval_checker": get_approval_status,
    "approval_router": reroute_approval
}
