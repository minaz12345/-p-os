"""
P-OS CLI Commands - Status

Displays current P-OS runtime status and health.
Checks constitutional state, service health, and operational readiness.

This is a read-only operation that aggregates status from multiple sources.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_constitutional_state() -> Dict:
    """
    Check the constitutional state from runtime configuration.
    
    Returns:
        dict: Constitutional state information
    """
    project_root = Path(__file__).parent.parent.parent
    state_file = project_root / "runtime" / "constitutional_state.json"
    
    if not state_file.exists():
        return {
            "status": "NOT_FOUND",
            "message": f"Constitutional state file not found: {state_file}",
        }
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        return {
            "status": "OK",
            "data": state,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to read constitutional state: {e}",
        }


def check_runtime_flags() -> Dict:
    """
    Check current runtime flags and W11 enforcement status.
    
    Returns:
        dict: Runtime flags information
    """
    project_root = Path(__file__).parent.parent.parent
    guard_log = project_root / "runtime" / "runtime_guard.log"
    
    if not guard_log.exists():
        return {
            "status": "NOT_FOUND",
            "message": f"Runtime guard log not found: {guard_log}",
        }
    
    try:
        # Read last 10 lines of guard log
        with open(guard_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-10:] if len(lines) > 10 else lines
        
        return {
            "status": "OK",
            "recent_entries": [line.strip() for line in recent_lines],
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to read runtime guard log: {e}",
        }


def check_system_health() -> Dict:
    """
    Check basic system health metrics.
    
    Returns:
        dict: System health information
    """
    try:
        import psutil
        
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "OK",
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "disk_percent": disk.percent,
        }
    except ImportError:
        return {
            "status": "WARNING",
            "message": "psutil not available - install with: pip install psutil",
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to check system health: {e}",
        }


def status(correlation_id: Optional[str] = None) -> bool:
    """
    Display comprehensive P-OS runtime status.
    
    Aggregates status from:
    - Constitutional state
    - Runtime flags
    - System health
    
    Args:
        correlation_id: Correlation ID for audit trail
        
    Returns:
        bool: True if status check completed successfully
    """
    console.print(Panel(
        "[bold cyan]P-OS Runtime Status Check[/bold cyan]\n"
        f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
        f"Correlation ID: {correlation_id or 'N/A'}",
        title="📊 STATUS",
        border_style="cyan",
    ))
    console.print()
    
    # Check constitutional state
    console.print("[bold]Constitutional State:[/bold]")
    const_state = check_constitutional_state()
    
    if const_state["status"] == "OK":
        data = const_state["data"]
        table = Table(show_header=False, box=None)
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            if isinstance(value, dict):
                table.add_row(key, json.dumps(value, indent=2))
            else:
                table.add_row(str(key), str(value))
        
        console.print(table)
    else:
        console.print(f"[yellow]⚠ {const_state.get('message', 'Unknown error')}[/yellow]")
    
    console.print()
    
    # Check runtime flags
    console.print("[bold]Runtime Flags (Recent):[/bold]")
    flags = check_runtime_flags()
    
    if flags["status"] == "OK":
        for entry in flags["recent_entries"]:
            console.print(f"  {entry}")
    else:
        console.print(f"[yellow]⚠ {flags.get('message', 'Unknown error')}[/yellow]")
    
    console.print()
    
    # Check system health
    console.print("[bold]System Health:[/bold]")
    health = check_system_health()
    
    if health["status"] == "OK":
        table = Table(show_header=False, box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("CPU Usage", f"{health['cpu_percent']}%")
        table.add_row("Memory Usage", f"{health['memory_percent']}%")
        table.add_row("Disk Usage", f"{health['disk_percent']}%")
        
        console.print(table)
    else:
        console.print(f"[yellow]⚠ {health.get('message', 'Unknown error')}[/yellow]")
    
    console.print()
    console.print("[green]✓ Status check completed[/green]")
    
    return True
