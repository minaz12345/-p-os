# P-OS Universal Protocol v4.1

## Modular Decision OS | Production Hardened

Complete implementation of the P-OS (POS) Universal Protocol - a modular, event-driven, agent-first autonomous data operating system with enterprise-grade security and plugin sovereignty.

**Latest Updates:**
- v4.1.0: Plugin Sovereignty Protocol (Iteration 2C)
- Security Hardening: CORS validation, input sanitization, SQL injection prevention
- Performance Optimization: Enhanced database indexing, query optimization
- **Current Status**: Production Ready with caveats (see AUDIT_REPORT_ITERATION_3.md)

---

## System Architecture

```
pos/
├── core/
│   ├── engine/
│   │   ├── kernel.py          # Central orchestration engine
│   │   ├── scheduler.py       # Task scheduling & execution
│   │   └── event_bus.py       # Event-driven messaging
│   │
│   ├── db/
│   │   ├── db.py              # Database module with migrations
│   │   └── schema.sql         # Production-grade schema v4.0
│   │
│   ├── router/
│   │   └── router.py          # Inter-agent message routing
│   │
│   ├── tokenizer/
│   │   ├── tokenizer.py       # Universal tokenizer protocol
│   │   ├── category_map.py    # 16 universal categories
│   │   ├── scorer.py          # Strategic weight scoring
│   │   ├── linker.py          # Semantic linking engine
│   │   └── change_detector.py # NEW/UPDATE/CONFLICT/DECAY detection
│   │
│   ├── policies/
│   │   └── engine.py          # RBAC policy enforcement (L11)
│   │
│   └── api/
│       └── rest_api.py        # External Brain REST API
│
├── agents/
│   └── base/
│       └── base_agent.py      # Agent framework V2
│
├── ingest/
│   └── pipelines/
│       └── pipeline.py        # Autonomic ingest loop
│
├── tests/
│   └── test_system.py         # Production test suite
│
└── main.py                    # Main entry point
```

---

## Key Features

### 1. Universal Tokenizer Protocol
- **16 Universal Categories**: INFRA, ENV, SOC, GOV, ECO, ACT, PPL, HIST, CULT, STRAT, SAFE, LEG, OPS, INTEL, MAN, FLEX
- **Atomic Fact Extraction**: Converts artefacts into knowledge tokens
- **Strategic Scoring**: Weight calculation (0.0 - 2.0) based on content importance
- **Semantic Linking**: Auto-links related tokens
- **Change Detection**: Detects NEW, UPDATE, CONFLICT, FALSE_CLOSURE, DECAY patterns

### 2. Event Bus System (L10)
- Publish/Subscribe architecture
- Event types: TOKEN_CREATED, TOKEN_UPDATED, CONFLICT_DETECTED, DECISION_REQUIRED, ALERT_HIGH, etc.
- Persistent event queue with priority processing
- Asynchronous event handling

### 3. Agent Framework V2
Every agent implements required protocols:
- `process(message)` - Process incoming messages
- `query(query_text, filters)` - Query knowledge base
- `notify(notification)` - Handle notifications
- `validate(data)` - Validate data/tokens

Supported communication protocols:
- REQUEST, INFORM, QUERY, ALERT, UPDATE, VETO, DELEGATE

### 4. Policy Engine (L11)
- Role-Based Access Control (RBAC)
- Resource-level permissions
- Agent-specific permissions
- Protected token prefixes (NOI-, SYS-, ADMIN-)
- Emergency override capability
- Full audit trail
- Rule priority system with cache TTL

### 5. Message Router (L8)
- Priority-based message routing (1-10)
- Protocol validation
- Message persistence and tracking
- Broadcast capability
- Delivery confirmation

### 6. Task Scheduler
- Priority-based task execution
- Retry logic with exponential backoff
- Recurring task support
- Thread-safe operation
- Task persistence

### 7. External Brain REST API
Endpoints:
```
GET  /health              - Health check
GET  /status              - System status
GET  /token/query?q=text  - Query tokens
POST /token/add           - Add token
POST /token/update        - Update token
GET  /agent/:id           - Get agent info
GET  /agents              - List agents
POST /agent/message       - Send agent message
GET  /event/log           - Get event log
GET  /context/export      - Export context
POST /ingest/trigger      - Trigger ingestion
```

### 8. Autonomic Ingest Loop
Flow: Watcher → Pipeline → Tokenizer → DB → Change Detector → Event Bus → Agent → Snapshot

Supports multiple source types: markdown, txt, csv, json, pdf, webhooks

---

## Security Features

### Enterprise-Grade Security (v4.1)
- **CORS Protection**: Origin whitelist validation prevents cross-origin attacks
- **Input Validation**: Comprehensive sanitization on all API endpoints
- **SQL Injection Prevention**: Parameterized queries with field whitelisting
- **Rate Limiting**: Configurable per-IP rate limiting
- **Authentication**: API key-based authentication with RBAC
- **Encryption**: SHA-256 based data encryption
- **Plugin Sandboxing**: Three-level isolation (L1/L2/L3) for plugins
- **Audit Logging**: Complete audit trail for all operations

### Security Hardening Tools
```bash
# Run security audit
python scripts/security_hardening.py --audit

# Rotate encryption keys
python scripts/security_hardening.py --rotate-key

# Secure environment files
python scripts/security_hardening.py --secure-env
```

### Configuration
Set allowed CORS origins:
```env
P_OS_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
```

**Important**: Before production deployment, rotate the default encryption key and review AUDIT_REPORT_ITERATION_3.md for security recommendations.

---

## Quick Start

### Initialize System

```python
from pos.core.engine.kernel import get_kernel

# Initialize kernel (auto-initializes all subsystems)
kernel = get_kernel()
kernel.start()

# Check system status
status = kernel.get_system_status()
print(status)

# Health check
health = kernel.health_check()
print(health)

# Stop system
kernel.stop()
```

### Use Tokenizer

```python
from pos.core.tokenizer.tokenizer import tokenize_artefact

# Tokenize content
token = tokenize_artefact(
    artefact_id="ART-001",
    content="Krytyczna awaria kanalizacji w centrum miasta",
    category="INFRA",
    owner="System"
)

print(f"Token ID: {token['id']}")
print(f"Category: {token['category']}")
print(f"Weight: {token['weight']}")
```

### Send Agent Messages

```python
from pos.core.router.router import MessageRouter, Protocol

router = kernel.router

# Send message between agents
msg_id = router.send_message(
    from_agent="ANALYST",
    to_agent="CORE",
    protocol=Protocol.REQUEST,
    subject="Analysis Complete",
    payload={"findings": "..."},
    priority=3
)
```

### Check Permissions

```python
from pos.core.policies.engine import PolicyDecision

policy = kernel.policy_engine

# Check if agent has permission
decision = policy.check_permission("AGENT-ID", "write", "resource-id")

if decision == PolicyDecision.ALLOW:
    print("Access granted")
else:
    print("Access denied")
```

### Start REST API Server

```bash
python pos/main.py --api --port 8000
```

Or programmatically:

```python
from pos.core.api.rest_api import RESTAPIServer

api_server = RESTAPIServer(kernel, host="0.0.0.0", port=8000)
api_server.start()
```

---

## Running Tests

```bash
python pos/tests/test_system.py
```

Expected output:
```
============================================================
TEST SUMMARY
============================================================
  [OK] Database             PASSED
  [OK] Tokenizer            PASSED
  [OK] Event Bus            PASSED
  [OK] Kernel               PASSED
  [OK] Policy Engine        PASSED
  [OK] Agent Framework      PASSED
  [OK] Message Router       PASSED

============================================================
Results: 7/7 tests passed
============================================================

[SUCCESS] All tests PASSED! System is production-ready.
```

---

## Database Schema v4.0

### Core Tables
- **tokens** - Knowledge tokens with universal categories
- **change_log** - Version tracking for token changes
- **conflicts** - Detected conflicts between tokens
- **sources** - Data source registry
- **events** - Event bus log
- **agents** - Agent registry
- **agent_messages** - Inter-agent communication
- **policy_audit** - Policy decision audit trail
- **external_ingest_log** - Ingestion tracking
- **blocks** - System architecture registry (L8)
- **shared_context** - Shared memory/context
- **artefacts** - File and output registry

### Indexes
Performance indexes on:
- Token category, status, weight, owner
- Unprocessed events
- Pending messages
- Unresolved conflicts
- Policy audit by agent

---

## Migration from v3.x

The system includes automatic migration from legacy NOI v3.x schema:

1. Old tables are backed up with `_backup_v3` suffix
2. New v4.0 schema is created
3. Existing data is migrated where compatible
4. Schema version is updated to 4.0.0

Backup is preserved for rollback capability.

---

## Configuration

Database path: `data/noi_core.db`
Schema version: `4.1.0` (updated with performance indexes)
API default port: `8000`
Policy cache TTL: `5 seconds`

### Environment Variables
```env
# Required
P_OS_ENCRYPTION_KEY=<generate-with-security-script>
P_OS_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com

# Optional
POS_API_PORT=8000
POS_API_HOST=0.0.0.0
POS_DB_PATH=data/noi_core.db
POS_LOG_LEVEL=INFO
```

---

## System Layers

- **L8** - Router/Engine (Message routing, architecture)
- **L9** - Governance/Ontology (Tokens, knowledge base)
- **L10** - Execution/Events (Event bus, messaging)
- **L11** - Audit/Policy (Policy enforcement, RBAC)

---

## System Status & Audits

### Current Status: YELLOW - Production Ready with Caveats

The system has undergone comprehensive auditing and hardening:

**Completed Iterations:**
- Iteration 2C: Plugin Sovereignty Protocol (see ITERATION_2C_COMPLETE.md)
- Hardening Iteration 2: Security fixes and performance optimization (see HARDENING_ITERATION_2.md)
- Hardening Iteration 3 Phase 1: CORS vulnerability fix (see HARDENING_ITERATION_3_PHASE1.md)

**Latest Audit:**
- Audit Iteration 3: Comprehensive security and performance audit (see AUDIT_REPORT_ITERATION_3.md)
- Findings: 1 Critical, 10 High, 12 Medium, 6 Low severity issues identified
- Remediation roadmap provided in audit report

**System Metrics:**
- Security Score: 8.0/10 (improved from 7.5/10)
- Performance Score: 7.0/10 (optimization needed)
- Code Quality: 7.8/10 (refactoring recommended)
- Production Readiness: 88% (Phase 1 hardening complete)

**Before Production Deployment:**
1. Rotate encryption key: `python scripts/security_hardening.py --rotate-key`
2. Review audit report and address remaining high-severity issues
3. Configure environment variables for your deployment
4. Run full test suite: `python tests/test_system.py`

---

## Production Deployment

### Requirements
- Python 3.8+
- SQLite 3.35+
- No external dependencies (stdlib only)

### Run as Service

```bash
# Start with API
python pos/main.py --api --port 8000

# Start without API (kernel only)
python pos/main.py
```

### Health Monitoring

```bash
curl http://localhost:8000/health
curl http://localhost:8000/status
```

---

## Architecture Principles

1. **Modular** - Each component is independent and replaceable
2. **Event-Driven** - All communication via event bus
3. **Agent-First** - Agents are first-class citizens
4. **Production-Grade** - Migrations, backups, audit trails
5. **Zero Dependencies** - Standard library only (optional Flask for API)
6. **Universal** - Adaptable for any domain (gminas, NGOs, business, OSINT)

---

## License

Internal use - P-OS Project

---

## Credits

Built according to the P-OS Universal Protocol Blueprint v4.0
Modular Decision OS | Production Upgrade

🤖 Generated with Lingma
# Constitutional Agent Test - 2026-05-08
