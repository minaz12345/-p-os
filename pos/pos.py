#!/usr/bin/env python3
"""
P-OS Constitutional CLI - Phase 1 Unified Wrapper
Governance-first orchestration layer for operational transparency.

Usage:
    pos validate <file> [--strict] [--dry-run] [--verbose]
    pos status [--dry-run] [--verbose]
    pos flags [--dry-run] [--verbose]

Philosophy:
    - No hidden logic or black-box automation
    - Full audit trail with correlation IDs
    - Deterministic replayability
    - Manual override always available
    - Transparency over convenience
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import typer
from rich.console import Console
from rich.panel import Panel
from datetime import datetime

from pos.core.correlation import generate_correlation_id
from pos.core.audit_logger import AuditLogger
from pos.commands.validate import validate as validate_cmd
from pos.commands.status import status as status_cmd
from pos.commands.flags import flags as flags_cmd

app = typer.Typer(
    name="pos",
    help="P-OS Constitutional CLI - Governance-first operations interface",
    add_completion=False,
)

console = Console()

# Initialize audit logger
audit_logger = AuditLogger(log_dir=project_root / "logs" / "cli_audit")


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show underlying commands and detailed execution info"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Show what would be executed without running it"),
):
    """
    P-OS Constitutional CLI v7.5
    
    A governance-first orchestration layer that provides unified access
    to P-OS operational procedures while maintaining full transparency
    and forensic traceability.
    
    Every command generates:
    - Correlation ID for tracking
    - Complete audit trail in logs/cli_audit/
    - Transparent display of underlying scripts
    - Deterministic output for replayability
    """
    # Store global flags in context for subcommands
    ctx.obj = {
        "verbose": verbose,
        "dry_run": dry_run,
        "correlation_id": generate_correlation_id(),
        "start_time": datetime.utcnow(),
    }


@app.command()
def validate(
    ctx: typer.Context,
    path: str = typer.Argument(..., help="Path to document or directory to validate"),
    strict: bool = typer.Option(False, "--strict", help="Enable strict validation mode (warnings become errors)"),
    verbose: bool = typer.Option(None, "--verbose", "-v", help="Show underlying commands (overrides global)"),
    dry_run: bool = typer.Option(None, "--dry-run", "-n", help="Preview without executing (overrides global)"),
):
    """
    Validate documents against P-OS Executable Markdown Level 5 standards.
    
    Checks constitutional compliance (R6) and forensic integrity (R3).
    
    Examples:
        pos validate docs/file.md
        pos validate docs/ --strict
        pos validate docs/file.md --dry-run --verbose
    """
    config = ctx.obj
    # Use command-level flags if provided, otherwise use global flags
    verbose = verbose if verbose is not None else config["verbose"]
    dry_run = dry_run if dry_run is not None else config["dry_run"]
    correlation_id = config["correlation_id"]
    
    # Log command intent
    audit_logger.log_command_start(
        correlation_id=correlation_id,
        command="validate",
        arguments={"path": path, "strict": strict},
        dry_run=dry_run,
        verbose=verbose,
    )
    
    if verbose:
        console.print(Panel(
            f"[bold cyan]Underlying Command:[/bold cyan]\n"
            f"python scripts/validate_docs.py {path}{' --strict' if strict else ''}\n\n"
            f"[bold cyan]Correlation ID:[/bold cyan]\n{correlation_id}\n\n"
            f"[bold cyan]Audit Log:[/bold cyan]\n{audit_logger.get_log_path(correlation_id)}",
            title="🔍 VALIDATION PLAN",
            border_style="cyan",
        ))
    
    if dry_run:
        console.print("[yellow]⚠️  DRY RUN MODE - No validation performed[/yellow]")
        console.print(f"[green]✓ Would execute:[/green] python scripts/validate_docs.py {path}{' --strict' if strict else ''}")
        audit_logger.log_dry_run(correlation_id=correlation_id, command="validate")
        return
    
    # Execute validation
    try:
        result = validate_cmd(path=path, strict=strict, correlation_id=correlation_id)
        
        duration_ms = (datetime.utcnow() - config["start_time"]).total_seconds() * 1000
        
        audit_logger.log_command_complete(
            correlation_id=correlation_id,
            exit_code=0 if result else 1,
            duration_ms=duration_ms,
        )
        
        if result:
            console.print("[green]✓ Validation completed successfully[/green]")
        else:
            console.print("[red]✗ Validation failed - check errors above[/red]")
            sys.exit(1)
            
    except Exception as e:
        duration_ms = (datetime.utcnow() - config["start_time"]).total_seconds() * 1000
        audit_logger.log_command_error(
            correlation_id=correlation_id,
            error=str(e),
            duration_ms=duration_ms,
        )
        console.print(f"[red]✗ Validation error: {e}[/red]")
        sys.exit(1)


@app.command()
def status(
    ctx: typer.Context,
    verbose: bool = typer.Option(None, "--verbose", "-v", help="Show underlying commands (overrides global)"),
    dry_run: bool = typer.Option(None, "--dry-run", "-n", help="Preview without executing (overrides global)"),
):
    """
    Display current P-OS runtime status and health.
    
    Shows constitutional state, active flags, system health,
    and operational readiness.
    
    Examples:
        pos status
        pos status --dry-run --verbose
    """
    config = ctx.obj
    # Use command-level flags if provided, otherwise use global flags
    verbose = verbose if verbose is not None else config["verbose"]
    dry_run = dry_run if dry_run is not None else config["dry_run"]
    correlation_id = config["correlation_id"]
    
    # Log command intent
    audit_logger.log_command_start(
        correlation_id=correlation_id,
        command="status",
        arguments={},
        dry_run=dry_run,
        verbose=verbose,
    )
    
    if verbose:
        console.print(Panel(
            f"[bold cyan]Underlying Commands:[/bold cyan]\n"
            f"1. Check runtime/constitutional_state.json\n"
            f"2. Verify service health endpoints\n"
            f"3. Inspect active W11 flags\n\n"
            f"[bold cyan]Correlation ID:[/bold cyan]\n{correlation_id}\n\n"
            f"[bold cyan]Audit Log:[/bold cyan]\n{audit_logger.get_log_path(correlation_id)}",
            title="📊 STATUS CHECK PLAN",
            border_style="cyan",
        ))
    
    if dry_run:
        console.print("[yellow]⚠️  DRY RUN MODE - No status check performed[/yellow]")
        console.print("[green]✓ Would check:[/green] constitutional state, service health, W11 flags")
        audit_logger.log_dry_run(correlation_id=correlation_id, command="status")
        return
    
    # Execute status check
    try:
        result = status_cmd(correlation_id=correlation_id)
        
        duration_ms = (datetime.utcnow() - config["start_time"]).total_seconds() * 1000
        
        audit_logger.log_command_complete(
            correlation_id=correlation_id,
            exit_code=0 if result else 1,
            duration_ms=duration_ms,
        )
        
        if result:
            console.print("[green]✓ Status check completed[/green]")
        else:
            console.print("[yellow]⚠ Status check completed with warnings[/yellow]")
            
    except Exception as e:
        duration_ms = (datetime.utcnow() - config["start_time"]).total_seconds() * 1000
        audit_logger.log_command_error(
            correlation_id=correlation_id,
            error=str(e),
            duration_ms=duration_ms,
        )
        console.print(f"[red]✗ Status check error: {e}[/red]")
        sys.exit(1)


@app.command()
def flags(
    ctx: typer.Context,
    verbose: bool = typer.Option(None, "--verbose", "-v", help="Show underlying commands (overrides global)"),
    dry_run: bool = typer.Option(None, "--dry-run", "-n", help="Preview without executing (overrides global)"),
):
    """
    Display and manage P-OS operational flags.
    
    Shows current W11 enforcement flags, constitutional constraints,
    and runtime configuration states.
    
    Examples:
        pos flags
        pos flags --dry-run --verbose
    """
    config = ctx.obj
    # Use command-level flags if provided, otherwise use global flags
    verbose = verbose if verbose is not None else config["verbose"]
    dry_run = dry_run if dry_run is not None else config["dry_run"]
    correlation_id = config["correlation_id"]
    
    # Log command intent
    audit_logger.log_command_start(
        correlation_id=correlation_id,
        command="flags",
        arguments={},
        dry_run=dry_run,
        verbose=verbose,
    )
    
    if verbose:
        console.print(Panel(
            f"[bold cyan]Operation:[/bold cyan]\n"
            f"Inspect runtime flags and W11 enforcement state\n\n"
            f"[bold cyan]Correlation ID:[/bold cyan]\n{correlation_id}\n\n"
            f"[bold cyan]Audit Log:[/bold cyan]\n{audit_logger.get_log_path(correlation_id)}",
            title="🚩 FLAGS INSPECTION PLAN",
            border_style="cyan",
        ))
    
    if dry_run:
        console.print("[yellow]⚠️  DRY RUN MODE - No flag inspection performed[/yellow]")
        console.print("[green]✓ Would inspect:[/green] W11 flags, constitutional constraints, runtime state")
        audit_logger.log_dry_run(correlation_id=correlation_id, command="flags")
        return
    
    # Execute flags inspection
    try:
        result = flags_cmd(correlation_id=correlation_id)
        
        duration_ms = (datetime.utcnow() - config["start_time"]).total_seconds() * 1000
        
        audit_logger.log_command_complete(
            correlation_id=correlation_id,
            exit_code=0 if result else 1,
            duration_ms=duration_ms,
        )
        
        if result:
            console.print("[green]✓ Flags inspection completed[/green]")
        else:
            console.print("[yellow]⚠ Flags inspection completed with warnings[/yellow]")
            
    except Exception as e:
        duration_ms = (datetime.utcnow() - config["start_time"]).total_seconds() * 1000
        audit_logger.log_command_error(
            correlation_id=correlation_id,
            error=str(e),
            duration_ms=duration_ms,
        )
        console.print(f"[red]✗ Flags inspection error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
