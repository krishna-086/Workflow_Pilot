import time
from langgraph.graph import StateGraph, END
from models import WorkflowState
from llm_router import call_llm_simple
from audit import audit_logger
import mock_systems


# Node 1: Detect SLA Breach
async def detect_sla_breach(state: WorkflowState) -> dict:
    """Detect and assess SLA breach severity."""
    start_time = time.time()
    approval = state["approval"]
    request_id = approval["request_id"]

    # Call mock approval status check
    status_result = await mock_systems.get_approval_status(request_id)

    # Check if SLA threshold is breached
    stuck_hours = status_result.get("stuck_since_hours", 0)
    sla_threshold = 24
    sla_breached = stuck_hours > sla_threshold

    # Use LLM to assess risk severity
    prompt = f"""A procurement approval (ID: {request_id}) has been stuck for {stuck_hours} hours.
SLA threshold is {sla_threshold} hours.
The approver {status_result['approver']} status is: {status_result['approver_status']}.

Assess the breach severity (critical/high/medium) and recommend immediate action. Be concise."""

    risk_assessment, model_used, tokens_used = await call_llm_simple("reasoning", prompt)

    duration_ms = (time.time() - start_time) * 1000

    # Build detailed breach analysis
    breach_analysis = f"SLA BREACH DETECTION:\n\n"
    breach_analysis += f"Request ID: {request_id}\n"
    breach_analysis += f"Stuck Duration: {stuck_hours} hours\n"
    breach_analysis += f"SLA Threshold: {sla_threshold} hours\n"
    breach_analysis += f"Hours Overdue: {stuck_hours - sla_threshold}\n"
    breach_analysis += f"Approver: {status_result['approver']}\n"
    breach_analysis += f"Approver Status: {status_result['approver_status']}\n\n"
    breach_analysis += f"RISK ASSESSMENT:\n{risk_assessment}"

    audit_entry = audit_logger.log(
        scenario="sla",
        agent="sla_monitor",
        action="detect_sla_breach",
        input_data=approval,
        output_data={
            "generated_content": breach_analysis,
            "status_result": status_result,
            "sla_breached": sla_breached,
            "hours_overdue": stuck_hours - sla_threshold
        },
        decision_reasoning=breach_analysis,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="escalated" if sla_breached else "success"
    )

    # Update approval state with status details
    updated_approval = {**approval, **status_result}

    return {
        "approval": updated_approval,
        "current_step": 2,
        "audit_trail": [audit_entry]
    }


# Node 2: Identify Bottleneck
async def identify_bottleneck(state: WorkflowState) -> dict:
    """Analyze why the approval is stuck."""
    start_time = time.time()
    approval = state["approval"]

    approver_name = approval["approver"]
    approver_status = approval["approver_status"]
    request_id = approval["request_id"]

    # Use LLM to identify root cause
    prompt = f"""Approval {request_id} is stuck.
Approver: {approver_name}
Status: {approver_status}

Possible reasons:
1) Approver on leave
2) Approval lost in queue
3) Missing information

Based on the approver status '{approver_status}', identify the root cause and recommend the best resolution path."""

    root_cause_analysis, model_used, tokens_used = await call_llm_simple("reasoning", prompt)

    # Determine bottleneck category
    if "leave" in approver_status.lower() or "away" in approver_status.lower():
        bottleneck_type = "approver_on_leave"
    elif "busy" in approver_status.lower() or "queue" in approver_status.lower():
        bottleneck_type = "approval_queue_overload"
    else:
        bottleneck_type = "unknown"

    duration_ms = (time.time() - start_time) * 1000

    # Build bottleneck analysis summary
    bottleneck_analysis = f"BOTTLENECK ANALYSIS:\n\n"
    bottleneck_analysis += f"Request ID: {request_id}\n"
    bottleneck_analysis += f"Approver: {approver_name}\n"
    bottleneck_analysis += f"Status: {approver_status}\n"
    bottleneck_analysis += f"Bottleneck Type: {bottleneck_type}\n\n"
    bottleneck_analysis += f"ROOT CAUSE ANALYSIS:\n{root_cause_analysis}"

    audit_entry = audit_logger.log(
        scenario="sla",
        agent="bottleneck_analyzer",
        action="identify_bottleneck",
        input_data={
            "request_id": request_id,
            "approver": approver_name,
            "status": approver_status
        },
        output_data={
            "generated_content": bottleneck_analysis,
            "bottleneck_type": bottleneck_type,
            "root_cause": root_cause_analysis
        },
        decision_reasoning=bottleneck_analysis,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    # Add bottleneck info to approval
    updated_approval = {**approval, "bottleneck_type": bottleneck_type}

    return {
        "approval": updated_approval,
        "current_step": 3,
        "audit_trail": [audit_entry]
    }


# Node 3: Find Delegate
async def find_delegate(state: WorkflowState) -> dict:
    """Identify and verify appropriate delegate."""
    start_time = time.time()
    approval = state["approval"]

    approver_name = approval["approver"]
    delegate_name = approval.get("delegate", "No delegate assigned")
    approval_type = approval["type"]
    request_id = approval["request_id"]

    # Use LLM to verify delegation
    prompt = f"""The approver {approver_name} is on leave.
Their designated delegate is {delegate_name}.

Verify this delegation is appropriate for a {approval_type} approval of this priority.
Confirm or suggest alternative if needed. Be concise."""

    delegation_verification, model_used, tokens_used = await call_llm_simple("reasoning", prompt)

    duration_ms = (time.time() - start_time) * 1000

    # Build delegate verification summary
    delegate_summary = f"DELEGATION VERIFICATION:\n\n"
    delegate_summary += f"Request ID: {request_id}\n"
    delegate_summary += f"Original Approver: {approver_name} (on leave)\n"
    delegate_summary += f"Proposed Delegate: {delegate_name}\n"
    delegate_summary += f"Approval Type: {approval_type}\n\n"
    delegate_summary += f"VERIFICATION RESULT:\n{delegation_verification}"

    audit_entry = audit_logger.log(
        scenario="sla",
        agent="delegation_manager",
        action="find_delegate",
        input_data={
            "request_id": request_id,
            "original_approver": approver_name,
            "proposed_delegate": delegate_name
        },
        output_data={
            "generated_content": delegate_summary,
            "delegate_confirmed": delegate_name,
            "verification": delegation_verification
        },
        decision_reasoning=delegate_summary,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "current_step": 4,
        "audit_trail": [audit_entry]
    }


# Node 4: Execute Reroute
async def execute_reroute(state: WorkflowState) -> dict:
    """Reroute approval and send notifications."""
    start_time = time.time()
    approval = state["approval"]

    request_id = approval["request_id"]
    approver_name = approval["approver"]
    delegate_name = approval["delegate"]
    requester = approval["requested_by"]
    approval_type = approval["type"]

    # Execute reroute
    reroute_result = await mock_systems.reroute_approval(
        request_id=request_id,
        new_approver=delegate_name,
        reason=f"Original approver {approver_name} on leave; SLA breach imminent"
    )

    # Draft notifications using LLM
    # 1. Notification to delegate
    delegate_prompt = f"""Write a professional email to {delegate_name} (delegate) notifying them of an approval reroute.

Original approver: {approver_name} (on leave)
Approval type: {approval_type}
Request ID: {request_id}
Requester: {requester}
Reason: SLA breach prevention

Include: urgency, what needs to be done, deadline. Keep under 100 words."""

    delegate_email, model_used_1, tokens_1 = await call_llm_simple("summarization", delegate_prompt)

    # 2. Notification to requester
    requester_prompt = f"""Write a brief email to {requester} (requester) notifying them their approval has been rerouted.

Your approval request {request_id} has been rerouted from {approver_name} to {delegate_name} due to the original approver being on leave.
Keep it reassuring and brief (under 80 words)."""

    requester_email, model_used_2, tokens_2 = await call_llm_simple("summarization", requester_prompt)

    # 3. Notification to original approver (FYI)
    approver_prompt = f"""Write a brief FYI email to {approver_name} about an approval that was rerouted in their absence.

Approval {request_id} was rerouted to {delegate_name} while you were on leave.
This was done to prevent SLA breach. Keep it factual and brief (under 60 words)."""

    approver_email, model_used_3, tokens_3 = await call_llm_simple("summarization", approver_prompt)

    # Send emails
    await mock_systems.send_email(
        to=[f"{delegate_name.lower().replace(' ', '.')}@company.com"],
        subject=f"URGENT: Approval Rerouted to You - {request_id}",
        body=delegate_email
    )

    await mock_systems.send_email(
        to=[f"{requester.lower().replace(' ', '.')}@company.com"],
        subject=f"Approval Update: {request_id}",
        body=requester_email
    )

    await mock_systems.send_email(
        to=[f"{approver_name.lower().replace(' ', '.')}@company.com"],
        subject=f"FYI: Approval Rerouted - {request_id}",
        body=approver_email
    )

    duration_ms = (time.time() - start_time) * 1000
    total_tokens = tokens_1 + tokens_2 + tokens_3

    # Build reroute summary with email content
    reroute_summary = f"APPROVAL REROUTED:\n\n"
    reroute_summary += f"Request ID: {request_id}\n"
    reroute_summary += f"From: {approver_name} (on leave)\n"
    reroute_summary += f"To: {delegate_name}\n"
    reroute_summary += f"Override ID: {reroute_result['override_id']}\n\n"
    reroute_summary += f"EMAIL TO DELEGATE ({delegate_name}):\n{delegate_email}\n\n"
    reroute_summary += f"EMAIL TO REQUESTER ({requester}):\n{requester_email}"

    audit_entry = audit_logger.log(
        scenario="sla",
        agent="reroute_executor",
        action="execute_reroute",
        input_data={
            "request_id": request_id,
            "from": approver_name,
            "to": delegate_name
        },
        output_data={
            "generated_content": reroute_summary,
            "reroute_result": reroute_result,
            "notifications_sent": 3,
            "override_id": reroute_result["override_id"],
            "delegate_email": delegate_email,
            "requester_email": requester_email
        },
        decision_reasoning=reroute_summary,
        model_used=f"{model_used_1},{model_used_2},{model_used_3}",
        tokens_used=total_tokens,
        duration_ms=duration_ms,
        status="success"
    )

    # Update approval with reroute info
    updated_approval = {
        **approval,
        "status": "rerouted",
        "new_approver": delegate_name,
        "override_id": reroute_result["override_id"]
    }

    return {
        "approval": updated_approval,
        "current_step": 5,
        "notifications_sent": [
            {"recipient": delegate_name, "type": "reroute_notification"},
            {"recipient": requester, "type": "status_update"},
            {"recipient": approver_name, "type": "fyi"}
        ],
        "audit_trail": [audit_entry]
    }


# Node 5: Log Compliance Record
async def log_compliance_record(state: WorkflowState) -> dict:
    """Create comprehensive compliance audit record."""
    start_time = time.time()
    approval = state["approval"]

    approver_name = approval["approver"]
    delegate_name = approval["delegate"]
    request_id = approval["request_id"]
    stuck_hours = approval.get("stuck_since_hours", 0)
    override_id = approval.get("override_id", "N/A")

    # Get audit summary
    audit_summary = audit_logger.get_trail(scenario="sla")

    # Generate compliance record using LLM
    prompt = f"""Generate a compliance audit summary for this SLA override:

- Original approver: {approver_name} (on leave)
- Delegate: {delegate_name}
- Request ID: {request_id}
- Reason for override: SLA breach prevention (stuck for {stuck_hours} hours)
- Override ID: {override_id}
- Time since SLA breach: {stuck_hours - 24} hours overdue
- All actions taken: Detected breach → Identified bottleneck (approver on leave) → Found delegate → Rerouted approval → Notified all parties

Format as a structured compliance record with:
- Override ID
- Justification
- Authority Chain
- Risk Assessment
- Timestamp

Keep it concise and professional."""

    compliance_record, model_used, tokens_used = await call_llm_simple("reasoning", prompt)

    # Send Slack notification to compliance channel
    await mock_systems.send_slack_message(
        "#compliance",
        f"📋 SLA Override Logged: Request {request_id} rerouted from {approver_name} to {delegate_name}. Override ID: {override_id}. Full compliance record available in audit trail."
    )

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="sla",
        agent="compliance_recorder",
        action="log_compliance_record",
        input_data={
            "request_id": request_id,
            "override_id": override_id
        },
        output_data={
            "generated_content": compliance_record,
            "compliance_record": compliance_record
        },
        decision_reasoning=compliance_record,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "status": "completed",
        "current_step": 6,
        "audit_trail": [audit_entry],
        "notifications_sent": [{"channel": "compliance", "type": "compliance_notification"}]
    }


# Build the graph
graph = StateGraph(WorkflowState)

# Add nodes
graph.add_node("detect_sla_breach", detect_sla_breach)
graph.add_node("identify_bottleneck", identify_bottleneck)
graph.add_node("find_delegate", find_delegate)
graph.add_node("execute_reroute", execute_reroute)
graph.add_node("log_compliance_record", log_compliance_record)

# Add edges (linear flow - simplest scenario)
graph.set_entry_point("detect_sla_breach")
graph.add_edge("detect_sla_breach", "identify_bottleneck")
graph.add_edge("identify_bottleneck", "find_delegate")
graph.add_edge("find_delegate", "execute_reroute")
graph.add_edge("execute_reroute", "log_compliance_record")
graph.add_edge("log_compliance_record", END)

# Compile and export
sla_graph = graph.compile()
