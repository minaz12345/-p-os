# P-OS Grafana Integration - Passive Observation Architecture

## 🛡️ Constitutional Compliance Status

**Mode:** Constitutional Quietness (Day 5/30)  
**Access Level:** READ-ONLY (Mutation Lock Engaged)  
**Security Protocol:** Environment variables only - NO hardcoded credentials  

---

## 📋 Architecture Overview

This integration follows **Ścieżka 1 (Prometheus Client)** - the most constitutionally sound approach for passive observation.

### Data Flow:
```
milejczyce_operational (PostgreSQL)
         ↓
grafana_friction_exporter.py (Python - READ-ONLY queries)
         ↓
http://localhost:8000/metrics (Prometheus format)
         ↓
Prometheus (scraping every 15s)
         ↓
Grafana (visualization dashboard)
```

### Security Boundaries:
- ✅ **Python Script:** Reads from database → Exposes metrics on localhost
- ✅ **Prometheus/Grafana:** Pulls metrics → No database credentials needed
- ✅ **Credential Isolation:** Database credentials in `.env.db`, Grafana credentials in `.env.grafana`
- ❌ **NO Direct DB Access from Grafana:** Eliminates credential exposure risk

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install prometheus-client psycopg2-binary python-dotenv
```

### 2. Start the Metrics Exporter

```bash
python scripts/grafana_friction_exporter.py
```

The exporter will:
- Connect to `milejczyce_operational` database (READ-ONLY)
- Collect friction metrics every 60 seconds
- Expose metrics at `http://localhost:8000/metrics`

### 3. Configure Prometheus

Add this to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'pos_friction_metrics'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 15s
```

### 4. Import Grafana Dashboard

1. Open Grafana at `http://localhost:3000`
2. Go to **Dashboards** → **Import**
3. Upload `config/grafana_dashboard_friction_map.json`
4. Select **Prometheus** as the datasource
5. Click **Import**

---

## 📊 Available Metrics

### Citizen Feedback Metrics
- `pos_citizen_feedback_by_status{category, status}` - Feedback volume by category and status

### Service Request Metrics
- `pos_service_requests_by_type{service_type, priority, status}` - Request count by type, priority, status

### Epistemic Health Metrics
- `pos_epistemic_health_score{system_version}` - Overall health score (0-100)
- `pos_dry_run_adoption_rate{measurement_period}` - Dry-run adoption percentage
- `pos_event_chain_integrity{chain_status}` - Event chain integrity status (1=valid, 0=compromised)

### Operational Metrics
- `pos_total_observations` - Cumulative count of observation cycles

---

## 🔒 Security Considerations

### Historical Context
On **2026-05-05**, Grafana credentials were exposed via chat output (`event_id: a12a7fff...`), triggering our **Defensive Chain Severance** protocol. This integration is designed to prevent recurrence.

### Protection Measures:
1. **Environment Variables Only:** All credentials loaded from `.env` files
2. **Read-Only Database User:** Grafana/Prometheus never connect directly to PostgreSQL
3. **Localhost Binding:** Metrics exporter only accessible on `127.0.0.1:8000`
4. **No Mutation:** Python script performs SELECT queries only - zero writes to database

### Compliance Checklist:
- [x] Credentials stored in `.env.db` and `.env.grafana` (never hardcoded)
- [x] Database connection uses existing `pos_admin` user with rotated password
- [x] No new tables created in `milejczyce_operational`
- [x] Script documented as "Passive Observation Tool"
- [x] Mutation Lock respected (no INSERT/UPDATE/DELETE operations)

---

## 🧪 Testing

### Verify Exporter is Running:
```bash
curl http://localhost:8000/metrics
```

Expected output should include lines like:
```
# HELP pos_citizen_feedback_by_status Number of citizen feedback items by category and status
# TYPE pos_citizen_feedback_by_status gauge
pos_citizen_feedback_by_status{category="utilities",status="resolved"} 17.0
```

### Verify Grafana Dashboard:
1. Check that all panels show data (not "No Data")
2. Verify Epistemic Health Score shows ~99.7
3. Confirm Event Chain Integrity shows 1 (valid)

---

## 📝 Operational Notes

### During Constitutional Quietness (Until 2026-06-10):
- **Purpose:** Passive observation and friction log visualization
- **Frequency:** Metrics collected every 60 seconds
- **Impact:** Zero - read-only queries with minimal database load

### Post-Quietness (v8.0 Development):
- **Enhancement:** Integrate with Semantic Canonicalization pipeline
- **Real-time Data:** Replace synthetic test data with real citizen feedback
- **Alert Rules:** Configure W11 violation alerts in Grafana

---

## 🛑 Troubleshooting

### Exporter Won't Start:
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# Kill existing process if needed
taskkill /PID <PID> /F
```

### No Data in Grafana:
1. Verify Prometheus is scraping: `http://localhost:9090/targets`
2. Check exporter logs for database connection errors
3. Ensure `.env.db` contains correct credentials

### Credential Errors:
```bash
# Re-rotate password if compromised
python scripts/rotate_password.py
```

---

## 📚 Related Documentation

- `archive/week4_sovereignty_exam/ARCHIVE-P-OS-7.5-REMEDIATION-CYCLE-v1.2-CLOSURE-20260512.yaml` - Remediation cycle documentation
- `docs/DESIGN_NOTE_EPISTEMIC_MONITORING_ARCHITECTURE.md` - Epistemic monitoring design
- `reports/CASE_STUDY_EPISTEMIC_SELF_CORRECTION_LOOP_20260513.md` - Self-correction case study

---

**Last Updated:** 2026-05-13  
**Status:** Constitutional Quietness Compliant  
**Next Review:** 2026-06-10 (v8.0 awakening)
