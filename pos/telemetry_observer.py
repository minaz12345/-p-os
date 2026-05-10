#!/usr/bin/env python3
"""
P-OS CLI Telemetry Observer - 30-Day Observation Framework

Monitors v7.5 CLI usage patterns during the observation period
(2026-05-10 to 2026-06-09) to inform v8.0 planning decisions.

Usage:
    python pos/telemetry_observer.py [--daily|--weekly|--summary]
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List


class TelemetryObserver:
    """Analyzes P-OS CLI usage patterns from audit logs."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.audit_dir = self.project_root / "logs" / "cli_audit"
        self.observation_start = datetime(2026, 5, 10)
        self.observation_end = datetime(2026, 6, 9)
    
    def load_audit_logs(self) -> List[Dict]:
        """Load all audit logs from the observation period."""
        if not self.audit_dir.exists():
            return []
        
        logs = []
        for log_file in self.audit_dir.glob("pos-*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                    logs.append(data)
            except Exception as e:
                print(f"Warning: Failed to load {log_file}: {e}")
        
        return logs
    
    def filter_observation_period(self, logs: List[Dict]) -> List[Dict]:
        """Filter logs to observation period only."""
        filtered = []
        for log in logs:
            try:
                timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                if self.observation_start <= timestamp <= self.observation_end:
                    filtered.append(log)
            except Exception:
                continue
        
        return filtered
    
    def analyze_command_distribution(self, logs: List[Dict]) -> Dict[str, int]:
        """Analyze command usage frequency."""
        command_counts = Counter()
        for log in logs:
            command = log.get('command', 'unknown')
            command_counts[command] += 1
        
        return dict(command_counts.most_common())
    
    def analyze_dry_run_usage(self, logs: List[Dict]) -> Dict:
        """Analyze dry-run mode adoption rate."""
        total = len(logs)
        dry_run_count = sum(1 for log in logs if log.get('dry_run', False))
        
        return {
            'total_operations': total,
            'dry_run_operations': dry_run_count,
            'dry_run_rate': (dry_run_count / total * 100) if total > 0 else 0,
        }
    
    def analyze_verbose_usage(self, logs: List[Dict]) -> Dict:
        """Analyze verbose mode adoption rate."""
        total = len(logs)
        verbose_count = sum(1 for log in logs if log.get('verbose', False))
        
        return {
            'total_operations': total,
            'verbose_operations': verbose_count,
            'verbose_rate': (verbose_count / total * 100) if total > 0 else 0,
        }
    
    def analyze_error_rates(self, logs: List[Dict]) -> Dict:
        """Analyze error rates and patterns."""
        total = len(logs)
        errors = [log for log in logs if log.get('status') == 'error']
        
        error_by_command = Counter()
        for error in errors:
            error_by_command[error.get('command', 'unknown')] += 1
        
        return {
            'total_operations': total,
            'error_count': len(errors),
            'error_rate': (len(errors) / total * 100) if total > 0 else 0,
            'errors_by_command': dict(error_by_command.most_common()),
        }
    
    def analyze_performance(self, logs: List[Dict]) -> Dict:
        """Analyze command execution performance."""
        completed_logs = [log for log in logs if 'duration_ms' in log]
        
        if not completed_logs:
            return {'message': 'No completed operations found'}
        
        durations = [log['duration_ms'] for log in completed_logs]
        
        by_command = defaultdict(list)
        for log in completed_logs:
            command = log.get('command', 'unknown')
            by_command[command].append(log['duration_ms'])
        
        performance_by_command = {}
        for command, times in by_command.items():
            performance_by_command[command] = {
                'count': len(times),
                'avg_ms': sum(times) / len(times),
                'min_ms': min(times),
                'max_ms': max(times),
            }
        
        return {
            'overall': {
                'count': len(durations),
                'avg_ms': sum(durations) / len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
            },
            'by_command': performance_by_command,
        }
    
    def analyze_operator_activity(self, logs: List[Dict]) -> Dict:
        """Analyze operator usage patterns."""
        operators = Counter()
        for log in logs:
            operator = log.get('operator', 'unknown')
            operators[operator] += 1
        
        return dict(operators.most_common())
    
    def analyze_audit_log_growth(self) -> Dict:
        """Analyze audit log storage growth."""
        if not self.audit_dir.exists():
            return {'message': 'No audit logs found'}
        
        log_files = list(self.audit_dir.glob("pos-*.json"))
        total_size = sum(f.stat().st_size for f in log_files)
        
        # Group by date
        by_date = defaultdict(int)
        for log_file in log_files:
            date_str = log_file.stem.split('-')[1]  # Extract YYYYMMDD
            by_date[date_str] += log_file.stat().st_size
        
        return {
            'total_files': len(log_files),
            'total_size_bytes': total_size,
            'total_size_kb': round(total_size / 1024, 2),
            'average_file_size_bytes': total_size / len(log_files) if log_files else 0,
            'growth_by_date': dict(sorted(by_date.items())),
        }
    
    def generate_daily_report(self) -> Dict:
        """Generate daily telemetry report."""
        logs = self.load_audit_logs()
        observation_logs = self.filter_observation_period(logs)
        
        return {
            'report_type': 'daily',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'observation_period': {
                'start': self.observation_start.isoformat(),
                'end': self.observation_end.isoformat(),
            },
            'total_operations': len(observation_logs),
            'command_distribution': self.analyze_command_distribution(observation_logs),
            'dry_run_usage': self.analyze_dry_run_usage(observation_logs),
            'verbose_usage': self.analyze_verbose_usage(observation_logs),
            'error_rates': self.analyze_error_rates(observation_logs),
            'performance': self.analyze_performance(observation_logs),
            'operator_activity': self.analyze_operator_activity(observation_logs),
            'audit_log_growth': self.analyze_audit_log_growth(),
        }
    
    def generate_weekly_summary(self, week_number: int = 1) -> Dict:
        """Generate weekly summary report."""
        logs = self.load_audit_logs()
        
        # Calculate week boundaries
        week_start = self.observation_start + timedelta(weeks=week_number-1)
        week_end = week_start + timedelta(days=7)
        
        # Filter to this week
        week_logs = []
        for log in logs:
            try:
                timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                if week_start <= timestamp < week_end:
                    week_logs.append(log)
            except Exception:
                continue
        
        return {
            'report_type': 'weekly',
            'week_number': week_number,
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'period': {
                'start': week_start.isoformat(),
                'end': week_end.isoformat(),
            },
            'total_operations': len(week_logs),
            'command_distribution': self.analyze_command_distribution(week_logs),
            'dry_run_usage': self.analyze_dry_run_usage(week_logs),
            'verbose_usage': self.analyze_verbose_usage(week_logs),
            'error_rates': self.analyze_error_rates(week_logs),
            'performance': self.analyze_performance(week_logs),
            'operator_activity': self.analyze_operator_activity(week_logs),
        }
    
    def generate_final_summary(self) -> Dict:
        """Generate final 30-day observation summary."""
        daily_report = self.generate_daily_report()
        
        # Calculate trends and insights
        insights = []
        
        # Dry-run adoption insight
        dry_run_rate = daily_report['dry_run_usage']['dry_run_rate']
        if dry_run_rate > 50:
            insights.append("High dry-run adoption indicates strong safety consciousness")
        elif dry_run_rate < 20:
            insights.append("Low dry-run adoption suggests need for operator training")
        
        # Error rate insight
        error_rate = daily_report['error_rates']['error_rate']
        if error_rate < 5:
            insights.append("Low error rate indicates good CLI ergonomics")
        elif error_rate > 15:
            insights.append("High error rate suggests usability issues requiring attention")
        
        # Verbose mode insight
        verbose_rate = daily_report['verbose_usage']['verbose_rate']
        if verbose_rate > 40:
            insights.append("High verbose usage indicates operators value transparency")
        
        return {
            'report_type': 'final_summary',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'observation_period': {
                'start': self.observation_start.isoformat(),
                'end': self.observation_end.isoformat(),
                'duration_days': 30,
            },
            'overall_metrics': daily_report,
            'insights': insights,
            'recommendations_for_v8': self._generate_v8_recommendations(daily_report),
        }
    
    def _generate_v8_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations for v8.0 based on telemetry."""
        recommendations = []
        
        # Based on command distribution
        cmd_dist = report.get('command_distribution', {})
        if cmd_dist:
            most_used = max(cmd_dist, key=cmd_dist.get)
            recommendations.append(f"Priority enhancement for '{most_used}' command based on usage")
        
        # Based on error rates
        error_rate = report.get('error_rates', {}).get('error_rate', 0)
        if error_rate > 10:
            recommendations.append("Implement enhanced error guidance and recovery tools")
        
        # Based on dry-run usage
        dry_run_rate = report.get('dry_run_usage', {}).get('dry_run_rate', 0)
        if dry_run_rate < 30:
            recommendations.append("Improve dry-run discoverability and education")
        
        # Based on log growth
        log_growth = report.get('audit_log_growth', {})
        total_kb = log_growth.get('total_size_kb', 0)
        if total_kb > 1000:  # >1MB
            recommendations.append("Implement log rotation system (Priority 5)")
        
        recommendations.append("Proceed with emergency-stop implementation (Priority 1)")
        recommendations.append("Develop session tracking for workflow continuity (Priority 2)")
        
        return recommendations
    
    def print_report(self, report: Dict, indent: int = 0):
        """Pretty-print report to console."""
        prefix = "  " * indent
        
        for key, value in report.items():
            if isinstance(value, dict):
                print(f"{prefix}{key}:")
                self.print_report(value, indent + 1)
            elif isinstance(value, list):
                print(f"{prefix}{key}:")
                for item in value:
                    if isinstance(item, dict):
                        self.print_report(item, indent + 1)
                    else:
                        print(f"{prefix}  - {item}")
            else:
                print(f"{prefix}{key}: {value}")


def main():
    observer = TelemetryObserver()
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = 'daily'
    
    if mode == '--daily':
        report = observer.generate_daily_report()
        print("="*70)
        print("P-OS CLI TELEMETRY - DAILY REPORT")
        print("="*70)
        observer.print_report(report)
        
    elif mode == '--weekly':
        week = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        report = observer.generate_weekly_summary(week)
        print("="*70)
        print(f"P-OS CLI TELEMETRY - WEEKLY SUMMARY (Week {week})")
        print("="*70)
        observer.print_report(report)
        
    elif mode == '--summary':
        report = observer.generate_final_summary()
        print("="*70)
        print("P-OS CLI TELEMETRY - 30-DAY OBSERVATION SUMMARY")
        print("="*70)
        observer.print_report(report)
        
    else:
        print("Usage: python pos/telemetry_observer.py [--daily|--weekly N|--summary]")
        sys.exit(1)


if __name__ == "__main__":
    main()
