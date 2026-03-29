from typing import TypedDict, Annotated, Optional, Literal, List
import operator
from pydantic import BaseModel, Field
from uuid import uuid4
from datetime import datetime


# Pydantic Models (for data validation)

class AuditEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    scenario: Literal["onboarding", "meeting", "sla"]
    agent: str
    action: str
    input_data: dict
    output_data: dict
    decision_reasoning: str
    model_used: str
    tokens_used: int
    duration_ms: float
    error: Optional[str] = None
    status: Literal["success", "failure", "retry", "escalated"]


class Employee(BaseModel):
    name: str
    email: str
    department: str
    role: str
    manager: str
    start_date: str


class ActionItem(BaseModel):
    description: str
    owner: Optional[str] = None
    deadline: Optional[str] = None
    priority: Literal["high", "medium", "low"]
    status: Literal["pending", "created", "flagged"]
    confidence: float


class TaskCreated(BaseModel):
    task_id: str
    title: str
    assignee: str
    source_action_item: str
    created_at: str
    tracker: str


class ApprovalRequest(BaseModel):
    request_id: str
    type: str
    requested_by: str
    approver: str
    submitted_at: str
    sla_deadline: str
    status: Literal["pending", "approved", "rerouted", "escalated"]
    delegate: Optional[str] = None


# LangGraph State (TypedDict)

class WorkflowState(TypedDict):
    scenario: str
    status: str
    current_step: int
    total_steps: int
    employee: Optional[dict]
    transcript: Optional[str]
    action_items: list[dict]
    tasks_created: Annotated[list[dict], operator.add]
    approval: Optional[dict]
    accounts_created: Annotated[list[dict], operator.add]
    buddy_assigned: Optional[str]
    orientation_scheduled: bool
    welcome_sent: bool
    error_log: Annotated[list[str], operator.add]
    retry_count: int
    human_input_needed: bool
    human_input_response: Optional[str]
    audit_trail: Annotated[list[dict], operator.add]
    messages: Annotated[list, operator.add]
    notifications_sent: Annotated[list[dict], operator.add]
