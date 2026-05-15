"""Tests for R5 Hash Chain Integrity Verification."""

import pytest
from pathlib import Path
import sys
import os

# Ensure project root is in path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.observability.hash_chain import HashChainVerifier


class TestHashChainVerifier:
    
    def test_compute_file_hash_deterministic(self, tmp_path):
        """Hash computation must be deterministic (R2 compliance)."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content for hashing")
        
        verifier = HashChainVerifier(tmp_path)
        hash1 = verifier.compute_file_hash(test_file)
        hash2 = verifier.compute_file_hash(test_file)
        
        assert hash1 == hash2, "Hash must be deterministic"
        assert len(hash1) == 64, "SHA-256 produces 64-character hex string"
    
    def test_record_daily_hash_creates_files(self, tmp_path):
        """Daily hash recording creates expected files."""
        obs_log = tmp_path / "pos" / "OBSERVATION_LOG.jsonl"
        obs_log.parent.mkdir(parents=True)
        obs_log.write_text('{"test": "data"}\n')
        
        verifier = HashChainVerifier(tmp_path)
        result = verifier.record_daily_hash("2026-05-13")
        
        assert result["status"] == "SUCCESS"
        assert Path(result["hash_file"]).exists()
        assert (tmp_path / "logs" / "hash_chain" / "HASH_CHAIN.jsonl").exists()
    
    def test_verify_chain_integrity_valid(self, tmp_path):
        """Chain verification passes for unmodified files."""
        obs_log = tmp_path / "pos" / "OBSERVATION_LOG.jsonl"
        obs_log.parent.mkdir(parents=True)
        obs_log.write_text('{"test": "data"}\n')
        
        verifier = HashChainVerifier(tmp_path)
        verifier.record_daily_hash("2026-05-13")
        
        result = verifier.verify_chain_integrity()
        
        assert result["status"] == "PASS"
        assert result["integrity_percentage"] == 100.0
