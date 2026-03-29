import json
from pathlib import Path
from typing import Optional
from models import AuditEntry
from config import settings


class AuditLogger:
    """Audit trail logging system for multi-agent workflow system."""

    def __init__(self, log_path: Optional[str] = None):
        """
        Initialize the audit logger.

        Args:
            log_path: Path to the audit log file (defaults to settings.audit_log_path)
        """
        self.log_path = Path(log_path or settings.audit_log_path)
        self.entries: list[dict] = []

        # Create the log file if it doesn't exist
        if not self.log_path.exists():
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            self.log_path.touch()

    def log(
        self,
        scenario: str,
        agent: str,
        action: str,
        input_data: dict,
        output_data: dict,
        decision_reasoning: str,
        model_used: str = "none",
        tokens_used: int = 0,
        duration_ms: float = 0,
        error: Optional[str] = None,
        status: str = "success"
    ) -> dict:
        """
        Log an audit entry.

        Args:
            scenario: Workflow scenario (onboarding, meeting, sla)
            agent: Name of the agent performing the action
            action: Description of the action taken
            input_data: Data received by the agent
            output_data: Data produced by the agent
            decision_reasoning: Why the agent made this decision
            model_used: LLM model used (if any)
            tokens_used: Approximate token count
            duration_ms: Duration in milliseconds
            error: Error message if any
            status: Status of the action (success, failure, retry, escalated)

        Returns:
            The audit entry as a dict for LangGraph state
        """
        # Create audit entry with auto-generated UUID and timestamp
        entry = AuditEntry(
            scenario=scenario,
            agent=agent,
            action=action,
            input_data=input_data,
            output_data=output_data,
            decision_reasoning=decision_reasoning,
            model_used=model_used,
            tokens_used=tokens_used,
            duration_ms=duration_ms,
            error=error,
            status=status
        )

        # Convert to dict
        entry_dict = entry.model_dump()

        # Append to in-memory list
        self.entries.append(entry_dict)

        # Append to log file as JSON line
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry_dict, ensure_ascii=False) + '\n')

        return entry_dict

    def get_trail(self, scenario: Optional[str] = None) -> list[dict]:
        """
        Get audit trail entries.

        Args:
            scenario: Optional filter by scenario

        Returns:
            List of audit entries (filtered if scenario is provided)
        """
        if scenario:
            return [entry for entry in self.entries if entry['scenario'] == scenario]
        return self.entries.copy()

    def get_summary(self) -> dict:
        """
        Get a summary of audit trail statistics.

        Returns:
            Dictionary with summary statistics
        """
        if not self.entries:
            return {
                "total_actions": 0,
                "actions_by_scenario": {},
                "actions_by_agent": {},
                "error_count": 0,
                "total_tokens": 0,
                "models_used": {}
            }

        actions_by_scenario = {}
        actions_by_agent = {}
        models_used = {}
        error_count = 0
        total_tokens = 0

        for entry in self.entries:
            # Count by scenario
            scenario = entry['scenario']
            actions_by_scenario[scenario] = actions_by_scenario.get(scenario, 0) + 1

            # Count by agent
            agent = entry['agent']
            actions_by_agent[agent] = actions_by_agent.get(agent, 0) + 1

            # Count models used
            model = entry.get('model_used', 'none')
            models_used[model] = models_used.get(model, 0) + 1

            # Count errors
            if entry.get('error') or entry.get('status') in ['failure', 'retry', 'escalated']:
                error_count += 1

            # Sum tokens
            total_tokens += entry.get('tokens_used', 0)

        return {
            "total_actions": len(self.entries),
            "actions_by_scenario": actions_by_scenario,
            "actions_by_agent": actions_by_agent,
            "error_count": error_count,
            "total_tokens": total_tokens,
            "models_used": models_used
        }

    def clear(self):
        """Clear the audit trail (in-memory and file)."""
        self.entries = []
        # Truncate the log file
        with open(self.log_path, 'w', encoding='utf-8') as f:
            f.truncate()


# Module-level singleton
audit_logger = AuditLogger()
