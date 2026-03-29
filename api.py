import asyncio
import json
import os
from uuid import uuid4
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from orchestrator import run_workflow
from audit import audit_logger
from mock_systems import reset_error_injection
from config import settings
from data.sample_data import SAMPLE_EMPLOYEE, SAMPLE_TRANSCRIPT, SAMPLE_PARTICIPANTS, SAMPLE_APPROVAL


# Create FastAPI app
app = FastAPI(
    title="WorkflowPilot",
    description="Multi-Agent Enterprise Workflow System - ET AI Hackathon 2026"
)

# Add CORS middleware (allow all origins for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State management - track running workflows
active_workflows = {}  # workflow_id -> {"status": str, "result": dict, "scenario": str}


# Request models
class OnboardingRequest(BaseModel):
    employee_name: str
    email: str
    department: str
    role: str
    manager: str
    start_date: str


class MeetingRequest(BaseModel):
    transcript: str
    participants: list[str]


class SLARequest(BaseModel):
    request_id: str
    type: str
    requested_by: str
    approver: str
    submitted_at: str = "2026-03-27T09:00:00Z"
    sla_deadline: str = "2026-03-29T09:00:00Z"


# Endpoint 1: Serve frontend dashboard
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the frontend dashboard."""
    frontend_path = "frontend/index.html"
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        # Return a simple placeholder if frontend doesn't exist yet
        return HTMLResponse(content="""
        <html>
            <head><title>WorkflowPilot</title></head>
            <body>
                <h1>WorkflowPilot API</h1>
                <p>Multi-Agent Enterprise Workflow System</p>
                <p>Frontend dashboard coming soon. Use API endpoints directly:</p>
                <ul>
                    <li>POST /api/workflow/onboarding</li>
                    <li>POST /api/workflow/meeting</li>
                    <li>POST /api/workflow/sla</li>
                    <li>POST /api/demo/run-all</li>
                    <li>GET /api/audit</li>
                </ul>
            </body>
        </html>
        """)


# Endpoint 2: Trigger onboarding workflow
@app.post("/api/workflow/onboarding")
async def trigger_onboarding(request: OnboardingRequest, background_tasks: BackgroundTasks):
    """Trigger an employee onboarding workflow."""
    workflow_id = str(uuid4())

    # Prepare employee data
    employee_data = {
        "name": request.employee_name,
        "email": request.email,
        "department": request.department,
        "role": request.role,
        "manager": request.manager,
        "start_date": request.start_date
    }

    # Initialize workflow tracking
    active_workflows[workflow_id] = {
        "status": "starting",
        "result": None,
        "scenario": "onboarding"
    }

    # Background task to run workflow
    async def _run_onboarding():
        try:
            active_workflows[workflow_id]["status"] = "running"
            result = await run_workflow("onboarding", employee=employee_data)
            active_workflows[workflow_id] = {
                "status": "completed",
                "result": result,
                "scenario": "onboarding"
            }
        except Exception as e:
            active_workflows[workflow_id] = {
                "status": "failed",
                "result": {"error": str(e)},
                "scenario": "onboarding"
            }

    background_tasks.add_task(_run_onboarding)

    return {
        "workflow_id": workflow_id,
        "status": "started",
        "scenario": "onboarding"
    }


# Endpoint 3: Trigger meeting workflow
@app.post("/api/workflow/meeting")
async def trigger_meeting(request: MeetingRequest, background_tasks: BackgroundTasks):
    """Trigger a meeting-to-action workflow."""
    workflow_id = str(uuid4())

    # Initialize workflow tracking
    active_workflows[workflow_id] = {
        "status": "starting",
        "result": None,
        "scenario": "meeting"
    }

    # Background task to run workflow
    async def _run_meeting():
        try:
            active_workflows[workflow_id]["status"] = "running"
            result = await run_workflow(
                "meeting",
                transcript=request.transcript,
                participants=request.participants
            )
            active_workflows[workflow_id] = {
                "status": "completed",
                "result": result,
                "scenario": "meeting"
            }
        except Exception as e:
            active_workflows[workflow_id] = {
                "status": "failed",
                "result": {"error": str(e)},
                "scenario": "meeting"
            }

    background_tasks.add_task(_run_meeting)

    return {
        "workflow_id": workflow_id,
        "status": "started",
        "scenario": "meeting"
    }


# Endpoint 4: Trigger SLA workflow
@app.post("/api/workflow/sla")
async def trigger_sla(request: SLARequest, background_tasks: BackgroundTasks):
    """Trigger an SLA breach prevention workflow."""
    workflow_id = str(uuid4())

    # Prepare approval data
    approval_data = {
        "request_id": request.request_id,
        "type": request.type,
        "requested_by": request.requested_by,
        "approver": request.approver,
        "submitted_at": request.submitted_at,
        "sla_deadline": request.sla_deadline
    }

    # Initialize workflow tracking
    active_workflows[workflow_id] = {
        "status": "starting",
        "result": None,
        "scenario": "sla"
    }

    # Background task to run workflow
    async def _run_sla():
        try:
            active_workflows[workflow_id]["status"] = "running"
            result = await run_workflow("sla", approval=approval_data)
            active_workflows[workflow_id] = {
                "status": "completed",
                "result": result,
                "scenario": "sla"
            }
        except Exception as e:
            active_workflows[workflow_id] = {
                "status": "failed",
                "result": {"error": str(e)},
                "scenario": "sla"
            }

    background_tasks.add_task(_run_sla)

    return {
        "workflow_id": workflow_id,
        "status": "started",
        "scenario": "sla"
    }


# Endpoint 5: Get workflow status
@app.get("/api/workflow/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get the current status and result of a workflow."""
    if workflow_id not in active_workflows:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return active_workflows[workflow_id]


# Endpoint 6: Get audit trail
@app.get("/api/audit")
async def get_audit_trail(scenario: str = None):
    """Get the full audit trail, optionally filtered by scenario."""
    entries = audit_logger.get_trail(scenario=scenario)
    summary = audit_logger.get_summary()

    return {
        "entries": entries,
        "summary": summary
    }


# Endpoint 7: Get audit summary
@app.get("/api/audit/summary")
async def get_audit_summary():
    """Get audit trail summary statistics."""
    return audit_logger.get_summary()


# Endpoint 8: Reset system
@app.post("/api/reset")
async def reset_system():
    """Reset everything for a new demo run."""
    # Clear audit trail
    audit_logger.clear()

    # Clear active workflows
    active_workflows.clear()

    # Reset error injection counters
    reset_error_injection()

    return {
        "status": "reset",
        "message": "System ready for new demo"
    }


# Endpoint 9: Run all demo scenarios
@app.post("/api/demo/run-all")
async def run_all_demos(background_tasks: BackgroundTasks):
    """Convenience endpoint: runs ALL 3 scenarios sequentially using sample data."""
    workflow_ids = []

    # Generate workflow IDs
    onboarding_id = str(uuid4())
    meeting_id = str(uuid4())
    sla_id = str(uuid4())

    # Initialize all workflows
    active_workflows[onboarding_id] = {
        "status": "starting",
        "result": None,
        "scenario": "onboarding"
    }
    active_workflows[meeting_id] = {
        "status": "starting",
        "result": None,
        "scenario": "meeting"
    }
    active_workflows[sla_id] = {
        "status": "starting",
        "result": None,
        "scenario": "sla"
    }

    # Background task to run all workflows sequentially
    async def _run_all_demos():
        try:
            # 1. Onboarding
            active_workflows[onboarding_id]["status"] = "running"
            onboarding_result = await run_workflow("onboarding", employee=SAMPLE_EMPLOYEE)
            active_workflows[onboarding_id] = {
                "status": "completed",
                "result": onboarding_result,
                "scenario": "onboarding"
            }

            # 2. Meeting
            active_workflows[meeting_id]["status"] = "running"
            meeting_result = await run_workflow(
                "meeting",
                transcript=SAMPLE_TRANSCRIPT,
                participants=SAMPLE_PARTICIPANTS
            )
            active_workflows[meeting_id] = {
                "status": "completed",
                "result": meeting_result,
                "scenario": "meeting"
            }

            # 3. SLA
            active_workflows[sla_id]["status"] = "running"
            sla_result = await run_workflow("sla", approval=SAMPLE_APPROVAL)
            active_workflows[sla_id] = {
                "status": "completed",
                "result": sla_result,
                "scenario": "sla"
            }

        except Exception as e:
            # Mark any incomplete workflows as failed
            for wf_id in [onboarding_id, meeting_id, sla_id]:
                if active_workflows[wf_id]["status"] != "completed":
                    active_workflows[wf_id] = {
                        "status": "failed",
                        "result": {"error": str(e)},
                        "scenario": active_workflows[wf_id]["scenario"]
                    }

    background_tasks.add_task(_run_all_demos)

    return {
        "message": "Running all demo scenarios",
        "workflow_ids": {
            "onboarding": onboarding_id,
            "meeting": meeting_id,
            "sla": sla_id
        },
        "status": "started"
    }


# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "WorkflowPilot",
        "version": "1.0.0"
    }


# Server startup
if __name__ == "__main__":
    uvicorn.run(
        "api:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
