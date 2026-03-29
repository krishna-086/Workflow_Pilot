import time
import json
from langgraph.graph import StateGraph, END
from models import WorkflowState
from graphs.onboarding import onboarding_graph
from graphs.meeting import meeting_graph
from graphs.sla import sla_graph
from audit import audit_logger
from llm_router import call_llm_simple


# Node 1: Classify Trigger
async def classify_trigger(state: WorkflowState) -> dict:
    """Classify the workflow trigger and route to appropriate sub-graph."""
    start_time = time.time()
    scenario = state.get("scenario", "")

    # If scenario is already set, use it directly
    if scenario in ["onboarding", "meeting", "sla"]:
        classified_scenario = scenario
        model_used = "none"
        tokens_used = 0
        reasoning = f"Scenario already specified: {scenario}"
    else:
        # Use LLM to classify unknown trigger
        trigger_data = {
            "employee": state.get("employee"),
            "transcript": state.get("transcript"),
            "approval": state.get("approval")
        }

        prompt = f"""Classify this workflow trigger into one of: onboarding, meeting, sla.

Trigger data: {json.dumps(trigger_data, indent=2)}

Respond with ONLY the category name (onboarding, meeting, or sla)."""

        response, model_used, tokens_used = await call_llm_simple("classification", prompt)
        classified_scenario = response.strip().lower()
        reasoning = f"LLM classified trigger as: {classified_scenario}"

        # Validate classification
        if classified_scenario not in ["onboarding", "meeting", "sla"]:
            classified_scenario = "meeting"  # Default fallback
            reasoning += " (invalid response, defaulting to meeting)"

    # Determine total steps based on scenario
    total_steps_map = {
        "onboarding": 7,  # 7 steps in onboarding
        "meeting": 5,     # 5 steps in meeting
        "sla": 6          # 6 steps in SLA (including finalize)
    }
    total_steps = total_steps_map.get(classified_scenario, 5)

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario=classified_scenario,
        agent="orchestrator",
        action="classify_trigger",
        input_data={"raw_scenario": scenario},
        output_data={"classified_scenario": classified_scenario, "total_steps": total_steps},
        decision_reasoning=reasoning,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "scenario": classified_scenario,
        "status": "in_progress",
        "current_step": 1,
        "total_steps": total_steps,
        "audit_trail": [audit_entry]
    }


# Node 2: Run Onboarding
async def run_onboarding(state: WorkflowState) -> dict:
    """Invoke the onboarding sub-graph."""
    start_time = time.time()

    # Invoke onboarding sub-graph
    result = await onboarding_graph.ainvoke(state)

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="onboarding",
        agent="orchestrator",
        action="run_onboarding_workflow",
        input_data={"employee": state.get("employee", {}).get("name", "Unknown")},
        output_data={"final_step": result.get("current_step", 0)},
        decision_reasoning="Completed onboarding sub-graph execution",
        model_used="none",
        tokens_used=0,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        **result,
        "audit_trail": [audit_entry]
    }


# Node 3: Run Meeting
async def run_meeting(state: WorkflowState) -> dict:
    """Invoke the meeting sub-graph."""
    start_time = time.time()

    # Invoke meeting sub-graph
    result = await meeting_graph.ainvoke(state)

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="meeting",
        agent="orchestrator",
        action="run_meeting_workflow",
        input_data={"has_transcript": bool(state.get("transcript"))},
        output_data={
            "final_step": result.get("current_step", 0),
            "tasks_created": len(result.get("tasks_created", []))
        },
        decision_reasoning="Completed meeting sub-graph execution",
        model_used="none",
        tokens_used=0,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        **result,
        "audit_trail": [audit_entry]
    }


# Node 4: Run SLA
async def run_sla(state: WorkflowState) -> dict:
    """Invoke the SLA sub-graph."""
    start_time = time.time()

    # Invoke SLA sub-graph
    result = await sla_graph.ainvoke(state)

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="sla",
        agent="orchestrator",
        action="run_sla_workflow",
        input_data={"request_id": state.get("approval", {}).get("request_id", "Unknown")},
        output_data={
            "final_step": result.get("current_step", 0),
            "approval_status": result.get("approval", {}).get("status", "Unknown")
        },
        decision_reasoning="Completed SLA sub-graph execution",
        model_used="none",
        tokens_used=0,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        **result,
        "audit_trail": [audit_entry]
    }


# Node 5: Finalize Workflow
async def finalize_workflow(state: WorkflowState) -> dict:
    """Generate final summary and complete the workflow."""
    start_time = time.time()
    scenario = state.get("scenario", "unknown")
    current_step = state.get("current_step", 0)
    total_steps = state.get("total_steps", 0)
    error_log = state.get("error_log", [])
    human_input_needed = state.get("human_input_needed", False)

    # Count human interventions
    human_input_count = 1 if human_input_needed else 0

    # Generate executive summary using LLM
    prompt = f"""Summarize the completed {scenario} workflow.

Steps completed: {current_step}/{total_steps}
Errors encountered: {len(error_log)}
Human interventions: {human_input_count}

Generate a 2-sentence executive summary highlighting key outcomes and any issues."""

    summary, model_used, tokens_used = await call_llm_simple("summarization", prompt)

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario=scenario,
        agent="orchestrator",
        action="finalize_workflow",
        input_data={
            "scenario": scenario,
            "steps_completed": current_step,
            "total_steps": total_steps
        },
        output_data={
            "summary": summary,
            "errors": len(error_log),
            "human_interventions": human_input_count
        },
        decision_reasoning=f"Workflow completed. Executive summary: {summary}",
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "status": "completed",
        "audit_trail": [audit_entry]
    }


# Conditional routing function
def route_to_scenario(state: WorkflowState) -> str:
    """Route to the appropriate sub-graph based on scenario."""
    scenario = state.get("scenario", "")

    if scenario == "onboarding":
        return "run_onboarding"
    elif scenario == "meeting":
        return "run_meeting"
    elif scenario == "sla":
        return "run_sla"
    else:
        # Default fallback
        return "run_meeting"


# Build the main orchestrator graph
graph = StateGraph(WorkflowState)

# Add nodes
graph.add_node("classify_trigger", classify_trigger)
graph.add_node("run_onboarding", run_onboarding)
graph.add_node("run_meeting", run_meeting)
graph.add_node("run_sla", run_sla)
graph.add_node("finalize_workflow", finalize_workflow)

# Add edges
graph.set_entry_point("classify_trigger")

# Conditional edge after classification
graph.add_conditional_edges(
    "classify_trigger",
    route_to_scenario,
    {
        "run_onboarding": "run_onboarding",
        "run_meeting": "run_meeting",
        "run_sla": "run_sla"
    }
)

# All sub-graphs lead to finalization
graph.add_edge("run_onboarding", "finalize_workflow")
graph.add_edge("run_meeting", "finalize_workflow")
graph.add_edge("run_sla", "finalize_workflow")
graph.add_edge("finalize_workflow", END)

# Compile the orchestrator
main_orchestrator = graph.compile()


# Convenience function to run a complete workflow
async def run_workflow(scenario: str, **kwargs) -> dict:
    """
    Run a complete workflow.

    Args:
        scenario: Workflow type ("onboarding", "meeting", or "sla")
        **kwargs: Scenario-specific data (employee, transcript, approval, participants)

    Returns:
        Final workflow state as dict
    """
    initial_state = {
        "scenario": scenario,
        "status": "pending",
        "current_step": 0,
        "total_steps": 0,
        "employee": None,
        "transcript": None,
        "action_items": [],
        "tasks_created": [],
        "approval": None,
        "accounts_created": [],
        "buddy_assigned": None,
        "orientation_scheduled": False,
        "welcome_sent": False,
        "error_log": [],
        "retry_count": 0,
        "human_input_needed": False,
        "human_input_response": None,
        "audit_trail": [],
        "messages": [],
        "notifications_sent": [],
        **kwargs  # Merge scenario-specific data
    }

    # Invoke the main orchestrator
    result = await main_orchestrator.ainvoke(initial_state)

    return result
