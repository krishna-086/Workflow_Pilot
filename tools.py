import asyncio
from langchain_core.tools import tool
from audit import audit_logger
import mock_systems


@tool
async def create_active_directory_account(employee_name: str, email: str, department: str) -> str:
    """Create an Active Directory account for a new employee."""
    try:
        result = await mock_systems.create_ad_account(employee_name, email, department)

        audit_logger.log(
            scenario="onboarding",
            agent="tool_active_directory",
            action="create_ad_account",
            input_data={"employee_name": employee_name, "email": email, "department": department},
            output_data=result,
            decision_reasoning="Creating Active Directory account for new employee",
            status="success"
        )

        return f"Active Directory account created successfully. Username: {result['username']}, Account ID: {result['account_id']}"

    except Exception as e:
        audit_logger.log(
            scenario="onboarding",
            agent="tool_active_directory",
            action="create_ad_account",
            input_data={"employee_name": employee_name, "email": email, "department": department},
            output_data={},
            decision_reasoning="Failed to create Active Directory account",
            error=str(e),
            status="failure"
        )
        return f"Error creating Active Directory account: {str(e)}"


@tool
async def create_jira_account(employee_name: str, email: str) -> str:
    """Create a JIRA account for a new employee."""
    try:
        result = await mock_systems.create_jira_account(employee_name, email)

        audit_logger.log(
            scenario="onboarding",
            agent="tool_jira",
            action="create_jira_account",
            input_data={"employee_name": employee_name, "email": email},
            output_data=result,
            decision_reasoning="Creating JIRA account for new employee",
            status="success"
        )

        return f"JIRA account created successfully. Username: {result['jira_username']}, Account ID: {result['account_id']}"

    except Exception as e:
        # IMPORTANT: Catch exception and return error string instead of raising
        audit_logger.log(
            scenario="onboarding",
            agent="tool_jira",
            action="create_jira_account",
            input_data={"employee_name": employee_name, "email": email},
            output_data={},
            decision_reasoning="Failed to create JIRA account - may need retry",
            error=str(e),
            status="failure"
        )
        return f"Error creating JIRA account: {str(e)}"


@tool
async def create_email_account(employee_name: str) -> str:
    """Create a company email account for a new employee."""
    try:
        result = await mock_systems.create_email_account(employee_name)

        audit_logger.log(
            scenario="onboarding",
            agent="tool_email",
            action="create_email_account",
            input_data={"employee_name": employee_name},
            output_data=result,
            decision_reasoning="Creating email account for new employee",
            status="success"
        )

        return f"Email account created successfully. Email: {result['email']}"

    except Exception as e:
        audit_logger.log(
            scenario="onboarding",
            agent="tool_email",
            action="create_email_account",
            input_data={"employee_name": employee_name},
            output_data={},
            decision_reasoning="Failed to create email account",
            error=str(e),
            status="failure"
        )
        return f"Error creating email account: {str(e)}"


@tool
async def assign_onboarding_buddy(department: str, new_hire_name: str) -> str:
    """Assign an onboarding buddy from the same department."""
    try:
        result = await mock_systems.assign_buddy(department, new_hire_name)

        audit_logger.log(
            scenario="onboarding",
            agent="tool_buddy",
            action="assign_buddy",
            input_data={"department": department, "new_hire_name": new_hire_name},
            output_data=result,
            decision_reasoning="Assigning onboarding buddy from department roster",
            status="success"
        )

        return f"Onboarding buddy assigned: {result['buddy_name']} ({result['buddy_email']})"

    except Exception as e:
        audit_logger.log(
            scenario="onboarding",
            agent="tool_buddy",
            action="assign_buddy",
            input_data={"department": department, "new_hire_name": new_hire_name},
            output_data={},
            decision_reasoning="Failed to assign buddy",
            error=str(e),
            status="failure"
        )
        return f"Error assigning buddy: {str(e)}"


@tool
async def schedule_orientation_meeting(employee_name: str, attendees: list[str]) -> str:
    """Schedule an orientation meeting for the new hire."""
    try:
        result = await mock_systems.schedule_meeting(
            title=f"Orientation - {employee_name}",
            attendees=attendees,
            date="2026-04-05",
            duration_min=60
        )

        audit_logger.log(
            scenario="onboarding",
            agent="tool_calendar",
            action="schedule_meeting",
            input_data={"employee_name": employee_name, "attendees": attendees},
            output_data=result,
            decision_reasoning="Scheduling orientation meeting for new hire",
            status="success"
        )

        return f"Orientation meeting scheduled successfully. Meeting ID: {result['meeting_id']}, Link: {result['calendar_link']}"

    except Exception as e:
        audit_logger.log(
            scenario="onboarding",
            agent="tool_calendar",
            action="schedule_meeting",
            input_data={"employee_name": employee_name, "attendees": attendees},
            output_data={},
            decision_reasoning="Failed to schedule orientation meeting",
            error=str(e),
            status="failure"
        )
        return f"Error scheduling orientation: {str(e)}"


@tool
async def send_notification_email(recipients: list[str], subject: str, body: str) -> str:
    """Send an email notification."""
    try:
        result = await mock_systems.send_email(recipients, subject, body)

        audit_logger.log(
            scenario="general",
            agent="tool_email_sender",
            action="send_email",
            input_data={"recipients": recipients, "subject": subject},
            output_data=result,
            decision_reasoning="Sending notification email",
            status="success"
        )

        return f"Email sent successfully to {len(recipients)} recipient(s). Message ID: {result['message_id']}"

    except Exception as e:
        audit_logger.log(
            scenario="general",
            agent="tool_email_sender",
            action="send_email",
            input_data={"recipients": recipients, "subject": subject},
            output_data={},
            decision_reasoning="Failed to send email",
            error=str(e),
            status="failure"
        )
        return f"Error sending email: {str(e)}"


@tool
async def send_slack_notification(channel: str, message: str) -> str:
    """Send a Slack notification."""
    try:
        result = await mock_systems.send_slack_message(channel, message)

        audit_logger.log(
            scenario="general",
            agent="tool_slack",
            action="send_slack_message",
            input_data={"channel": channel, "message": message},
            output_data=result,
            decision_reasoning="Sending Slack notification",
            status="success"
        )

        return f"Slack message sent successfully to #{channel}. Timestamp: {result['ts']}"

    except Exception as e:
        audit_logger.log(
            scenario="general",
            agent="tool_slack",
            action="send_slack_message",
            input_data={"channel": channel, "message": message},
            output_data={},
            decision_reasoning="Failed to send Slack message",
            error=str(e),
            status="failure"
        )
        return f"Error sending Slack message: {str(e)}"


@tool
async def create_project_task(title: str, assignee: str, description: str, priority: str = "medium") -> str:
    """Create a task in the project management system."""
    try:
        result = await mock_systems.create_task(title, assignee, description, priority)

        audit_logger.log(
            scenario="meeting",
            agent="tool_task_tracker",
            action="create_task",
            input_data={"title": title, "assignee": assignee, "priority": priority},
            output_data=result,
            decision_reasoning="Creating task in project management system",
            status="success"
        )

        return f"Task created successfully. Task ID: {result['task_id']}, Assignee: {assignee}, URL: {result['url']}"

    except Exception as e:
        audit_logger.log(
            scenario="meeting",
            agent="tool_task_tracker",
            action="create_task",
            input_data={"title": title, "assignee": assignee, "priority": priority},
            output_data={},
            decision_reasoning="Failed to create task",
            error=str(e),
            status="failure"
        )
        return f"Error creating task: {str(e)}"


@tool
async def check_approval_status(request_id: str) -> str:
    """Check the current status of an approval request."""
    try:
        result = await mock_systems.get_approval_status(request_id)

        audit_logger.log(
            scenario="sla",
            agent="tool_approval_checker",
            action="check_approval_status",
            input_data={"request_id": request_id},
            output_data=result,
            decision_reasoning="Checking approval request status",
            status="success"
        )

        return (f"Approval status: {result['status']}. "
                f"Approver: {result['approver']} ({result['approver_status']}). "
                f"Stuck for {result['stuck_since_hours']} hours. "
                f"Suggested delegate: {result['delegate']}")

    except Exception as e:
        audit_logger.log(
            scenario="sla",
            agent="tool_approval_checker",
            action="check_approval_status",
            input_data={"request_id": request_id},
            output_data={},
            decision_reasoning="Failed to check approval status",
            error=str(e),
            status="failure"
        )
        return f"Error checking approval status: {str(e)}"


@tool
async def reroute_approval_request(request_id: str, new_approver: str, reason: str) -> str:
    """Reroute a stuck approval to a delegate."""
    try:
        result = await mock_systems.reroute_approval(request_id, new_approver, reason)

        audit_logger.log(
            scenario="sla",
            agent="tool_approval_router",
            action="reroute_approval",
            input_data={"request_id": request_id, "new_approver": new_approver, "reason": reason},
            output_data=result,
            decision_reasoning="Rerouting stuck approval to delegate",
            status="success"
        )

        return (f"Approval rerouted successfully. "
                f"New approver: {new_approver}. "
                f"Override ID: {result['override_id']}")

    except Exception as e:
        audit_logger.log(
            scenario="sla",
            agent="tool_approval_router",
            action="reroute_approval",
            input_data={"request_id": request_id, "new_approver": new_approver, "reason": reason},
            output_data={},
            decision_reasoning="Failed to reroute approval",
            error=str(e),
            status="failure"
        )
        return f"Error rerouting approval: {str(e)}"


# Export all tools for easy binding to LLM
ALL_TOOLS = [
    create_active_directory_account,
    create_jira_account,
    create_email_account,
    assign_onboarding_buddy,
    schedule_orientation_meeting,
    send_notification_email,
    send_slack_notification,
    create_project_task,
    check_approval_status,
    reroute_approval_request
]
