"""
P-OS v7.5 - Hash Chain Integrity Verification (R5 Compliance)

Provides SHA-256 hash chain validation for observation logs
and critical system artifacts.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class HashChainVerifier:
    """Manages SHA-256 hash chain for constitutional audit integrity."""
    
    def __init__(self, project_root: Path = None):
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.hash_chain_dir = self.project_root / "logs" / "hash_chain"
        self.observation_log = self.project_root / "pos" / "OBSERVATION_LOG.jsonl"
        
        # Ensure hash chain directory exists
        self.hash_chain_dir.mkdir(parents=True, exist_ok=True)
    
    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256_hash = hashlib.sha256()
        
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        return sha256_hash.hexdigest()
    
    def record_daily_hash(self, date: str = None) -> dict:
        """Record daily hash of observation log."""
        if date is None:
            date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        if not self.observation_log.exists():
            return {
                "status": "ERROR",
                "message": "Observation log not found",
                "path": str(self.observation_log)
            }
        
        file_hash = self.compute_file_hash(self.observation_log)
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        
        hash_record = {
            "date": date,
            "timestamp": timestamp,
            "file": str(self.observation_log),
            "algorithm": "SHA-256",
            "hash": file_hash,
            "file_size_bytes": self.observation_log.stat().st_size
        }
        
        # Save individual day hash file
        hash_file = self.hash_chain_dir / f"DAY_{date.replace('-', '')}.sha256"
        with open(hash_file, "w", encoding="utf-8") as f:
            json.dump(hash_record, f, indent=2, ensure_ascii=False)
        
        # Append to master chain log
        chain_log = self.hash_chain_dir / "HASH_CHAIN.jsonl"
        with open(chain_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(hash_record, ensure_ascii=False) + "\n")
        
        return {
            "status": "SUCCESS",
            "hash": file_hash,
            "hash_file": str(hash_file),
            "chain_log": str(chain_log)
        }
    
    def verify_chain_integrity(self) -> dict:
        """Verify integrity of entire hash chain."""
        chain_log = self.hash_chain_dir / "HASH_CHAIN.jsonl"
        
        if not chain_log.exists():
            return {
                "status": "ERROR",
                "message": "Hash chain log not found",
                "verified": False
            }
        
        verified_count = 0
        failed_count = 0
        failures = []
        
        with open(chain_log, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    record = json.loads(line.strip())
                    file_path = Path(record["file"])
                    
                    if file_path.exists():
                        current_hash = self.compute_file_hash(file_path)
                        if current_hash == record["hash"]:
                            verified_count += 1
                        else:
                            failed_count += 1
                            failures.append({
                                "line": line_num,
                                "date": record.get("date"),
                                "expected": record["hash"],
                                "actual": current_hash
                            })
                    else:
                        failed_count += 1
                        failures.append({
                            "line": line_num,
                            "date": record.get("date"),
                            "error": "File not found"
                        })
                except Exception as e:
                    failed_count += 1
                    failures.append({
                        "line": line_num,
                        "error": str(e)
                    })
        
        total = verified_count + failed_count
        return {
            "status": "PASS" if failed_count == 0 else "FAIL",
            "verified_count": verified_count,
            "failed_count": failed_count,
            "total_records": total,
            "failures": failures,
            "integrity_percentage": round((verified_count / total) * 100, 2) if total > 0 else 0
        }
