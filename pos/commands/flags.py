"""
P-OS CLI Commands - Flags

Displays and manages P-OS operational flags.
Shows current W11 enforcement flags, constitutional constraints,
and runtime configuration states.

This is a read-only operation that inspects flag states.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def check_w11_flag_files() -> List[Dict]:
    """
    Check actual W11 flag files in flags/ directory.
    This is the authoritative source of W11 state.
    """
    project_root = Path(__file__).parent.parent.parent
    flags_dir = project_root / "flags"

    if not flags_dir.exists():
        return []

    active_flags = []
    for flag_file in sorted(flags_dir.glob("*.flag")):
        try:
            content = flag_file.read_text(encoding="utf-8")
            active_flags.append({
                "name": flag_file.name,
                "content": content.strip(),
                "modified": datetime.fromtimestamp(
                    flag_file.stat().st_mtime
                ).isoformat(),
            })
        except Exception:
            active_flags.append({
                "name": flag_file.name,
                "content": "(unreadable)",
                "modified": "unknown",
            })

    return active_flags


def load_w11_enforcement_contract() -> Dict:
    """
    Load the W11 enforcement contract configuration.
    
    Returns:
        dict: W11 enforcement contract data
    """
    project_root = Path(__file__).parent.parent.parent
    contract_file = project_root / ".lingma" / "contracts" / "w11_enforcement_contract.yaml"
    
    if not contract_file.exists():
        return {
            "status": "NOT_FOUND",
            "message": f"W11 contract not found: {contract_file}",
        }
    
    try:
        # For YAML files, we'll read as text and show basic info
        # In production, you'd use PyYAML to parse properly
        with open(contract_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "status": "OK",
            "file_size": len(content),
            "preview": content[:500] + "..." if len(content) > 500 else content,
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to read W11 contract: {e}",
        }


def check_constitutional_constraints() -> List[Dict]:
    """
    Check active constitutional constraints from runtime state.
    
    Returns:
        list: List of active constraints
    """
    project_root = Path(__file__).parent.parent.parent
    state_file = project_root / "runtime" / "constitutional_state.json"
    
    if not state_file.exists():
        return []
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # Extract constraint-related information
        constraints = []
        
        # Check for various constraint indicators
        if "enforcement_mode" in state:
            constraints.append({
                "name": "Enforcement Mode",
                "value": state["enforcement_mode"],
                "status": "ACTIVE",
            })
        
        if "w11_enabled" in state:
            constraints.append({
                "name": "W11 Rules",
                "value": "Enabled" if state["w11_enabled"] else "Disabled",
                "status": "ACTIVE" if state["w11_enabled"] else "INACTIVE",
            })
        
        if "audit_required" in state:
            constraints.append({
                "name": "Audit Requirement",
                "value": "Required" if state["audit_required"] else "Optional",
                "status": "ACTIVE" if state["audit_required"] else "INACTIVE",
            })
        
        return constraints
        
    except Exception as e:
        console.print(f"[yellow]⚠ Warning: Failed to parse constitutional state: {e}[/yellow]")
        return []


def inspect_runtime_flags() -> Dict:
    """
    Inspect runtime guard log for active flags.
    
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
        with open(guard_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Look for flag-related entries
        flag_entries = []
        for line in lines[-50:]:  # Check last 50 lines
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in ["flag", "enforcement", "constraint", "w11"]):
                flag_entries.append(line.strip())
        
        return {
            "status": "OK",
            "flag_entries": flag_entries[-10:],  # Return last 10 relevant entries
            "total_lines": len(lines),
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to read runtime guard log: {e}",
        }


def flags(correlation_id: Optional[str] = None) -> bool:
    """
    Display comprehensive P-OS operational flags and constraints.
    
    Shows:
    - W11 enforcement contract status
    - Active constitutional constraints
    - Runtime flag states
    
    Args:
        correlation_id: Correlation ID for audit trail
        
    Returns:
        bool: True if flags inspection completed successfully
    """
    console.print(Panel(
        "[bold cyan]P-OS Operational Flags Inspection[/bold cyan]\n"
        f"Timestamp: {datetime.utcnow().isoformat()}Z\n"
        f"Correlation ID: {correlation_id or 'N/A'}",
        title="🚩 FLAGS",
        border_style="cyan",
    ))
    console.print()
    
    # SEKCJA 1: Rzeczywiste flagi W11 z katalogu flags/
    console.print("[bold]W11 Flag Files (flags/*.flag):[/bold]")
    w11_files = check_w11_flag_files()

    if w11_files:
        console.print(f"  [red]🚨 SYSTEM DEGRADED — {len(w11_files)} aktywna flaga[/red]")
        for flag in w11_files:
            console.print(f"\n  [red]● {flag['name']}[/red]")
            console.print(f"    Modified: {flag['modified']}")
            for line in flag['content'].split('\n'):
                console.print(f"    {line}")
    else:
        console.print("  [green]✓ Brak aktywnych flag — system HEALTHY[/green]")
    console.print()
    
    # Check W11 enforcement contract
    console.print("[bold]W11 Enforcement Contract:[/bold]")
    w11_contract = load_w11_enforcement_contract()
    
    if w11_contract["status"] == "OK":
        console.print(f"  Status: [green]✓ Found[/green]")
        console.print(f"  File Size: {w11_contract['file_size']} bytes")
        console.print()
        console.print("  Preview:")
        for line in w11_contract["preview"].split('\n')[:10]:
            console.print(f"    {line}")
    else:
        console.print(f"  Status: [yellow]⚠ {w11_contract.get('message', 'Unknown')}[/yellow]")
    
    console.print()
    
    # Check constitutional constraints
    console.print("[bold]Active Constitutional Constraints:[/bold]")
    constraints = check_constitutional_constraints()
    
    if constraints:
        table = Table(show_header=True, box=None)
        table.add_column("Constraint", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")
        
        for constraint in constraints:
            table.add_row(
                constraint["name"],
                constraint["value"],
                f"[{'green' if constraint['status'] == 'ACTIVE' else 'yellow'}]{constraint['status']}[/]",
            )
        
        console.print(table)
    else:
        console.print("  [yellow]⚠ No active constraints found or unable to read state[/yellow]")
    
    console.print()
    
    # Inspect runtime flags
    console.print("[bold]Runtime Flag Activity (Recent):[/bold]")
    runtime_flags = inspect_runtime_flags()
    
    if runtime_flags["status"] == "OK":
        if runtime_flags["flag_entries"]:
            for entry in runtime_flags["flag_entries"]:
                console.print(f"  {entry}")
        else:
            console.print("  No recent flag activity detected")
        console.print(f"\n  [dim]Total log entries: {runtime_flags['total_lines']}[/dim]")
    else:
        console.print(f"  [yellow]⚠ {runtime_flags.get('message', 'Unknown error')}[/yellow]")
    
    console.print()
    console.print("[green]✓ Flags inspection completed[/green]")
    
    return True
