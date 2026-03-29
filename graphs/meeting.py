import time
import asyncio
import json
import re
from langgraph.graph import StateGraph, END
from models import WorkflowState
from llm_router import call_llm, call_llm_simple
from audit import audit_logger
import mock_systems


# Helper function to parse JSON from LLM response (handles markdown code blocks)
def parse_json_from_llm(response: str) -> list:
    """Extract and parse JSON from LLM response, handling markdown code blocks."""
    # Remove markdown code blocks if present
    response = response.strip()

    # Try to extract JSON from code blocks
    json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response, re.DOTALL)
    if json_match:
        response = json_match.group(1)

    # Try to parse JSON
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # If that fails, try to find JSON array in the response
        array_match = re.search(r'\[.*\]', response, re.DOTALL)
        if array_match:
            return json.loads(array_match.group(0))
        raise


# Node 1: Extract Action Items
async def extract_action_items(state: WorkflowState) -> dict:
    """Extract action items from meeting transcript using LLM."""
    start_time = time.time()
    transcript = state["transcript"]

    # Use LLM to extract action items (routes to Gemini Flash for speed)
    prompt = f"""Analyze this meeting transcript and extract ALL action items.

TRANSCRIPT:
{transcript}

For each action item, determine:
1. Description of the task
2. Who should own it (based on context in the transcript — look for who volunteered, was assigned, or is most relevant)
3. Suggested deadline (if mentioned or inferrable)
4. Priority (high/medium/low based on urgency signals)
5. Confidence score (0.0-1.0) for the owner assignment. Use 0.0 if NO clear owner can be determined.

CRITICAL: If you cannot determine a clear owner for an action item, set owner to null and confidence to 0.0. Do NOT guess.

Respond ONLY in this JSON format, no other text:
[
  {{
    "description": "...",
    "owner": "Name" or null,
    "deadline": "YYYY-MM-DD" or null,
    "priority": "high|medium|low",
    "confidence": 0.0-1.0
  }}
]"""

    response, model_used, tokens_used = await call_llm_simple("action_item_extraction", prompt)

    # Parse JSON response
    try:
        action_items = parse_json_from_llm(response)
    except Exception as e:
        # Fallback if parsing fails
        action_items = []
        response = f"Error parsing LLM response: {e}. Response was: {response[:200]}"

    duration_ms = (time.time() - start_time) * 1000

    # Format action items for display
    action_items_formatted = "\n".join([
        f"• {item.get('description', 'No description')}\n  Owner: {item.get('owner') or '⚠️ NO OWNER - FLAGGED'} | Priority: {item.get('priority', 'medium')} | Confidence: {item.get('confidence', 0.0)}"
        for item in action_items
    ]) if action_items else "No action items extracted"

    audit_entry = audit_logger.log(
        scenario="meeting",
        agent="action_item_extractor",
        action="extract_action_items",
        input_data={"transcript_length": len(transcript)},
        output_data={"generated_content": action_items_formatted, "action_items": action_items, "count": len(action_items)},
        decision_reasoning=f"Extracted {len(action_items)} action items from meeting transcript:\n\n{action_items_formatted}",
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "action_items": action_items,
        "current_step": 2,
        "audit_trail": [audit_entry]
    }


# Node 2: Identify Owners
async def identify_owners(state: WorkflowState) -> dict:
    """Review action items and flag unclear ownership."""
    start_time = time.time()
    action_items = state.get("action_items", [])
    participants = state.get("transcript", "")  # We'll extract participants from context

    # Categorize action items by confidence
    pending_items = []
    flagged_items = []

    for item in action_items:
        owner = item.get("owner")
        confidence = item.get("confidence", 0.0)

        if owner and confidence >= 0.5:
            item["status"] = "pending"
            pending_items.append(item)
        else:
            item["status"] = "flagged"
            flagged_items.append(item)

    # If there are flagged items, use LLM to double-check
    llm_reasoning = ""
    model_used = "none"
    tokens_used = 0

    if flagged_items:
        # Extract participant list from state
        participants_list = state.get("participants", ["Unknown participants"])

        prompt = f"""These action items have unclear ownership:
{json.dumps(flagged_items, indent=2)}

The meeting participants were: {', '.join(participants_list)}

Can you determine owners for these action items based on typical roles and responsibilities?
If ownership is still unclear, confirm they should be flagged for human input.

Respond with your reasoning and final recommendation."""

        llm_response, model_used, tokens_used = await call_llm_simple("owner_identification", prompt)
        llm_reasoning = llm_response

    duration_ms = (time.time() - start_time) * 1000

    human_input_needed = len(flagged_items) > 0

    # Build reasoning text
    owner_analysis = f"ACTION ITEM OWNERSHIP ANALYSIS:\n\n"
    owner_analysis += f"✓ Items with clear owners: {len(pending_items)}\n"
    owner_analysis += f"⚠️ Items flagged for human review: {len(flagged_items)}\n\n"

    if pending_items:
        owner_analysis += "ASSIGNED ITEMS:\n"
        for item in pending_items:
            owner_analysis += f"• {item.get('description', 'N/A')[:60]}... → {item.get('owner')} (confidence: {item.get('confidence', 0)})\n"

    if flagged_items:
        owner_analysis += "\nFLAGGED FOR HUMAN INPUT:\n"
        for item in flagged_items:
            owner_analysis += f"• {item.get('description', 'N/A')[:60]}... → ⚠️ No clear owner\n"

    if llm_reasoning:
        owner_analysis += f"\nLLM ANALYSIS:\n{llm_reasoning}"

    audit_entry = audit_logger.log(
        scenario="meeting",
        agent="owner_identifier",
        action="identify_owners",
        input_data={"action_items_count": len(action_items)},
        output_data={
            "generated_content": owner_analysis,
            "pending_items": len(pending_items),
            "flagged_items": len(flagged_items),
            "human_input_needed": human_input_needed
        },
        decision_reasoning=owner_analysis,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success" if not human_input_needed else "escalated"
    )

    return {
        "action_items": action_items,
        "human_input_needed": human_input_needed,
        "current_step": 3,
        "audit_trail": [audit_entry]
    }


# Node 3: Handle Human Input
async def handle_human_input(state: WorkflowState) -> dict:
    """Simulate human input for flagged action items."""
    start_time = time.time()
    action_items = state.get("action_items", [])

    # Find flagged items
    flagged_items = [item for item in action_items if item.get("status") == "flagged"]

    # Simulate human operator reviewing and assigning
    # In a real system, this would pause and wait for actual human input
    await asyncio.sleep(2)  # Simulate thinking time

    # Auto-assign flagged items to a default person for demo
    assignments = []
    for item in flagged_items:
        # Default assignment based on description keywords
        description = item.get("description", "").lower()

        if "document" in description or "api" in description or "write" in description:
            assigned_owner = "Rahul Mehta"  # Engineering manager for docs
        elif "test" in description:
            assigned_owner = "Neha Gupta"  # QA lead
        elif "design" in description or "mockup" in description:
            assigned_owner = "Vikram Patel"  # Design lead
        else:
            assigned_owner = "Ananya Desai"  # Product manager as default

        item["owner"] = assigned_owner
        item["status"] = "pending"
        item["confidence"] = 0.7  # Human-assigned confidence

        assignments.append({
            "description": item["description"],
            "assigned_to": assigned_owner
        })

    duration_ms = (time.time() - start_time) * 1000

    # Build human assignment summary
    human_summary = "HUMAN OPERATOR ASSIGNMENTS:\n\n"
    for a in assignments:
        human_summary += f"✓ \"{a['description']}\"\n  → Assigned to: {a['assigned_to']}\n\n"

    audit_entry = audit_logger.log(
        scenario="meeting",
        agent="human_operator",
        action="assign_unclear_owners",
        input_data={"flagged_items": len(flagged_items)},
        output_data={"generated_content": human_summary, "assignments": assignments},
        decision_reasoning=human_summary,
        model_used="none",
        tokens_used=0,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "action_items": action_items,
        "human_input_needed": False,
        "current_step": 3,
        "audit_trail": [audit_entry]
    }


# Node 4: Create Tasks
async def create_tasks_node(state: WorkflowState) -> dict:
    """Create tasks in project tracker for all action items."""
    start_time = time.time()
    action_items = state.get("action_items", [])

    created_tasks = []

    # Create tasks for each action item with an owner
    for item in action_items:
        if item.get("owner") and item.get("status") == "pending":
            try:
                task_result = await mock_systems.create_task(
                    title=item["description"],
                    assignee=item["owner"],
                    description=f"From meeting action item. Deadline: {item.get('deadline', 'TBD')}",
                    priority=item.get("priority", "medium")
                )

                created_tasks.append({
                    "task_id": task_result["task_id"],
                    "title": item["description"],
                    "assignee": item["owner"],
                    "source_action_item": item["description"],
                    "created_at": "2026-03-29",
                    "tracker": "ProjectTracker"
                })

                # Mark item as created
                item["status"] = "created"

            except Exception as e:
                # Log error but continue with other tasks
                item["status"] = "flagged"
                item["error"] = str(e)

    # Use LLM to generate task creation summary
    prompt = f"""Generate a brief summary of task creation.

    Created {len(created_tasks)} tasks:
    {json.dumps(created_tasks, indent=2)}

    Provide a one-sentence summary."""

    summary, model_used, tokens_used = await call_llm_simple("summarization", prompt)

    duration_ms = (time.time() - start_time) * 1000

    # Build tasks created summary
    tasks_summary = f"TASKS CREATED IN PROJECT TRACKER:\n\n"
    for task in created_tasks:
        tasks_summary += f"✓ {task['title']}\n  → Assignee: {task['assignee']}\n  → Task ID: {task['task_id']}\n\n"

    audit_entry = audit_logger.log(
        scenario="meeting",
        agent="task_creator",
        action="create_tasks",
        input_data={"action_items_count": len(action_items)},
        output_data={"generated_content": tasks_summary, "tasks_created": created_tasks, "summary": summary},
        decision_reasoning=tasks_summary,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "tasks_created": created_tasks,
        "action_items": action_items,
        "current_step": 4,
        "audit_trail": [audit_entry]
    }


# Node 5: Send Meeting Summary
async def send_meeting_summary(state: WorkflowState) -> dict:
    """Generate and send meeting follow-up email."""
    start_time = time.time()
    action_items = state.get("action_items", [])
    tasks_created = state.get("tasks_created", [])
    participants_list = state.get("participants", ["team"])

    # Prepare action items summary
    action_items_text = "\n".join([
        f"- {item['description']} (Owner: {item.get('owner', 'TBD')}, Deadline: {item.get('deadline', 'TBD')})"
        for item in action_items
    ])

    # Prepare task IDs
    task_ids = [task["task_id"] for task in tasks_created]

    # Use LLM to generate meeting summary email
    prompt = f"""Write a professional meeting follow-up email.

Meeting had these participants: {', '.join(participants_list)}

Action items created:
{action_items_text}

Tasks created in tracker: {', '.join(task_ids)}

Keep it concise — bullet points for action items, who owns what, deadlines. Under 150 words."""

    email_body, model_used, tokens_used = await call_llm_simple("summarization", prompt)

    # Send email to all participants
    participant_emails = [f"{p.lower().replace(' ', '.')}@company.com" for p in participants_list]

    await mock_systems.send_email(
        to=participant_emails,
        subject="Meeting Follow-up: Action Items & Tasks",
        body=email_body
    )

    duration_ms = (time.time() - start_time) * 1000

    audit_entry = audit_logger.log(
        scenario="meeting",
        agent="meeting_coordinator",
        action="send_meeting_summary",
        input_data={"participants": participants_list, "tasks_count": len(tasks_created)},
        output_data={"generated_content": email_body, "email_sent": True, "recipients": participant_emails},
        decision_reasoning=email_body,
        model_used=model_used,
        tokens_used=tokens_used,
        duration_ms=duration_ms,
        status="success"
    )

    return {
        "status": "completed",
        "notifications_sent": [{"type": "email", "recipients": participant_emails}],
        "current_step": 5,
        "audit_trail": [audit_entry]
    }


# Conditional routing function
def route_after_owner_check(state: WorkflowState) -> str:
    """Route based on whether human input is needed."""
    if state.get("human_input_needed"):
        return "handle_human_input"
    return "create_tasks_node"


# Build the graph
graph = StateGraph(WorkflowState)

# Add nodes
graph.add_node("extract_action_items", extract_action_items)
graph.add_node("identify_owners", identify_owners)
graph.add_node("handle_human_input", handle_human_input)
graph.add_node("create_tasks_node", create_tasks_node)
graph.add_node("send_meeting_summary", send_meeting_summary)

# Add edges
graph.set_entry_point("extract_action_items")
graph.add_edge("extract_action_items", "identify_owners")

# Conditional edge after owner identification
graph.add_conditional_edges(
    "identify_owners",
    route_after_owner_check,
    {
        "handle_human_input": "handle_human_input",
        "create_tasks_node": "create_tasks_node"
    }
)

graph.add_edge("handle_human_input", "create_tasks_node")
graph.add_edge("create_tasks_node", "send_meeting_summary")
graph.add_edge("send_meeting_summary", END)

# Compile and export
meeting_graph = graph.compile()
