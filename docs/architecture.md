# WorkflowPilot — Multi-Agent Architecture for Autonomous Enterprise Workflows

**ET AI Hackathon 2026 | Technical Architecture Document**

---

## 1. System Overview

WorkflowPilot is a multi-agent system built on LangGraph that autonomously manages complex enterprise workflows. It uses a hub-and-spoke orchestration pattern where a central Orchestrator routes workflow triggers to scenario-specific sub-graphs. Each sub-graph contains specialized agents that execute, verify, and recover from failures autonomously. Every decision is logged to an immutable audit trail for enterprise compliance, enabling full transparency and auditability of AI-driven actions.

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              TRIGGER LAYER                                   │
│         ┌──────────┐    ┌──────────┐    ┌──────────┐                        │
│         │ REST API │    │ Webhook  │    │  Timer   │                        │
│         └────┬─────┘    └────┬─────┘    └────┬─────┘                        │
└──────────────┼───────────────┼───────────────┼──────────────────────────────┘
               └───────────────┼───────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ORCHESTRATOR (LangGraph)                            │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  classify_trigger() ──► route_to_scenario() ──► finalize_workflow() │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                    │                │                │                       │
└────────────────────┼────────────────┼────────────────┼───────────────────────┘
                     ▼                ▼                ▼
    ┌────────────────────┐ ┌────────────────────┐ ┌────────────────────┐
    │  ONBOARDING GRAPH  │ │   MEETING GRAPH    │ │     SLA GRAPH      │
    │                    │ │                    │ │                    │
    │ ┌────────────────┐ │ │ ┌────────────────┐ │ │ ┌────────────────┐ │
    │ │ Create AD Acct │ │ │ │ Extract Items  │ │ │ │ Detect Breach  │ │
    │ └───────┬────────┘ │ │ └───────┬────────┘ │ │ └───────┬────────┘ │
    │         ▼          │ │         ▼          │ │         ▼          │
    │ ┌────────────────┐ │ │ ┌────────────────┐ │ │ ┌────────────────┐ │
    │ │ Create JIRA ───┼─┼─┼─┤► RETRY LOOP    │ │ │ │ Find Bottleneck│ │
    │ └───────┬────────┘ │ │ └───────┬────────┘ │ │ └───────┬────────┘ │
    │    [error?]        │ │         ▼          │ │         ▼          │
    │    ▼    ▼          │ │ ┌────────────────┐ │ │ ┌────────────────┐ │
    │ retry  escalate    │ │ │ Human Input?───┼─┼─┼─┤► HUMAN-IN-LOOP │ │
    │         ▼          │ │ └───────┬────────┘ │ │ └───────┬────────┘ │
    │ ┌────────────────┐ │ │         ▼          │ │         ▼          │
    │ │ Create Email   │ │ │ ┌────────────────┐ │ │ ┌────────────────┐ │
    │ │ Assign Buddy   │ │ │ │ Create Tasks   │ │ │ │ Reroute Approv │ │
    │ │ Schedule Orient│ │ │ │ Send Summary   │ │ │ │ Log Compliance │ │
    │ │ Send Welcome   │ │ │ └────────────────┘ │ │ └────────────────┘ │
    │ └────────────────┘ │ │                    │ │                    │
    └────────────────────┘ └────────────────────┘ └────────────────────┘
                     │                │                │
                     └────────────────┼────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SHARED TOOL LAYER                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Active   │ │  JIRA    │ │ Calendar │ │  Slack   │ │  Email   │          │
│  │ Directory│ │          │ │          │ │          │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                     ┌────────────────┼────────────────┐
                     ▼                ▼                ▼
┌────────────────────────┐ ┌────────────────────────┐ ┌──────────────────────┐
│      LLM ROUTER        │ │    ERROR RECOVERY      │ │    AUDIT TRAIL       │
│ ┌────────────────────┐ │ │ ┌────────────────────┐ │ │ ┌────────────────┐   │
│ │ Groq Llama 3.3 70B │ │ │ │ Tier 1: Retry      │ │ │ │ JSON Lines     │   │
│ │ (Complex Reasoning)│ │ │ │ Tier 2: Reroute    │ │ │ │ Append-Only    │   │
│ ├────────────────────┤ │ │ │ Tier 3: Escalate   │ │ │ │ Immutable      │   │
│ │ Gemini 2.0 Flash   │ │ │ └────────────────────┘ │ │ └────────────────┘   │
│ │ (Fast Extraction)  │ │ │                        │ │                      │
│ └────────────────────┘ │ │                        │ │                      │
└────────────────────────┘ └────────────────────────┘ └──────────────────────┘
```

---

## 3. Agent Roles

| Agent | Responsibility | Scenarios | LLM Model |
|-------|---------------|-----------|-----------|
| **Orchestrator** | Classifies triggers, routes to sub-graphs, finalizes workflows | All | Gemini Flash (classification) |
| **System Provisioner** | Creates accounts (AD, JIRA, Email) across enterprise systems | Onboarding | None (API calls) |
| **People Coordinator** | Assigns buddies, schedules orientation, sends welcome communications | Onboarding | Llama 70B (personalization) |
| **NLP Analyst** | Extracts action items, identifies owners, analyzes meeting content | Meeting | Gemini Flash (extraction) |
| **Task Manager** | Creates and tracks tasks in project management systems | Meeting | Llama 70B (summarization) |
| **SLA Monitor** | Detects breaches, analyzes bottlenecks, manages approvals | SLA | Llama 70B (reasoning) |
| **Recovery Agent** | Analyzes errors, coordinates retries, escalates to humans/IT | All | Llama 70B (error analysis) |

---

## 4. Orchestration Pattern

WorkflowPilot implements a **hierarchical state machine** using LangGraph's composable graph architecture:

```python
# Parent Graph: Routes triggers to scenario-specific sub-graphs
graph.add_conditional_edges(
    "classify_trigger",
    route_to_scenario,  # LLM-based classification
    {
        "onboarding": "run_onboarding",
        "meeting": "run_meeting",
        "sla": "run_sla"
    }
)

# Sub-graphs execute with shared state (TypedDict)
class WorkflowState(TypedDict):
    scenario: str
    current_step: int
    audit_trail: Annotated[list, operator.add]  # Accumulates across nodes
    error_log: Annotated[list, operator.add]
    # ... scenario-specific fields
```

**Key Design Decisions:**
- **Partial State Updates**: Each node returns only changed fields; LangGraph merges updates
- **Accumulated Fields**: Audit trail and error logs use `Annotated[list, operator.add]` for automatic accumulation
- **Async Execution**: All nodes are `async def` for efficient I/O operations

---

## 5. Error Handling & Recovery

WorkflowPilot implements a **3-tier recovery pattern** with conditional edge routing:

| Tier | Strategy | Trigger Condition | Example |
|------|----------|-------------------|---------|
| **Tier 1** | Retry with delay | Transient errors (API timeouts, rate limits) | JIRA 403 → retry up to 3x |
| **Tier 2** | Reroute to alternative | Resource unavailable | Approver on leave → delegate |
| **Tier 3** | Escalate to human | Recovery failed or ambiguous decision | Create IT ticket + Slack alert |

```python
def route_after_jira(state: WorkflowState) -> str:
    if "JIRA" in state["error_log"][-1]:
        if state["retry_count"] < MAX_RETRIES:
            return "retry"      # Tier 1: Retry
        return "escalate"       # Tier 3: Human escalation
    return "success"            # Continue workflow
```

**LLM-Powered Error Analysis**: Before retry or escalation, the Recovery Agent uses Llama 70B to analyze the error and recommend the appropriate tier.

---

## 6. Cost-Efficient Model Routing

WorkflowPilot uses **dual-model intelligent routing** to optimize cost and latency:

| Task Type | Model | Latency | Cost |
|-----------|-------|---------|------|
| `reasoning`, `decision_making`, `error_analysis` | Groq Llama 3.3 70B | ~2s | Higher |
| `extraction`, `classification`, `summarization` | Gemini 2.0 Flash | ~0.5s | Lower |

```python
def get_llm(task_type: str) -> BaseChatModel:
    if task_type in EXTRACTION_TASKS:
        return fast_llm   # Gemini Flash
    return heavy_llm      # Llama 70B
```

**Automatic Fallback**: If the primary model fails, the router automatically switches to the secondary model, ensuring workflow continuity.

**Estimated Savings**: 60% cost reduction vs. using Llama 70B for all tasks, with 40% latency improvement for extraction-heavy workflows.

---

## 7. Audit Trail Design

Every agent action is logged to an **append-only JSON Lines file** for enterprise compliance:

```json
{
  "id": "uuid-v4",
  "timestamp": "2026-03-29T10:15:32.123Z",
  "scenario": "onboarding",
  "agent": "system_provisioner",
  "action": "create_jira_account",
  "input_data": {"employee": "Priya Sharma"},
  "output_data": {"account_id": "..."},
  "decision_reasoning": "Creating JIRA account for new employee",
  "model_used": "none",
  "tokens_used": 0,
  "duration_ms": 1523.4,
  "status": "success"
}
```

**Query Capabilities**: Filter by scenario, agent, time range, or status. Real-time summary statistics track total actions, LLM calls, errors, and token usage.

---

## 8. Impact Quantification

| Metric | Manual Process | WorkflowPilot | Improvement |
|--------|---------------|---------------|-------------|
| **Onboarding Time** | 4-6 hours | ~45 seconds | **99% faster** |
| **Meeting Follow-up** | 30-60 minutes | ~20 seconds | **99% faster** |
| **SLA Breach Response** | Hours to detect | Instant | **Proactive** |
| **Human Touchpoints** | 5-10 per workflow | 0-1 (edge cases) | **90% reduction** |
| **Error Recovery** | Manual escalation | Autonomous retry | **100% automated** |
| **Audit Compliance** | Manual documentation | Automatic logging | **100% coverage** |

---

## 9. Extensibility for Surprise Scenarios

WorkflowPilot is designed for rapid extension:

| Extension Task | Required Changes | Estimated Time |
|----------------|------------------|----------------|
| Add new scenario | New sub-graph + routing condition | < 30 minutes |
| Add new integration | New tool in shared layer | < 15 minutes |
| Modify workflow steps | Edit existing sub-graph | < 10 minutes |

**Key Extensibility Features:**
- **LLM-based trigger classification** handles unknown scenario types automatically
- **Shared tool layer** allows new scenarios to reuse existing integrations
- **Modular sub-graphs** can be developed and tested independently
- **TypedDict state** ensures type safety when adding new fields

---

**Built with**: LangGraph • Groq Llama 3.3 70B • Google Gemini 2.0 Flash • FastAPI • React

**Team**: TensorZ
