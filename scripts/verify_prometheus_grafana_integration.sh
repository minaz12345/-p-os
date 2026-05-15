#!/usr/bin/env bash
# P-OS v7.5 Integration Verification Script
# Purpose: Validate Prometheus + Grafana pipeline for friction metrics
# Compliance: Read-only checks, no mutations

set -e

echo "🛡️  P-OS Integration Verification Starting..."
echo "---------------------------------------------"

# 1. Check Exporter
echo "1. Checking Friction Exporter (Port 8000)..."
if curl -s http://localhost:8000/metrics | grep -q "pos_epistemic_health_score"; then
    echo "   ✅ Exporter is active and exposing metrics."
else
    echo "   ❌ Exporter check failed. Is grafana_friction_exporter.py running?"
    exit 1
fi

# 2. Check Prometheus
echo "2. Checking Prometheus (Port 9090)..."
PROM_STATUS=$(curl -s http://localhost:9090/api/v1/targets | jq -r '.data.activeTargets[] | select(.labels.job=="pos_friction_metrics") | .health')
if [ "$PROM_STATUS" == "up" ]; then
    echo "   ✅ Prometheus is scraping pos_friction_metrics successfully."
else
    echo "   ⚠️  Prometheus target status: $PROM_STATUS. Check prometheus.yml config."
fi

# 3. Check Queryability
echo "3. Checking Metric Queryability..."
HEALTH_SCORE=$(curl -s "http://localhost:9090/api/v1/query?query=pos_epistemic_health_score" | jq -r '.data.result[0].value[1]')
if [ "$HEALTH_SCORE" != "null" ]; then
    echo "   ✅ Epistemic Health Score query successful: $HEALTH_SCORE"
else
    echo "   ❌ Failed to query metrics from Prometheus."
fi

# 4. Check Grafana Datasource
echo "4. Checking Grafana Datasource (Port 3000)..."
DS_CHECK=$(curl -s http://admin:admin@localhost:3000/api/datasources | jq -r '.[] | select(.name=="Prometheus-P-OS") | .name')
if [ "$DS_CHECK" == "Prometheus-P-OS" ]; then
    echo "   ✅ Grafana datasource 'Prometheus-P-OS' is configured."
else
    echo "   ⚠️  Datasource not found. Run the datasource setup command."
fi

echo "---------------------------------------------"
echo "🛡️  Verification Complete. Tarcza w górze."
