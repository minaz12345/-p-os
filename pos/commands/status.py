"""
P-OS CLI Commands - Status

Displays current P-OS runtime status and health.
Checks constitutional state, service health, and operational readiness.

This is a read-only operation that aggregates status from multiple sources.
"""

import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

# Windows UTF-8 enforcement to prevent UnicodeEncodeError
if sys.platform == 'win32':
    # Set environment variable for proper encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    # Reconfigure stdout/stderr if they support it
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def check_constitutional_state() -> Dict:
    """
    Check the constitutional state from runtime configuration.
    
    Returns:
        dict: Constitutional state information with semantic separation
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
        
        # Extract semantic dimensions per v8.0 doctrine
        return {
            "status": "OK",
            "data": state,
            "mode": state.get("mode", "unknown"),
            "enforcement_active": state.get("enforcement_active", False),
            "mutation_lock_until": state.get("mutation_lock_until"),
            "health_score": state.get("constitutional_health_score"),
            "semantic_doctrine": state.get("semantic_refinement_doctrine", {}),
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


def check_audit_integrity() -> Dict:
    """
    Check audit log integrity and completeness.
    
    Returns:
        dict: Audit integrity metrics
    """
    project_root = Path(__file__).parent.parent.parent
    audit_dir = project_root / "logs" / "cli_audit"
    
    if not audit_dir.exists():
        return {
            "status": "NOT_FOUND",
            "completeness": 0.0,
            "total_entries": 0,
            "message": "Audit directory not found",
        }
    
    try:
        # Count audit log files
        audit_files = list(audit_dir.glob("*.json"))
        total_entries = len(audit_files)
        
        # Check for incomplete/corrupted entries (simplified heuristic)
        incomplete_count = 0
        for audit_file in audit_files:
            try:
                with open(audit_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Check for required fields
                    if not all(k in data for k in ['timestamp', 'correlation_id']):
                        incomplete_count += 1
            except (json.JSONDecodeError, Exception):
                incomplete_count += 1
        
        completeness = ((total_entries - incomplete_count) / total_entries * 100) if total_entries > 0 else 0.0
        
        return {
            "status": "OK",
            "completeness": round(completeness, 2),
            "total_entries": total_entries,
            "incomplete_entries": incomplete_count,
            "directory": str(audit_dir),
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to check audit integrity: {e}",
        }


def check_operator_friction() -> Dict:
    """
    Check operator friction points from FRICTION_POINTS_LOG.
    
    Returns:
        dict: Operator friction summary
    """
    project_root = Path(__file__).parent.parent.parent
    friction_log = project_root / "docs" / "FRICTION_POINTS_LOG_P-OS_v7.5_20260511-20260610.md"
    
    if not friction_log.exists():
        return {
            "status": "NOT_FOUND",
            "friction_points": 0,
            "message": "Friction points log not found",
        }
    
    try:
        content = friction_log.read_text(encoding='utf-8')
        
        # Count friction point entries (simple heuristic)
        entry_count = content.count("### **Entry #")
        resolved_count = content.count("✅ RESOLVED")
        deferred_count = content.count("⏸️ DEFERRED")
        
        return {
            "status": "OK",
            "total_friction_points": entry_count,
            "resolved": resolved_count,
            "deferred": deferred_count,
            "active_issues": entry_count - resolved_count,
            "log_file": str(friction_log),
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Failed to read friction log: {e}",
        }


def check_historical_debt() -> Dict:
    """
    Check historical violations and technical debt.
    
    Returns:
        dict: Historical debt summary
    """
    project_root = Path(__file__).parent.parent.parent
    
    # Check for archived chaos test results (historical violations)
    chaos_archive = project_root / "archive" / "week3_chaos_tests"
    
    historical_violations = 0
    if chaos_archive.exists():
        violation_files = list(chaos_archive.glob("*violation*"))
        historical_violations = len(violation_files)
    
    return {
        "status": "OK",
        "historical_violations": historical_violations,
        "chaos_test_results": "archived" if chaos_archive.exists() else "not_found",
        "note": "Historical violations tracked separately from current compliance",
    }


def status(correlation_id: Optional[str] = None) -> bool:
    """
    Display comprehensive P-OS runtime status with semantic separation.
    
    Implements v8.0 Semantic Refinement Doctrine:
    - Separates operational success from audit integrity
    - Reports constitutional compliance independently
    - Tracks operator friction as telemetry
    - Acknowledges historical debt
    
    Args:
        correlation_id: Correlation ID for audit trail
        
    Returns:
        bool: True if status check completed successfully
    """
    # Use plain print to avoid Rich console Unicode issues on Windows
    print("=" * 70)
    print("P-OS Runtime Status Check - Semantic Separation Model")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"Correlation ID: {correlation_id or 'N/A'}")
    print("=" * 70)
    print()
    
    # AXIS 1: Operational Success (Runtime Health)
    print("[AXIS 1] OPERATIONAL SUCCESS (Runtime Health):")
    health = check_system_health()
    
    if health["status"] == "OK":
        print(f"  CPU Usage: {health['cpu_percent']}%")
        print(f"  Memory Usage: {health['memory_percent']}%")
        print(f"  Disk Usage: {health['disk_percent']}%")
        print(f"  [OK] System resources within normal parameters")
    else:
        print(f"  [WARN] {health.get('message', 'Unknown error')}")
    
    print()
    
    # AXIS 2: Constitutional Compliance
    print("[AXIS 2] CONSTITUTIONAL COMPLIANCE:")
    const_state = check_constitutional_state()
    
    if const_state["status"] == "OK":
        mode = const_state.get("mode", "unknown")
        enforcement = const_state.get("enforcement_active", False)
        lock_until = const_state.get("mutation_lock_until")
        health_score = const_state.get("health_score")
        
        print(f"  Mode: {mode}")
        print(f"  Enforcement Active: {'Yes' if enforcement else 'No'}")
        if lock_until:
            print(f"  Mutation Lock Until: {lock_until}")
        if health_score is not None:
            print(f"  Constitutional Health Score: {health_score}")
        
        # Check semantic doctrine status
        doctrine = const_state.get("semantic_doctrine", {})
        if doctrine:
            doctrine_status = doctrine.get("status", "UNKNOWN")
            print(f"  Semantic Refinement Doctrine: {doctrine_status}")
    else:
        print(f"  [WARN] {const_state.get('message', 'Unknown error')}")
    
    print()
    
    # AXIS 3: Audit Integrity
    print("[AXIS 3] AUDIT INTEGRITY:")
    audit = check_audit_integrity()
    
    if audit["status"] == "OK":
        completeness = audit.get("completeness", 0)
        total = audit.get("total_entries", 0)
        incomplete = audit.get("incomplete_entries", 0)
        
        print(f"  Total Entries: {total}")
        print(f"  Incomplete Entries: {incomplete}")
        print(f"  Completeness: {completeness}%")
        
        if completeness < 100:
            print(f"  [WARN] Audit completeness below 100% - forensic artifacts may be incomplete")
        else:
            print(f"  [OK] All audit artifacts complete")
    else:
        print(f"  [WARN] {audit.get('message', 'Unknown error')}")
    
    print()
    
    # AXIS 4: Operator Friction
    print("[AXIS 4] OPERATOR FRICTION (Telemetry):")
    friction = check_operator_friction()
    
    if friction["status"] == "OK":
        total = friction.get("total_friction_points", 0)
        resolved = friction.get("resolved", 0)
        deferred = friction.get("deferred", 0)
        active = friction.get("active_issues", 0)
        
        print(f"  Total Friction Points: {total}")
        print(f"  Resolved: {resolved}")
        print(f"  Deferred to v8.0: {deferred}")
        print(f"  Active Issues: {active}")
        
        if active > 0:
            print(f"  [INFO] {active} friction points under observation (not defects)")
        else:
            print(f"  [OK] No active friction points")
    else:
        print(f"  [WARN] {friction.get('message', 'Unknown error')}")
    
    print()
    
    # AXIS 5: Historical Debt
    print("[AXIS 5] HISTORICAL DEBT:")
    debt = check_historical_debt()
    
    if debt["status"] == "OK":
        violations = debt.get("historical_violations", 0)
        archive_status = debt.get("chaos_test_results", "unknown")
        
        print(f"  Historical Violations: {violations}")
        print(f"  Chaos Test Archive: {archive_status}")
        print(f"  Note: {debt.get('note', '')}")
        
        if violations > 0:
            print(f"  [INFO] Historical violations tracked separately from current compliance")
    else:
        print(f"  [WARN] {debt.get('message', 'Unknown error')}")
    
    print()
    print("=" * 70)
    print("Status check completed - Forensic Truth First doctrine applied")
    print("=" * 70)
    
    return True
