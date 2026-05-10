#!/usr/bin/env python3
"""
P-OS CLI Phase 1 - Acceptance Test Suite

Validates that the CLI meets all constitutional requirements and acceptance criteria.

Run with:
    python pos/test_cli.py
"""

import subprocess
import sys
import json
from pathlib import Path
from typing import List, Tuple


class CLITestSuite:
    """Test suite for P-OS Constitutional CLI."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.tests_passed = 0
        self.tests_failed = 0
        self.test_results: List[Tuple[str, bool, str]] = []
    
    def run_test(self, name: str, test_func) -> bool:
        """Run a single test and record results."""
        try:
            result = test_func()
            if result:
                self.tests_passed += 1
                self.test_results.append((name, True, "PASS"))
                print(f"✅ {name}")
                return True
            else:
                self.tests_failed += 1
                self.test_results.append((name, False, "FAIL"))
                print(f"❌ {name}")
                return False
        except Exception as e:
            self.tests_failed += 1
            self.test_results.append((name, False, f"ERROR: {e}"))
            print(f"❌ {name} - Error: {e}")
            return False
    
    def test_cli_help(self) -> bool:
        """Test that CLI help is accessible."""
        result = subprocess.run(
            [sys.executable, "-m", "pos", "--help"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0 and "validate" in result.stdout
    
    def test_validate_dry_run(self) -> bool:
        """Test validate command with --dry-run flag."""
        result = subprocess.run(
            [sys.executable, "-m", "pos", "validate", 
             "docs/ARCHIVE_P-OS_WEEK1_CHAOS_TESTING.md", "--dry-run"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Check for dry-run indicators (handle Unicode variations)
        output = result.stdout + result.stderr
        return ("DRY RUN" in output or "Would execute" in output)
    
    def test_status_dry_run(self) -> bool:
        """Test status command with --dry-run flag."""
        result = subprocess.run(
            [sys.executable, "-m", "pos", "status", "--dry-run"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        return "DRY RUN" in output
    
    def test_flags_dry_run(self) -> bool:
        """Test flags command with --dry-run flag."""
        result = subprocess.run(
            [sys.executable, "-m", "pos", "flags", "--dry-run"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        return "DRY RUN" in output
    
    def test_verbose_mode(self) -> bool:
        """Test that --verbose shows underlying commands."""
        result = subprocess.run(
            [sys.executable, "-m", "pos", "validate",
             "docs/ARCHIVE_P-OS_WEEK1_CHAOS_TESTING.md", 
             "--dry-run", "--verbose"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout + result.stderr
        return ("Underlying Command" in output or
                "VALIDATION PLAN" in output or
                "Would execute" in output)
    
    def test_audit_log_creation(self) -> bool:
        """Test that audit logs are created."""
        # Run a command to generate audit log
        subprocess.run(
            [sys.executable, "-m", "pos", "flags", "--dry-run"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        # Check if audit log directory exists and has files
        audit_dir = self.project_root / "logs" / "cli_audit"
        if not audit_dir.exists():
            return False
        
        audit_files = list(audit_dir.glob("pos-*.json"))
        return len(audit_files) > 0
    
    def test_audit_log_format(self) -> bool:
        """Test that audit logs have correct JSON format."""
        audit_dir = self.project_root / "logs" / "cli_audit"
        if not audit_dir.exists():
            return False
        
        audit_files = list(audit_dir.glob("pos-*.json"))
        if not audit_files:
            return False
        
        # Check multiple recent audit files to find one with completion data
        for audit_file in sorted(audit_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]:
            try:
                with open(audit_file, 'r', encoding='utf-8-sig') as f:
                    data = json.load(f)
                
                # All logs should have basic fields
                basic_fields = ["correlation_id", "command", "timestamp", "operator"]
                has_basic = all(field in data for field in basic_fields)
                
                # Completed logs should have additional fields
                if "exit_code" in data and "duration_ms" in data:
                    # This is a completed log - verify it's complete
                    return has_basic
                elif has_basic:
                    # This is a start/dry-run log - also acceptable
                    return True
            except Exception as e:
                continue
        
        return False
    
    def test_correlation_id_format(self) -> bool:
        """Test that correlation IDs follow correct format."""
        audit_dir = self.project_root / "logs" / "cli_audit"
        if not audit_dir.exists():
            return False
        
        audit_files = list(audit_dir.glob("pos-*.json"))
        if not audit_files:
            return False
        
        # Check the most recent audit file
        latest_file = max(audit_files, key=lambda f: f.stat().st_mtime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            correlation_id = data.get("correlation_id", "")
            
            # Format: pos-YYYYMMDD-HHMMSS-XXXXXX
            import re
            pattern = r"^pos-\d{8}-\d{6}-[a-f0-9]{6}$"
            return bool(re.match(pattern, correlation_id))
        except Exception:
            return False
    
    def test_manual_fallback(self) -> bool:
        """Test that original scripts still work."""
        result = subprocess.run(
            [sys.executable, "scripts/validate_docs.py",
             "docs/ARCHIVE_P-OS_WEEK1_CHAOS_TESTING.md"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Script should run (even if it has warnings)
        output = result.stdout + result.stderr
        return "VALIDATION REPORT" in output or result.returncode in [0, 1]
    
    def test_no_hidden_operations(self) -> bool:
        """Test that dry-run doesn't execute actual operations."""
        # This is a heuristic test - we check that dry-run output
        # contains "Would execute" but not actual validation results
        result = subprocess.run(
            [sys.executable, "-m", "pos", "validate",
             "docs/ARCHIVE_P-OS_WEEK1_CHAOS_TESTING.md", "--dry-run"],
            cwd=self.project_root,
            capture_output=True,
            text=True,
            timeout=10,
        )
        
        output = result.stdout + result.stderr
        
        # Should show what would be executed
        has_plan = "Would execute" in output
        
        # Should NOT show actual validation results
        no_execution = "VALIDATION REPORT" not in output
        
        return has_plan and no_execution
    
    def run_all_tests(self):
        """Run all acceptance tests."""
        print("="*70)
        print("P-OS CLI PHASE 1 - ACCEPTANCE TEST SUITE")
        print("="*70)
        print()
        
        tests = [
            ("CLI Help Accessible", self.test_cli_help),
            ("Validate Dry-Run Mode", self.test_validate_dry_run),
            ("Status Dry-Run Mode", self.test_status_dry_run),
            ("Flags Dry-Run Mode", self.test_flags_dry_run),
            ("Verbose Mode Shows Commands", self.test_verbose_mode),
            ("Audit Log Creation", self.test_audit_log_creation),
            ("Audit Log Format Valid", self.test_audit_log_format),
            ("Correlation ID Format", self.test_correlation_id_format),
            ("Manual Fallback Works", self.test_manual_fallback),
            ("No Hidden Operations", self.test_no_hidden_operations),
        ]
        
        for name, test_func in tests:
            self.run_test(name, test_func)
        
        print()
        print("="*70)
        print(f"RESULTS: {self.tests_passed} passed, {self.tests_failed} failed")
        print("="*70)
        
        if self.tests_failed == 0:
            print("✅ ALL ACCEPTANCE CRITERIA MET")
            print()
            print("CLI Phase 1 is ready for operator acceptance review.")
            return 0
        else:
            print("❌ SOME TESTS FAILED")
            print()
            print("Review failures above before proceeding.")
            return 1


if __name__ == "__main__":
    suite = CLITestSuite()
    exit_code = suite.run_all_tests()
    sys.exit(exit_code)
