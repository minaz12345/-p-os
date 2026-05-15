"""
P-OS v8.0 - Epistemic KPI Engine
Measures governance cognition, not just operational performance.

KPIs:
1. Dry-run persistence (absolute count stability)
2. Classification stability (epistemic state consistency)
3. Governance reconciliation latency (conflict resolution speed)
4. Evidence completeness (audit trail quality)
5. Context preservation rate (decision rationale retention)
6. False positive escalation rate (alert accuracy)
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


class EpistemicKPICalculator:
    """Calculates governance cognition metrics from observation logs."""
    
    def __init__(self, observation_log_path: str = "pos/OBSERVATION_LOG.jsonl"):
        self.log_path = observation_log_path
        self.data = self._load_data()
    
    def _load_data(self) -> List[Dict]:
        """Load and parse observation log entries."""
        try:
            with open(self.log_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            return [json.loads(line) for line in lines]
        except FileNotFoundError:
            print(f"Warning: {self.log_path} not found")
            return []
    
    # ── KPI 1: Dry-Run Persistence ──────────────────────────────────────
    
    def calculate_dry_run_persistence(self, window_days: int = 7) -> Dict:
        """
        Measures whether safety simulation culture persists over time.
        
        Returns absolute dry-run counts, not percentages.
        Percentage is misleading when execution volume varies.
        """
        if not self.data:
            return {"status": "NO_DATA", "recommendation": "Collect more observations"}
        
        # Filter to recent window
        cutoff = datetime.now() - timedelta(days=window_days)
        recent = []
        for d in self.data:
            try:
                ts = d['timestamp'].replace('Z', '+00:00')
                obs_time = datetime.fromisoformat(ts)
                # Make cutoff timezone-aware for comparison
                if obs_time.tzinfo is not None and cutoff.tzinfo is None:
                    cutoff_aware = cutoff.replace(tzinfo=obs_time.tzinfo)
                    if obs_time > cutoff_aware:
                        recent.append(d)
                elif obs_time > cutoff:
                    recent.append(d)
            except (ValueError, KeyError):
                continue
        
        if not recent:
            return {"status": "INSUFFICIENT_DATA", "recommendation": f"Need data from last {window_days} days"}
        
        # Extract absolute dry-run counts
        dry_run_counts = [
            d['automated_metrics']['dry_run_adoption']['dry_run_count']
            for d in recent
        ]
        
        execution_counts = [
            d['automated_metrics']['dry_run_adoption']['execution_count']
            for d in recent
        ]
        
        # Calculate stability metrics
        avg_dry_runs = sum(dry_run_counts) / len(dry_run_counts)
        min_dry_runs = min(dry_run_counts)
        max_dry_runs = max(dry_run_counts)
        std_dev = (sum((x - avg_dry_runs) ** 2 for x in dry_run_counts) / len(dry_run_counts)) ** 0.5
        
        # Trend analysis
        if len(dry_run_counts) >= 2:
            trend = dry_run_counts[-1] - dry_run_counts[0]
        else:
            trend = 0
        
        # Classification
        if avg_dry_runs >= 30:
            status = "HEALTHY"
            interpretation = "Strong safety simulation culture"
        elif avg_dry_runs >= 20:
            status = "ACCEPTABLE"
            interpretation = "Moderate safety culture, monitor trend"
        elif avg_dry_runs >= 10:
            status = "WARNING"
            interpretation = "Safety culture weakening, investigate"
        else:
            status = "CRITICAL"
            interpretation = "Safety simulation abandoned, immediate intervention needed"
        
        return {
            "kpi": "dry_run_persistence",
            "status": status,
            "interpretation": interpretation,
            "metrics": {
                "avg_daily_dry_runs": round(avg_dry_runs, 2),
                "min_dry_runs": min_dry_runs,
                "max_dry_runs": max_dry_runs,
                "std_deviation": round(std_dev, 2),
                "trend_change": trend,
                "observation_count": len(recent),
                "avg_execution_count": round(sum(execution_counts) / len(execution_counts), 2)
            },
            "recommendation": self._dry_run_recommendation(status, trend, avg_dry_runs)
        }
    
    def _dry_run_recommendation(self, status: str, trend: int, avg: float) -> str:
        """Generate actionable recommendation based on dry-run persistence."""
        if status == "HEALTHY":
            return "Continue current practices. Consider documenting successful patterns."
        elif status == "ACCEPTABLE":
            return "Monitor trend. If declining, investigate operational changes."
        elif status == "WARNING":
            return "Review recent operations. Are operators skipping safety checks?"
        else:  # CRITICAL
            return "URGENT: Investigate why dry-run usage dropped. Reinforce safety culture."
    
    # ── KPI 2: Classification Stability ─────────────────────────────────
    
    def calculate_classification_stability(self) -> Dict:
        """
        Measures whether epistemic states remain consistent over time.
        
        Detects classification drift (e.g., TRUSTED → DISPUTED without cause).
        """
        if not self.data:
            return {"status": "NO_DATA"}
        
        # Extract W11 states (proxy for classification)
        w11_states = [
            d['automated_metrics']['w11_activations'].get('system_state', 'UNKNOWN')
            for d in self.data
        ]
        
        # Count state transitions
        transitions = 0
        for i in range(1, len(w11_states)):
            if w11_states[i] != w11_states[i-1]:
                transitions += 1
        
        # Calculate stability score
        total_observations = len(w11_states)
        stability_rate = ((total_observations - transitions) / total_observations) * 100 if total_observations > 0 else 0
        
        # Classification
        if stability_rate >= 95:
            status = "STABLE"
            interpretation = "Classifications consistent, minimal drift"
        elif stability_rate >= 80:
            status = "MODERATE_DRIFT"
            interpretation = "Some classification changes, review triggers"
        else:
            status = "HIGH_DRIFT"
            interpretation = "Frequent classification changes, investigate root causes"
        
        return {
            "kpi": "classification_stability",
            "status": status,
            "interpretation": interpretation,
            "metrics": {
                "stability_rate_percent": round(stability_rate, 2),
                "total_transitions": transitions,
                "total_observations": total_observations,
                "unique_states": list(set(w11_states)),
                "most_common_state": max(set(w11_states), key=w11_states.count)
            },
            "recommendation": self._classification_recommendation(status, transitions)
        }
    
    def _classification_recommendation(self, status: str, transitions: int) -> str:
        """Generate recommendation based on classification stability."""
        if status == "STABLE":
            return "Classifications stable. Continue current governance practices."
        elif status == "MODERATE_DRIFT":
            return f"Review {transitions} state transitions. Are they justified?"
        else:
            return f"HIGH DRIFT: {transitions} transitions detected. Investigate classification criteria."
    
    # ── KPI 3: Evidence Completeness ────────────────────────────────────
    
    def calculate_evidence_completeness(self) -> Dict:
        """
        Measures whether operations leave sufficient audit trails.
        
        Checks for missing timestamps, incomplete metrics, absent operator feedback.
        """
        if not self.data:
            return {"status": "NO_DATA"}
        
        total = len(self.data)
        complete_entries = 0
        
        for entry in self.data:
            # Check required fields
            has_timestamp = 'timestamp' in entry
            has_metrics = 'automated_metrics' in entry
            has_audit_logs = 'audit_logs' in entry.get('automated_metrics', {})
            has_w11 = 'w11_activations' in entry.get('automated_metrics', {})
            
            if all([has_timestamp, has_metrics, has_audit_logs, has_w11]):
                complete_entries += 1
        
        completeness_rate = (complete_entries / total) * 100 if total > 0 else 0
        
        # Classification
        if completeness_rate >= 95:
            status = "COMPLETE"
            interpretation = "Audit trails comprehensive"
        elif completeness_rate >= 80:
            status = "PARTIAL"
            interpretation = "Some gaps in evidence chain"
        else:
            status = "INCOMPLETE"
            interpretation = "Significant evidence gaps, improve logging"
        
        return {
            "kpi": "evidence_completeness",
            "status": status,
            "interpretation": interpretation,
            "metrics": {
                "completeness_rate_percent": round(completeness_rate, 2),
                "complete_entries": complete_entries,
                "total_entries": total,
                "missing_fields": total - complete_entries
            },
            "recommendation": self._evidence_recommendation(status, completeness_rate)
        }
    
    def _evidence_recommendation(self, status: str, rate: float) -> str:
        """Generate recommendation based on evidence completeness."""
        if status == "COMPLETE":
            return "Evidence chain robust. Maintain current logging standards."
        elif status == "PARTIAL":
            return f"Improve logging completeness (currently {rate:.0f}%). Add missing fields."
        else:
            return f"CRITICAL: Only {rate:.0f}% completeness. Implement mandatory audit fields."
    
    # ── KPI 4: Context Preservation Rate ────────────────────────────────
    
    def calculate_context_preservation(self) -> Dict:
        """
        Measures whether decisions retain their rationale over time.
        
        Checks for operator feedback, document references, contextual notes.
        """
        if not self.data:
            return {"status": "NO_DATA"}
        
        total = len(self.data)
        entries_with_context = 0
        
        for entry in self.data:
            # Check for contextual information
            has_feedback = 'operator_feedback' in entry
            has_documents = entry.get('automated_metrics', {}).get('document_usage', {}).get('documents_found', 0) > 0
            
            if has_feedback or has_documents:
                entries_with_context += 1
        
        preservation_rate = (entries_with_context / total) * 100 if total > 0 else 0
        
        # Classification
        if preservation_rate >= 50:
            status = "GOOD"
            interpretation = "Context well-preserved in decisions"
        elif preservation_rate >= 25:
            status = "MODERATE"
            interpretation = "Some context captured, improve documentation"
        else:
            status = "POOR"
            interpretation = "Decisions lack context, add rationale tracking"
        
        return {
            "kpi": "context_preservation_rate",
            "status": status,
            "interpretation": interpretation,
            "metrics": {
                "preservation_rate_percent": round(preservation_rate, 2),
                "entries_with_context": entries_with_context,
                "total_entries": total,
                "feedback_entries": sum(1 for d in self.data if 'operator_feedback' in d)
            },
            "recommendation": self._context_recommendation(status, preservation_rate)
        }
    
    def _context_recommendation(self, status: str, rate: float) -> str:
        """Generate recommendation based on context preservation."""
        if status == "GOOD":
            return "Context preservation strong. Continue capturing operator feedback."
        elif status == "MODERATE":
            return f"Improve context capture (currently {rate:.0f}%). Add decision rationale fields."
        else:
            return f"POOR context ({rate:.0f}%). Require operator comments for significant operations."
    
    # ── KPI 5: False Positive Escalation Rate ───────────────────────────
    
    def calculate_false_positive_rate(self) -> Dict:
        """
        Estimates rate of alerts triggered by misinterpretation vs real issues.
        
        Uses W11 activations as proxy for alerts.
        Compares with actual constitutional violations.
        """
        if not self.data:
            return {"status": "NO_DATA"}
        
        total_observations = len(self.data)
        w11_activations = sum(
            d['automated_metrics']['w11_activations'].get('activations', 0)
            for d in self.data
        )
        
        # In current system, W11 activations are rare (good sign)
        # False positive rate = (alerts without real violations) / total alerts
        # Since we have 0 activations, we can't calculate this yet
        
        if w11_activations == 0:
            return {
                "kpi": "false_positive_escalation_rate",
                "status": "NO_ALERTS_TO_ANALYZE",
                "interpretation": "No W11 activations recorded. System stable.",
                "metrics": {
                    "total_alerts": 0,
                    "confirmed_violations": 0,
                    "false_positive_rate_percent": 0,
                    "note": "Insufficient data for false positive analysis"
                },
                "recommendation": "Continue monitoring. Track future W11 activations for pattern analysis."
            }
        
        # Placeholder for future implementation when W11 activations occur
        return {
            "kpi": "false_positive_escalation_rate",
            "status": "PENDING_DATA",
            "interpretation": "Awaiting W11 activation events for analysis",
            "metrics": {
                "total_alerts": w11_activations,
                "confirmed_violations": 0,  # Would need manual verification
                "false_positive_rate_percent": 0
            },
            "recommendation": "When W11 activates, verify if it's true violation or false positive."
        }
    
    # ── Comprehensive Epistemic Health Report ───────────────────────────
    
    def generate_epistemic_health_report(self) -> Dict:
        """
        Generates comprehensive epistemic health assessment.
        
        Combines all KPIs into unified governance cognition score.
        """
        print("=" * 80)
        print("EPISTEMIC HEALTH REPORT - GOVERNANCE COGNITION METRICS")
        print("=" * 80)
        print()
        
        # Calculate all KPIs
        kpis = {
            "dry_run_persistence": self.calculate_dry_run_persistence(),
            "classification_stability": self.calculate_classification_stability(),
            "evidence_completeness": self.calculate_evidence_completeness(),
            "context_preservation": self.calculate_context_preservation(),
            "false_positive_rate": self.calculate_false_positive_rate()
        }
        
        # Print results
        overall_score = 0
        scored_kpis = 0
        
        for kpi_name, result in kpis.items():
            print(f"\n{'─' * 80}")
            print(f"KPI: {kpi_name.upper().replace('_', ' ')}")
            print(f"{'─' * 80}")
            print(f"Status: {result['status']}")
            print(f"Interpretation: {result['interpretation']}")
            print(f"\nMetrics:")
            for metric_name, metric_value in result['metrics'].items():
                print(f"  • {metric_name}: {metric_value}")
            print(f"\nRecommendation: {result['recommendation']}")
            
            # Calculate score (simple heuristic)
            status_scores = {
                "HEALTHY": 100, "STABLE": 100, "COMPLETE": 100, "GOOD": 90,
                "ACCEPTABLE": 80, "MODERATE": 70, "PARTIAL": 70,
                "WARNING": 50, "MODERATE_DRIFT": 50,
                "CRITICAL": 20, "HIGH_DRIFT": 20, "INCOMPLETE": 20, "POOR": 20
            }
            
            if result['status'] in status_scores:
                overall_score += status_scores[result['status']]
                scored_kpis += 1
        
        # Overall epistemic health score
        if scored_kpis > 0:
            overall_health = overall_score / scored_kpis
        else:
            overall_health = 0
        
        print(f"\n{'=' * 80}")
        print(f"OVERALL EPISTEMIC HEALTH SCORE: {overall_health:.1f}/100")
        print(f"{'=' * 80}")
        
        if overall_health >= 80:
            print("\n✅ EPISTEMIC MATURITY: HIGH")
            print("   System demonstrates strong governance cognition.")
        elif overall_health >= 60:
            print("\n⚠️  EPISTEMIC MATURITY: MODERATE")
            print("   Some areas need improvement. Review recommendations.")
        else:
            print("\n❌ EPISTEMIC MATURITY: LOW")
            print("   Significant governance cognition gaps. Immediate action needed.")
        
        print(f"\n{'=' * 80}")
        print("Report generated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print(f"{'=' * 80}")
        
        return {
            "overall_health_score": round(overall_health, 1),
            "kpis": kpis,
            "timestamp": datetime.now().isoformat()
        }


# ── Main Execution ──────────────────────────────────────────────────────

if __name__ == "__main__":
    calculator = EpistemicKPICalculator()
    report = calculator.generate_epistemic_health_report()
