import time
import asyncio
from langgraph.graph import StateGraph, END
from models import WorkflowState
from llm_router import call_llm_simple
from audit import audit_logger
from config import settings, MAX_RETRIES
import mock_systems


# Node 1: Create Active Directory Account
async def create_ad_account(state: WorkflowState) -> dict:
    """Create Active Directory account for new employee."""
    start_time = time.time()
    employee = state["employee"]

    try:
        result = await mock_systems.create_ad_account(
            employee["name"],
            employee["email"],
            employee["department"]
        )

        duration_ms = (time.time() - start_time) * 1000

        audit_entry = audit_logger.log(
            scenario="onboarding",
            agent="system_provisioner",
            action="create_ad_account",
            input_data=employee,
            output_data=result,
            decision_reasoning="Creating Active Directory account for new employee",
            model_used="none",
            tokens_used=0,
            duration_ms=duration_ms,
            status="success"
        )

        return {
            "accounts_created": [result],
            "current_step": 2,
            "audit_trail": [audit_entry]
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        audit_entry = audit_logger.log(
            scenario="onboarding",
            agent="system_provisioner",
            action="create_ad_account",
            input_data=employee,
            output_data={},
            decision_reasoning="Failed to create Active Directory account",
            error=str(e),
            duration_ms=duration_ms,
            status="failure"
        )

        return {
            "error_log": [f"AD account creation failed: {str(e)}"],
            "audit_trail": [audit_entry]
        }


# Node 2: Create JIRA Account
async def create_jira_account_node(state: WorkflowState) -> dict:
    """Create JIRA account for new employee."""
    start_time = time.time()
    employee = state["employee"]

    try:
        result = await mock_systems.create_jira_account(
            employee["name"],
            employee["email"]
        )

        duration_ms = (time.time() - start_time) * 1000

        audit_entry = audit_logger.log(
            scenario="onboarding",
            agent="system_provisioner",
            action="create_jira_account",
            input_data={"name": employee["name"], "email": employee["email"]},
            output_data=result,
            decision_reasoning="Creating JIRA account for new employee",
            model_used="none",
            tokens_used=0,
            duration_ms=duration_ms,
            status="success"
        )

        return {
            "accounts_created": [result],
            "current_step": 3,
            "audit_trail": [audit_entry],
            "retry_count": 0  # Reset retry count on success
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_msg = str(e)

        audit_entry = audit_logger.log(
            scenario="onboarding",
            agent="system_provisioner",
            action="create_jira_account",
            input_data={"name": employee["name"], "email": employee["email"]},
            output_data={},
            decision_reasoning=f"JIRA account creation failed (attempt {state.get('retry_count', 0) + 1})",
            error=error_msg,
            duration_ms=duration_ms,
            status="failure"
        )

        return {
            "error_log": [f"JIRA account creation failed: {error_msg}"],
            "retry_count": state.get("retry_count", 0) + 1,
            "audit_trail": [audit_entry]
        }


# Node 3: Handle JIRA Retry
async def handle_jira_retry(state: WorkflowState) -> dict:
    """Analyze error and retry JIRA account creation."""
    start_time = time.time()
    retry_count = state.get("retry_count", 0)
    last_error = state.get("error_log", ["Unknown error"])[-1]

    # Use LLM to analyze the error
    prompt = f"""A JIRA account creation failed with error: {last_error}
This is retry attempt {retry_count}/{MAX_RETRIES}.
Analyze the error and suggest if we should retry or escalate.
Respond with either RETRY or ESCALATE and a brief reason."""

    response, model_used, tokens_used = await call_llm_simple("error_analysis", prompt)
    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="onboarding",
        agent="retry_coordinator",
        action="analyze_jira_error",
        input_data={"error": last_error, "retry_count": retry_count},
        output_data={"llm_decision": response},
        decision_reasoning=response,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="retry"
    )

    # Wait before retry
    await asyncio.sleep(2)

    return {
        "audit_trail": [audit_entry],
        "current_step": 2  # Stay on JIRA account creation step
    }


# Node 4: Escalate to IT
async def escalate_to_it(state: WorkflowState) -> dict:
    """Escalate JIRA account creation failure to IT helpdesk."""
    start_time = time.time()
    employee = state["employee"]
    retry_count = state.get("retry_count", 0)
    last_error = state.get("error_log", ["Unknown error"])[-1]

    # Use LLM to draft escalation message
    prompt = f"""JIRA account creation for {employee['name']} has failed after {retry_count} attempts.
Error: {last_error}
Draft a brief IT escalation ticket with:
- Subject (one line)
- Priority (high/medium/low)
- Description (2-3 sentences)
- Suggested resolution (1-2 sentences)"""

    response, model_used, tokens_used = await call_llm_simple("reasoning", prompt)
    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="onboarding",
        agent="escalation_manager",
        action="escalate_jira_failure",
        input_data={"employee": employee["name"], "error": last_error, "retry_count": retry_count},
        output_data={"generated_content": response, "escalation_ticket": response},
        decision_reasoning=response,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="escalated"
    )

    # Send Slack notification to IT helpdesk
    await mock_systems.send_slack_message(
        "#it-helpdesk",
        f"🚨 Escalation: JIRA account creation failed for {employee['name']}. See ticket for details."
    )

    return {
        "audit_trail": [audit_entry],
        "current_step": 3,
        "notifications_sent": [{"channel": "it-helpdesk", "type": "escalation"}]
    }


# Node 5: Create Email Account
async def create_email_account(state: WorkflowState) -> dict:
    """Create email account for new employee."""
    start_time = time.time()
    employee = state["employee"]

    try:
        result = await mock_systems.create_email_account(employee["name"])

        duration_ms = (time.time() - start_time) * 1000

        audit_entry = audit_logger.log(
            scenario="onboarding",
            agent="system_provisioner",
            action="create_email_account",
            input_data={"name": employee["name"]},
            output_data=result,
            decision_reasoning="Creating email account for new employee",
            model_used="none",
            tokens_used=0,
            duration_ms=duration_ms,
            status="success"
        )

        return {
            "accounts_created": [result],
            "current_step": 4,
            "audit_trail": [audit_entry]
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        audit_entry = audit_logger.log(
            scenario="onboarding",
            agent="system_provisioner",
            action="create_email_account",
            input_data={"name": employee["name"]},
            output_data={},
            decision_reasoning="Failed to create email account",
            error=str(e),
            duration_ms=duration_ms,
            status="failure"
        )

        return {
            "error_log": [f"Email account creation failed: {str(e)}"],
            "audit_trail": [audit_entry]
        }


# Node 6: Assign Buddy
async def assign_buddy_node(state: WorkflowState) -> dict:
    """Assign onboarding buddy and generate introduction message."""
    start_time = time.time()
    employee = state["employee"]

    # Assign buddy
    buddy_result = await mock_systems.assign_buddy(
        employee["department"],
        employee["name"]
    )

    # Use LLM to write personalized buddy introduction
    prompt = f"""Write a warm, personalized introduction message for {employee['name']} (new {employee['role']}) to their onboarding buddy {buddy_result['buddy_name']}.
Include:
- Brief welcome
- Buddy's role in onboarding
- Encouragement to reach out with questions
Keep it under 100 words and friendly."""

    intro_message, model_used, tokens_used = await call_llm_simple("reasoning", prompt)
    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="onboarding",
        agent="people_coordinator",
        action="assign_buddy",
        input_data={"employee": employee["name"], "department": employee["department"]},
        output_data={"generated_content": intro_message, "buddy": buddy_result, "intro_message": intro_message},
        decision_reasoning=f"Buddy Assignment: {buddy_result['buddy_name']} ({buddy_result['buddy_email']})\n\nIntroduction Message:\n{intro_message}",
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "buddy_assigned": buddy_result["buddy_name"],
        "current_step": 5,
        "audit_trail": [audit_entry]
    }


# Node 7: Schedule Orientation
async def schedule_orientation(state: WorkflowState) -> dict:
    """Schedule orientation meeting for new employee."""
    start_time = time.time()
    employee = state["employee"]
    buddy = state.get("buddy_assigned", "HR Team")

    # Schedule orientation meeting
    attendees = [
        employee["email"],
        f"{buddy.lower().replace(' ', '.')}@company.com",
        employee.get("manager", "manager") + "@company.com",
        "hr@company.com"
    ]

    result = await mock_systems.schedule_meeting(
        title=f"Orientation - {employee['name']}",
        attendees=attendees,
        date=employee["start_date"],
        duration_min=60
    )

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="onboarding",
        agent="people_coordinator",
        action="schedule_orientation",
        input_data={"employee": employee["name"], "attendees": attendees},
        output_data=result,
        decision_reasoning="Scheduled orientation meeting with new hire, buddy, manager, and HR",
        model_used="none",
        tokens_used=0,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "orientation_scheduled": True,
        "current_step": 6,
        "audit_trail": [audit_entry]
    }


# Node 8: Send Welcome Pack
async def send_welcome_pack(state: WorkflowState) -> dict:
    """Generate and send personalized welcome email."""
    start_time = time.time()
    employee = state["employee"]
    buddy = state.get("buddy_assigned", "your onboarding buddy")

    # Use LLM to generate welcome email
    prompt = f"""Write a warm, professional welcome email for {employee['name']} joining {employee['department']} as {employee['role']}.
Their buddy is {buddy}. Orientation is on {employee['start_date']}.
Include:
- Welcome message
- First-day instructions
- Key contacts (manager: {employee.get('manager', 'TBD')}, buddy: {buddy})
- What to bring
Keep it under 200 words."""

    welcome_email, model_used, tokens_used = await call_llm_simple("summarization", prompt)

    # Send email
    await mock_systems.send_email(
        to=[employee["email"]],
        subject=f"Welcome to {employee['department']}!",
        body=welcome_email
    )

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="onboarding",
        agent="people_coordinator",
        action="send_welcome_pack",
        input_data={"employee": employee["name"]},
        output_data={"generated_content": welcome_email, "email_sent": True, "email_sent_to": employee["email"]},
        decision_reasoning=welcome_email,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "welcome_sent": True,
        "current_step": 7,
        "status": "completed",
        "audit_trail": [audit_entry]
    }


# Conditional routing function
def route_after_jira(state: WorkflowState) -> str:
    """Route after JIRA account creation based on error status and retry count."""
    error_log = state.get("error_log", [])
    retry_count = state.get("retry_count", 0)

    # Check if last error was JIRA-related
    if error_log and "JIRA" in error_log[-1]:
        if retry_count < MAX_RETRIES:
            return "retry"
        else:
            return "escalate"

    return "success"


# Build the graph
graph = StateGraph(WorkflowState)

# Add nodes
graph.add_node("create_ad_account", create_ad_account)
graph.add_node("create_jira_account_node", create_jira_account_node)
graph.add_node("handle_jira_retry", handle_jira_retry)
graph.add_node("escalate_to_it", escalate_to_it)
graph.add_node("create_email_account", create_email_account)
graph.add_node("assign_buddy_node", assign_buddy_node)
graph.add_node("schedule_orientation", schedule_orientation)
graph.add_node("send_welcome_pack", send_welcome_pack)

# Add edges
graph.set_entry_point("create_ad_account")
graph.add_edge("create_ad_account", "create_jira_account_node")

# Conditional edge after JIRA
graph.add_conditional_edges(
    "create_jira_account_node",
    route_after_jira,
    {
        "success": "create_email_account",
        "retry": "handle_jira_retry",
        "escalate": "escalate_to_it"
    }
)

graph.add_edge("handle_jira_retry", "create_jira_account_node")
graph.add_edge("escalate_to_it", "create_email_account")
graph.add_edge("create_email_account", "assign_buddy_node")
graph.add_edge("assign_buddy_node", "schedule_orientation")
graph.add_edge("schedule_orientation", "send_welcome_pack")
graph.add_edge("send_welcome_pack", END)

# Compile and export
onboarding_graph = graph.compile()
