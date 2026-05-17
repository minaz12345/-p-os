#!/usr/bin/env python3
"""
Context Buffer Monitor & Auto-Cleanup System

Monitors context buffer usage and triggers cleanup when 80% threshold is reached.
Prevents memory bloat from accumulated temporary files and cached data.

Usage:
    python scripts/context_buffer_monitor.py [--auto-clean] [--threshold 80]
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


class ContextBufferMonitor:
    """Monitor and manage context buffer usage"""
    
    def __init__(self, base_dir: Path = None, threshold_percent: float = 80.0):
        self.base_dir = base_dir or project_root
        self.threshold_percent = threshold_percent
        self.temp_dirs = [
            self.base_dir / "data" / "temp",
            self.base_dir / "__pycache__",
        ]
        self.cache_patterns = ["*.pyc", "*.pyo", "*~", ".DS_Store"]
        self.monitor_log = self.base_dir / "logs" / "context_buffer_monitor.jsonl"
        
    def calculate_buffer_usage(self) -> dict:
        """Calculate current buffer/cache usage"""
        
        total_size = 0
        file_count = 0
        breakdown = {}
        
        # Check temp directories
        for temp_dir in self.temp_dirs:
            if temp_dir.exists():
                dir_size = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                dir_files = len(list(temp_dir.rglob('*')))
                breakdown[str(temp_dir.relative_to(self.base_dir))] = {
                    "size_mb": round(dir_size / (1024 * 1024), 2),
                    "file_count": dir_files
                }
                total_size += dir_size
                file_count += dir_files
        
        # Check for large log files
        logs_dir = self.base_dir / "logs"
        if logs_dir.exists():
            log_files = [f for f in logs_dir.iterdir() if f.is_file() and f.suffix == '.log']
            log_size = sum(f.stat().st_size for f in log_files)
            breakdown["logs/*.log"] = {
                "size_mb": round(log_size / (1024 * 1024), 2),
                "file_count": len(log_files)
            }
            total_size += log_size
            file_count += len(log_files)
        
        # Estimate context buffer capacity (e.g., 500 MB)
        estimated_capacity_mb = 500
        usage_percent = (total_size / (estimated_capacity_mb * 1024 * 1024)) * 100
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_files": file_count,
            "usage_percent": round(usage_percent, 2),
            "threshold_percent": self.threshold_percent,
            "exceeds_threshold": usage_percent > self.threshold_percent,
            "breakdown": breakdown
        }
    
    def log_status(self, status: dict):
        """Log buffer status to monitor log"""
        
        self.monitor_log.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.monitor_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(status) + '\n')
    
    def auto_cleanup(self, dry_run: bool = False) -> dict:
        """Perform automatic cleanup of temporary files"""
        
        print("=" * 80)
        print("CONTEXT BUFFER AUTO-CLEANUP")
        print("=" * 80)
        
        cleaned = {
            "files_removed": 0,
            "space_freed_mb": 0,
            "dirs_cleaned": [],
            "errors": []
        }
        
        # Clean temp directories
        for temp_dir in self.temp_dirs:
            if not temp_dir.exists():
                continue
            
            print(f"\n[CLEANING] {temp_dir.relative_to(self.base_dir)}...")
            
            try:
                if dry_run:
                    file_count = len(list(temp_dir.rglob('*')))
                    dir_size = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                    print(f"   Would remove {file_count} files ({dir_size / (1024*1024):.2f} MB)")
                    cleaned["files_removed"] += file_count
                    cleaned["space_freed_mb"] += round(dir_size / (1024*1024), 2)
                else:
                    # Remove all files in temp directory
                    for item in temp_dir.rglob('*'):
                        if item.is_file():
                            item.unlink()
                            cleaned["files_removed"] += 1
                    
                    # Remove empty directories
                    for item in sorted(temp_dir.rglob('*'), reverse=True):
                        if item.is_dir():
                            try:
                                item.rmdir()
                            except OSError:
                                pass  # Directory not empty
                    
                    dir_size_after = sum(f.stat().st_size for f in temp_dir.rglob('*') if f.is_file())
                    cleaned["dirs_cleaned"].append(str(temp_dir.relative_to(self.base_dir)))
                    print(f"   ✓ Cleaned {temp_dir.relative_to(self.base_dir)}")
                    
            except Exception as e:
                error_msg = f"Error cleaning {temp_dir}: {str(e)}"
                cleaned["errors"].append(error_msg)
                print(f"   ✗ {error_msg}")
        
        # Clean Python cache files
        print("\n[CLEANING] Python cache files (*.pyc, *.pyo)...")
        pycache_dirs = list(self.base_dir.rglob("__pycache__"))
        
        for pycache_dir in pycache_dirs:
            try:
                if dry_run:
                    file_count = len(list(pycache_dir.rglob('*.pyc')))
                    print(f"   Would remove {file_count} .pyc files from {pycache_dir.relative_to(self.base_dir)}")
                    cleaned["files_removed"] += file_count
                else:
                    shutil.rmtree(pycache_dir)
                    cleaned["dirs_cleaned"].append(str(pycache_dir.relative_to(self.base_dir)))
            except Exception as e:
                cleaned["errors"].append(f"Error removing {pycache_dir}: {str(e)}")
        
        # Clean old log files (older than 30 days)
        print("\n[CLEANING] Old log files (>30 days)...")
        logs_dir = self.base_dir / "logs"
        if logs_dir.exists():
            cutoff_date = datetime.now() - timedelta(days=30)
            
            for log_file in logs_dir.iterdir():
                if log_file.is_file() and log_file.suffix == '.log':
                    file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        try:
                            if dry_run:
                                file_size_mb = log_file.stat().st_size / (1024*1024)
                                print(f"   Would remove {log_file.name} ({file_size_mb:.2f} MB, {file_mtime.strftime('%Y-%m-%d')})")
                                cleaned["space_freed_mb"] += round(file_size_mb, 2)
                            else:
                                log_file.unlink()
                                cleaned["files_removed"] += 1
                                cleaned["space_freed_mb"] += round(log_file.stat().st_size / (1024*1024), 2)
                        except Exception as e:
                            cleaned["errors"].append(f"Error removing {log_file}: {str(e)}")
        
        # Summary
        print("\n" + "=" * 80)
        print("CLEANUP SUMMARY")
        print("=" * 80)
        print(f"Files removed: {cleaned['files_removed']}")
        print(f"Space freed: {cleaned['space_freed_mb']:.2f} MB")
        print(f"Directories cleaned: {len(cleaned['dirs_cleaned'])}")
        
        if cleaned['errors']:
            print(f"\n⚠️  Errors encountered: {len(cleaned['errors'])}")
            for error in cleaned['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
        
        if dry_run:
            print("\nℹ️  DRY RUN MODE - No files were actually removed")
        
        return cleaned
    
    def check_and_cleanup(self, auto_clean: bool = False) -> dict:
        """Check buffer usage and optionally trigger cleanup"""
        
        # Calculate current usage
        status = self.calculate_buffer_usage()
        
        # Log status
        self.log_status(status)
        
        # Print status
        print("=" * 80)
        print("CONTEXT BUFFER STATUS")
        print("=" * 80)
        print(f"Total size: {status['total_size_mb']:.2f} MB")
        print(f"Total files: {status['total_files']}")
        print(f"Usage: {status['usage_percent']:.2f}% / {status['threshold_percent']:.0f}% threshold")
        
        if status['exceeds_threshold']:
            print(f"\n⚠️  WARNING: Buffer usage EXCEEDS {status['threshold_percent']:.0f}% threshold!")
            
            if auto_clean:
                print("\n[AUTO-CLEAN] Triggering automatic cleanup...")
                cleanup_result = self.auto_cleanup(dry_run=False)
                
                # Recalculate after cleanup
                new_status = self.calculate_buffer_usage()
                print(f"\n✅ After cleanup: {new_status['usage_percent']:.2f}% usage")
                
                return {
                    "status": status,
                    "cleanup_performed": True,
                    "cleanup_result": cleanup_result,
                    "new_status": new_status
                }
            else:
                print("\n💡 Run with --auto-clean flag to perform automatic cleanup")
                return {
                    "status": status,
                    "cleanup_performed": False,
                    "recommendation": "Run: python scripts/context_buffer_monitor.py --auto-clean"
                }
        else:
            print(f"\n✅ Buffer usage OK ({status['usage_percent']:.2f}% < {status['threshold_percent']:.0f}%)")
            return {
                "status": status,
                "cleanup_performed": False
            }


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Context Buffer Monitor & Auto-Cleanup")
    parser.add_argument("--auto-clean", action="store_true", help="Automatically clean when threshold exceeded")
    parser.add_argument("--threshold", type=float, default=80.0, help="Usage threshold percentage (default: 80)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be cleaned without actually removing files")
    
    args = parser.parse_args()
    
    monitor = ContextBufferMonitor(threshold_percent=args.threshold)
    
    if args.dry_run:
        print("[DRY RUN MODE] Showing what would be cleaned...\n")
        result = monitor.auto_cleanup(dry_run=True)
    else:
        result = monitor.check_and_cleanup(auto_clean=args.auto_clean)
    
    # Exit with appropriate code
    if result.get("status", {}).get("exceeds_threshold", False) and not result.get("cleanup_performed", False):
        sys.exit(1)  # Threshold exceeded, cleanup needed
    else:
        sys.exit(0)  # All good


if __name__ == "__main__":
    main()
