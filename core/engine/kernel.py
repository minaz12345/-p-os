"""
P-OS Core Kernel (L8 Router)
Central orchestration engine for the modular decision OS
"""

import sys
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from core.db.db import get_db_conn, init_db
from core.engine.event_bus import EventBus, get_event_bus, EventType
from core.engine.scheduler import Scheduler
from core.router.router import MessageRouter
from core.policies.enhanced_policy_engine import EnhancedPolicyEngine
from core.policies.enhanced_policy_engine import EnhancedPolicyEngine as PolicyEngine
from core.db.recovery_manager import RecoveryManager, get_recovery_manager
from core.db.agent_repository import get_agent_repository
from core.observability.logging_framework import get_logger, set_correlation_id, get_correlation_id
import uuid

# Initialize logger
logger = get_logger(__name__)



class POSKernel:
    """
    Central kernel orchestrating all P-OS components.

    Responsibilities:
    - Initialize and coordinate subsystems
    - Route messages between components
    - Manage event lifecycle
    - Enforce policies
    - Provide system health monitoring
    """

    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self.db_conn = None
        self.event_bus = None
        self.scheduler = None
        self.router = None
        self.policy_engine = None
        self.enhanced_policy_engine = None
        self.recovery_manager = None
        self.agent_repo = None
        self.running = False

    def initialize(self):
        """Initialize all kernel subsystems."""
        logger.info("Initializing P-OS Universal Protocol Kernel v5.0.0 (Enterprise)")

        # Initialize database
        logger.info("[1/7] Initializing database...")
        init_db(self.db_path)
        self.db_conn = get_db_conn(self.db_path)

        # Initialize repositories
        logger.info("[2/7] Initializing repositories...")
        self.agent_repo = get_agent_repository(self.db_conn)

        # Initialize recovery manager
        logger.info("[3/7] Initializing recovery manager...")
        self.recovery_manager = get_recovery_manager(db_conn=self.db_conn)

        # Initialize event bus
        logger.info("[4/7] Initializing event bus...")
        self.event_bus = get_event_bus(self.db_conn)

        # Initialize scheduler
        logger.info("[5/7] Initializing scheduler...")
        self.scheduler = Scheduler(self.db_conn, self.event_bus)

        # Initialize message router
        logger.info("[6/7] Initializing message router...")
        self.router = MessageRouter(self.db_conn, self.event_bus)

        # Initialize policy engine
        logger.info("[7/8] Initializing policy engine...")
        self.policy_engine = PolicyEngine(self.db_conn, self.event_bus)

        # Initialize enhanced policy engine (RBAC v2)
        logger.info("[8/8] Initializing enhanced policy engine (RBAC v2)...")
        self.enhanced_policy_engine = EnhancedPolicyEngine(self.db_conn, self.event_bus)

        # Register default agents
        self._register_default_agents()

        # Subscribe to system events
        self._setup_event_handlers()

        # Run initial corruption scan
        self._run_initial_health_check()

        logger.info("All subsystems initialized successfully")

    def _run_initial_health_check(self):
        """Run initial health check and corruption detection."""
        if not self.recovery_manager:
            return

        logger.info("Running initial health check...")

        # Check for corruption
        findings = self.recovery_manager.detect_corruption()

        if findings:
            logger.warning(f"Found {len(findings)} potential issues during health check")
            for finding in findings:
                logger.warning(f"  - [{finding['severity']}] {finding['details']}")

            # Attempt auto-repair for non-critical issues
            repairable = [f for f in findings if f.get('severity') != 'critical']
            if repairable:
                logger.info(f"Attempting auto-repair of {len(repairable)} issues...")
                results = self.recovery_manager.auto_repair(repairable)
                logger.info(f"Repaired: {len(results['repaired'])} issues")
        else:
            logger.info("Health check passed - no corruption detected")

        # Register circuit breakers for external services
        self.recovery_manager.register_circuit_breaker("deepseek_api", failure_threshold=3, recovery_timeout=300)
        self.recovery_manager.register_circuit_breaker("external_ingest", failure_threshold=5, recovery_timeout=60)


    def _register_default_agents(self):
        """Register default system agents using AgentRepository."""
        default_agents = [
            {
                "agent_id": "NOI-CORE",
                "agent_name": "NOI Core Orchestrator",
                "role": "Orchestrator",
                "scope": "*",
                "allowed_ops": "*",
                "active": 1,
                "system_prompt": "Main orchestrator agent for P-OS system.",
                "layer": 9
            },
            {
                "agent_id": "ANALYST",
                "agent_name": "Analyst Agent",
                "role": "Analyst",
                "scope": "*",
                "allowed_ops": "read,write,query",
                "active": 1,
                "system_prompt": "Analyzes tokens and provides insights.",
                "layer": 8
            },
            {
                "agent_id": "INGEST",
                "agent_name": "Ingest Agent",
                "role": "Ingestor",
                "scope": "*",
                "allowed_ops": "read,write",
                "active": 1,
                "system_prompt": "Handles data ingestion from external sources.",
                "layer": 8
            },
            {
                "agent_id": "RISK",
                "agent_name": "Risk Assessment Agent",
                "role": "Risk Analyst",
                "scope": "*",
                "allowed_ops": "read,query",
                "active": 1,
                "system_prompt": "Identifies and assesses risks.",
                "layer": 8
            },
            {
                "agent_id": "GOVERNANCE",
                "agent_name": "Governance Agent",
                "role": "Policy Enforcer",
                "scope": "*",
                "allowed_ops": "read,query,veto",
                "active": 1,
                "system_prompt": "Enforces governance policies and compliance.",
                "layer": 11
            },
            {
                "agent_id": "REPORTING",
                "agent_name": "Reporting Agent",
                "role": "Reporter",
                "scope": "*",
                "allowed_ops": "read,write",
                "active": 1,
                "system_prompt": "Generates reports and summaries.",
                "layer": 8
            }
        ]

        registered_count = 0
        for agent_data in default_agents:
            try:
                success = self.agent_repo.register_agent(agent_data)
                if success:
                    registered_count += 1
            except Exception as e:
                logger.warning(f"Failed to register agent {agent_data['agent_id']}: {e}")

        logger.info(f"Registered {registered_count}/{len(default_agents)} default agents")

        # Try to register DeepSeek agent if configured
        self._register_deepseek_agent()

    def _register_deepseek_agent(self):
        """Register DeepSeek agent if API key is configured."""
        try:
            from core.config import get_config
            config = get_config()

            if config.has_api_key("DEEPSEEK"):
                from agents.implementations.deepseek_agent import register_deepseek_agent
                register_deepseek_agent(self)
            else:
                logger.info("DeepSeek agent not configured (set DEEPSEEK_API_KEY in .env)")
        except ImportError:
            logger.info("DeepSeek agent module not found - skipping")
        except Exception as e:
            logger.warning(f"Failed to register DeepSeek agent: {e}")

    def _setup_event_handlers(self):
        """Setup internal event handlers."""

        def on_token_created(event):
            """Handle token creation events."""
            payload = event.get("payload", {})
            token_id = payload.get("token_id")
            print(f"[KERNEL] Token created: {token_id}")

        def on_conflict_detected(event):
            """Handle conflict detection events."""
            payload = event.get("payload", {})
            print(f"[KERNEL ALERT] Conflict detected: {payload}")

        def on_policy_denied(event):
            """Handle policy denial events."""
            payload = event.get("payload", {})
            print(f"[KERNEL POLICY] Access denied: {payload}")

        # Subscribe to critical events
        self.event_bus.subscribe(EventType.TOKEN_CREATED.value, on_token_created)
        self.event_bus.subscribe(EventType.CONFLICT_DETECTED.value, on_conflict_detected)
        self.event_bus.subscribe(EventType.POLICY_DENIED.value, on_policy_denied)

    def start(self):
        """Start the kernel and all subsystems."""
        if self.running:
            print("[KERNEL] Already running")
            return

        print("\n[KERNEL] Starting P-OS Universal Protocol...")
        self.running = True

        # Start scheduler
        self.scheduler.start()

        # Publish startup event
        self.event_bus.publish(
            "SYSTEM_START",  # Changed from SYSTEM_ERROR to proper event type
            payload={"message": "P-OS Kernel started", "version": "5.0.0"},
            source_agent="KERNEL",
            priority=1
        )

        print("[KERNEL] System running\n")

    def stop(self):
        """Stop the kernel and cleanup."""
        if not self.running:
            return

        # EMIT AUDIT EVENT (R3 Compliance - Forensic Continuity)
        try:
            from datetime import datetime, timezone
            
            stop_event = {
                "event_type": "SYSTEM_STOP",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "correlation_id": str(uuid.uuid4()),
                "actor_identity": "kernel",
                "risk_level": "HIGH",
                "metadata": {
                    "initiated_by": "kernel.stop()",
                    "components_stopped": ["scheduler", "database"],
                    "reason": "graceful_shutdown"
                }
            }
            
            if self.event_bus:
                self.event_bus.emit(stop_event)
                logger.info("SYSTEM_STOP event emitted")
        except Exception as e:
            logger.error(f"Failed to emit SYSTEM_STOP event: {e}")
            # Continue with shutdown even if event emission fails

        print("\n[KERNEL] Stopping P-OS...")
        self.running = False

        # Stop scheduler
        if self.scheduler:
            self.scheduler.stop()

        # Close database connection
        if self.db_conn:
            self.db_conn.close()

        print("[KERNEL] System stopped\n")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status."""
        status = {
            "running": self.running,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": "connected" if self.db_conn else "disconnected",
                "event_bus": "active" if self.event_bus else "inactive",
                "scheduler": "running" if self.scheduler and self.scheduler.running else "stopped",
                "router": "active" if self.router else "inactive",
                "policy_engine": "active" if self.policy_engine else "inactive"
            }
        }

        # Get statistics
        if self.db_conn:
            try:
                status["statistics"] = {
                    "tokens": self.db_conn.execute("SELECT COUNT(*) FROM tokens").fetchone()[0],
                    "agents": self.db_conn.execute("SELECT COUNT(*) FROM agents WHERE active = 1").fetchone()[0],
                    "unprocessed_events": self.event_bus.get_unprocessed_count() if self.event_bus else 0,
                    "pending_messages": self.db_conn.execute(
                        "SELECT COUNT(*) FROM agent_messages WHERE status = 'pending'"
                    ).fetchone()[0],
                    "active_conflicts": self.db_conn.execute(
                        "SELECT COUNT(*) FROM conflicts WHERE resolved = 0"
                    ).fetchone()[0]
                }
            except Exception as e:
                status["statistics_error"] = str(e)

        return status

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            "status": "healthy",
            "checks": []
        }

        # W11 FLAG CHECK (R4 Compliance)
        try:
            from w11_guard import get_active_flags, BLOCKING_FLAGS
            w11_flags = get_active_flags()
            
            if w11_flags:
                blocking_active = [f for f in w11_flags if f in BLOCKING_FLAGS]
                if blocking_active:
                    health["status"] = "degraded"
                    health["checks"].append({
                        "component": "w11_enforcement",
                        "status": "active_restriction",
                        "blocking_flags": blocking_active,
                        "all_flags": w11_flags
                    })
                else:
                    health["checks"].append({
                        "component": "w11_enforcement",
                        "status": "warning_flags_active",
                        "flags": w11_flags
                    })
            else:
                health["checks"].append({"component": "w11_enforcement", "status": "ok"})
        except Exception as e:
            health["checks"].append({
                "component": "w11_enforcement",
                "status": "error",
                "message": f"W11 check failed: {str(e)}"
            })
            # Don't degrade status for W11 check failure alone

        # Database check
        try:
            if self.db_conn:
                self.db_conn.execute("SELECT 1")
                health["checks"].append({"component": "database", "status": "ok"})
            else:
                health["checks"].append({"component": "database", "status": "error", "message": "Not connected"})
                health["status"] = "degraded"
        except Exception as e:
            health["checks"].append({"component": "database", "status": "error", "message": str(e)})
            health["status"] = "unhealthy"

        # Event bus check
        if self.event_bus:
            unprocessed = self.event_bus.get_unprocessed_count()
            if unprocessed > 1000:
                health["checks"].append({
                    "component": "event_bus",
                    "status": "warning",
                    "message": f"{unprocessed} unprocessed events"
                })
                if health["status"] == "healthy":
                    health["status"] = "degraded"
            else:
                health["checks"].append({"component": "event_bus", "status": "ok"})
        else:
            health["checks"].append({"component": "event_bus", "status": "error"})
            health["status"] = "unhealthy"

        # Scheduler check
        if self.scheduler and self.scheduler.running:
            health["checks"].append({"component": "scheduler", "status": "ok"})
        else:
            health["checks"].append({"component": "scheduler", "status": "warning", "message": "Not running"})

        return health


# Global kernel instance with thread-safe initialization
_kernel_instance: Optional[POSKernel] = None
_kernel_lock = threading.Lock()


def get_kernel(db_path: str = None) -> POSKernel:
    """Get or create global kernel instance (thread-safe singleton)."""
    global _kernel_instance
    
    if _kernel_instance is None:
        with _kernel_lock:
            if _kernel_instance is None:  # Double-check locking
                _kernel_instance = POSKernel(db_path)
                _kernel_instance.initialize()
    
    return _kernel_instance


if __name__ == "__main__":
    # Test kernel initialization
    kernel = get_kernel()
    kernel.start()

    # Get status
    status = kernel.get_system_status()
    print("\nSystem Status:")
    print(json.dumps(status, indent=2))

    # Health check
    health = kernel.health_check()
    print("\nHealth Check:")
    print(json.dumps(health, indent=2))

    kernel.stop()
