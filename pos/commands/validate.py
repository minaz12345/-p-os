"""
P-OS CLI Commands - Validate

Wraps the existing scripts/validate_docs.py with audit logging
and correlation ID tracking.

Maintains full transparency by showing the underlying command
being executed.
"""

import subprocess
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel

console = Console()


def validate(path: str, strict: bool = False, correlation_id: Optional[str] = None) -> bool:
    """
    Execute document validation using the existing validator script.
    
    This is a thin wrapper around scripts/validate_docs.py that adds:
    - Correlation ID tracking
    - Audit logging
    - Structured output
    
    Args:
        path: Path to document or directory to validate
        strict: Enable strict validation mode
        correlation_id: Correlation ID for audit trail
        
    Returns:
        bool: True if validation passed, False otherwise
    """
    project_root = Path(__file__).parent.parent.parent
    validator_script = project_root / "scripts" / "validate_docs.py"
    
    if not validator_script.exists():
        console.print(f"[red]✗ Validator script not found: {validator_script}[/red]")
        return False
    
    # Build command
    cmd = [sys.executable, str(validator_script), path]
    if strict:
        cmd.append("--strict")
    
    console.print(f"[cyan]Executing:[/cyan] {' '.join(cmd)}")
    if correlation_id:
        console.print(f"[cyan]Correlation ID:[/cyan] {correlation_id}")
    console.print()
    
    # Execute validation
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False,  # Show output directly to user
            text=True,
        )
        
        success = result.returncode == 0
        
        if success:
            console.print("\n[green]✓ Validation completed successfully[/green]")
        else:
            console.print(f"\n[red]✗ Validation failed (exit code: {result.returncode})[/red]")
        
        return success
        
    except FileNotFoundError:
        console.print(f"[red]✗ Python interpreter not found: {sys.executable}[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Validation error: {e}[/red]")
        return False
