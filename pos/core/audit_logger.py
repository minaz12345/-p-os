"""
P-OS CLI Core - Audit Logger

Provides structured audit logging for all CLI operations.
Ensures forensic traceability and constitutional compliance (R3).

Every operation generates a complete audit trail including:
- Timestamp (UTC ISO 8601)
- Correlation ID
- Operator identity
- Command executed
- Underlying script invoked
- Arguments passed
- Exit code
- Duration
- Environment snapshot
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class AuditLogger:
    """
    Structured audit logger for P-OS CLI operations.
    
    All logs are written to logs/cli_audit/ in JSON format
    for machine parsing and forensic analysis.
    """
    
    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory for audit logs. Defaults to project_root/logs/cli_audit/
        """
        if log_dir is None:
            # Default to project root
            project_root = Path(__file__).parent.parent.parent
            log_dir = project_root / "logs" / "cli_audit"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def get_log_path(self, correlation_id: str) -> Path:
        """
        Get the full path for a correlation ID's audit log.
        
        Args:
            correlation_id: The correlation ID for the operation
            
        Returns:
            Path: Full path to the audit log file
        """
        return self.log_dir / f"{correlation_id}.json"
    
    def _get_environment_snapshot(self) -> Dict[str, str]:
        """
        Capture relevant environment variables for audit trail.
        
        Returns:
            dict: Snapshot of relevant environment variables
        """
        relevant_vars = [
            "USER",
            "USERNAME",
            "HOME",
            "PATH",
            "PYTHONPATH",
            "POS_ENV",
            "POS_DEBUG",
        ]
        
        snapshot = {}
        for var in relevant_vars:
            value = os.environ.get(var)
            if value:
                # Mask sensitive values
                if any(keyword in var.lower() for keyword in ["password", "secret", "key", "token"]):
                    snapshot[var] = "***MASKED***"
                else:
                    snapshot[var] = value
        
        return snapshot
    
    def log_command_start(
        self,
        correlation_id: str,
        command: str,
        arguments: Dict[str, Any],
        dry_run: bool = False,
        verbose: bool = False,
    ) -> None:
        """
        Log the start of a CLI command execution.
        
        Args:
            correlation_id: Unique correlation ID for tracking
            command: Command name (e.g., 'validate', 'status')
            arguments: Command arguments as dictionary
            dry_run: Whether this is a dry run
            verbose: Whether verbose mode is enabled
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        audit_entry = {
            "event": "COMMAND_START",
            "timestamp": timestamp,
            "correlation_id": correlation_id,
            "command": command,
            "arguments": arguments,
            "dry_run": dry_run,
            "verbose": verbose,
            "operator": os.environ.get("USER") or os.environ.get("USERNAME") or "unknown",
            "python_version": sys.version,
            "platform": sys.platform,
            "environment_snapshot": self._get_environment_snapshot(),
        }
        
        log_path = self.get_log_path(correlation_id)
        
        # Write initial log entry
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(audit_entry, f, indent=2, ensure_ascii=False)
    
    def log_dry_run(self, correlation_id: str, command: str) -> None:
        """
        Log a dry-run execution (no actual operation performed).
        
        Args:
            correlation_id: Unique correlation ID for tracking
            command: Command name
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        log_path = self.get_log_path(correlation_id)
        
        # Read existing log
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)
        else:
            audit_data = {}
        
        # Add dry-run event
        audit_data["dry_run_executed"] = True
        audit_data["dry_run_timestamp"] = timestamp
        
        # Write updated log
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)
    
    def log_command_complete(
        self,
        correlation_id: str,
        exit_code: int,
        duration_ms: float,
    ) -> None:
        """
        Log successful completion of a CLI command.
        
        Args:
            correlation_id: Unique correlation ID for tracking
            exit_code: Command exit code (0 = success)
            duration_ms: Execution duration in milliseconds
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        log_path = self.get_log_path(correlation_id)
        
        # Read existing log
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)
        else:
            audit_data = {}
        
        # Add completion event
        audit_data["event"] = "COMMAND_COMPLETE"
        audit_data["completion_timestamp"] = timestamp
        audit_data["exit_code"] = exit_code
        audit_data["duration_ms"] = round(duration_ms, 2)
        audit_data["status"] = "success" if exit_code == 0 else "failure"
        
        # Write updated log
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)
    
    def log_command_error(
        self,
        correlation_id: str,
        error: str,
        duration_ms: float,
    ) -> None:
        """
        Log error during CLI command execution.
        
        Args:
            correlation_id: Unique correlation ID for tracking
            error: Error message
            duration_ms: Execution duration before error in milliseconds
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        log_path = self.get_log_path(correlation_id)
        
        # Read existing log
        if log_path.exists():
            with open(log_path, 'r', encoding='utf-8') as f:
                audit_data = json.load(f)
        else:
            audit_data = {}
        
        # Add error event
        audit_data["event"] = "COMMAND_ERROR"
        audit_data["error_timestamp"] = timestamp
        audit_data["error_message"] = error
        audit_data["duration_ms"] = round(duration_ms, 2)
        audit_data["status"] = "error"
        
        # Write updated log
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=2, ensure_ascii=False)
    
    def get_audit_trail(self, correlation_id: str) -> Optional[Dict]:
        """
        Retrieve the complete audit trail for a correlation ID.
        
        Args:
            correlation_id: Unique correlation ID for tracking
            
        Returns:
            dict: Complete audit trail, or None if not found
        """
        log_path = self.get_log_path(correlation_id)
        
        if not log_path.exists():
            return None
        
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
