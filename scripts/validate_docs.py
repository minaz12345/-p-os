#!/usr/bin/env python3
"""
P-OS Executable Markdown Validator - Level 5 Compliance

Purpose: Validates P-OS documentation against Executable Markdown Level 5 standards
to ensure constitutional compliance (R6) and forensic integrity (R3).

Usage:
    python scripts/validate_docs.py <document_path> [--strict]
    
Examples:
    python scripts/validate_docs.py docs/ARCHIVE_P-OS_WEEK1_CHAOS_TESTING.md
    python scripts/validate_docs.py docs/ARCHIVE_P-OS_WEEK1_CHAOS_TESTING.md --strict
"""

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ExecutableMarkdownValidator:
    """Validates P-OS documents against Executable Markdown Level 5 standards."""
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.metadata: Dict = {}
        
    def validate_file(self, file_path: str) -> bool:
        """Validate a single markdown file."""
        path = Path(file_path)
        
        if not path.exists():
            self.errors.append(f"File not found: {file_path}")
            return False
        
        content = path.read_text(encoding='utf-8')
        
        # Run all validations
        self._validate_yaml_frontmatter(content, path.name)
        self._validate_classification(content)
        self._validate_immutable_markers(content)
        self._validate_metadata_completeness(content)
        self._validate_hash_integrity(content, path)
        
        # Report results
        self._print_results(file_path)
        
        return len(self.errors) == 0
    
    def _validate_yaml_frontmatter(self, content: str, filename: str):
        """Validate YAML frontmatter structure."""
        # Check for YAML frontmatter delimiters
        if not content.startswith('---'):
            self.errors.append("Missing YAML frontmatter opening delimiter (---)")
            return
        
        # Extract frontmatter
        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not match:
            self.errors.append("Invalid YAML frontmatter structure")
            return
        
        frontmatter = match.group(1)
        
        # Required fields for Level 5
        required_fields = [
            'document_id:',
            'schema_version:',
            'status:',
            'owner:',
            'approved_by:',
            'next_review:',
        ]
        
        for field in required_fields:
            if field not in frontmatter:
                if self.strict_mode:
                    self.errors.append(f"Missing required field: {field.rstrip(':')}")
                else:
                    self.warnings.append(f"Missing recommended field: {field.rstrip(':')}")
        
        # Validate schema version
        if 'executable-markdown-level-5' not in frontmatter:
            self.errors.append("Schema version must be 'executable-markdown-level-5'")
        
        # Extract metadata for further validation
        self._parse_metadata(frontmatter)
    
    def _parse_metadata(self, frontmatter: str):
        """Parse YAML frontmatter into dictionary."""
        for line in frontmatter.split('\n'):
            if ':' in line and not line.strip().startswith('#'):
                key, _, value = line.partition(':')
                self.metadata[key.strip()] = value.strip()
    
    def _validate_classification(self, content: str):
        """Validate document classification."""
        if '**Klasyfikacja:**' not in content and '**Classification:**' not in content:
            if self.strict_mode:
                self.errors.append("Missing document classification")
            else:
                self.warnings.append("Document classification not found")
    
    def _validate_immutable_markers(self, content: str):
        """Validate immutable status markers."""
        if 'CERTIFIED_IMMUTABLE' not in content and 'NIEMODYFIKOWALNY' not in content:
            if self.strict_mode:
                self.errors.append("Missing immutable status marker")
            else:
                self.warnings.append("Immutable status not explicitly marked")
    
    def _validate_metadata_completeness(self, content: str):
        """Validate metadata completeness."""
        required_contacts = ['ops@milejczyce.gov.pl']
        
        for contact in required_contacts:
            if contact not in content:
                self.warnings.append(f"Recommended contact missing: {contact}")
    
    def _validate_hash_integrity(self, content: str, path: Path):
        """Validate document hash integrity."""
        # Calculate SHA-256 hash
        file_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Check if hash is documented in file
        if f'sha256:{file_hash}' not in content and file_hash[:16] not in content:
            self.warnings.append(f"Document hash not embedded: sha256:{file_hash[:16]}...")
        
        # Store hash for audit trail
        self.metadata['computed_hash'] = f"sha256:{file_hash}"
    
    def _print_results(self, file_path: str):
        """Print validation results."""
        print("\n" + "="*70)
        print(f"P-OS EXECUTABLE MARKDOWN VALIDATION REPORT")
        print("="*70)
        print(f"File: {file_path}")
        print(f"Mode: {'STRICT' if self.strict_mode else 'STANDARD'}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
        print("-"*70)
        
        if self.metadata:
            print("\nMetadata:")
            for key, value in self.metadata.items():
                print(f"  {key}: {value}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        print("\n" + "-"*70)
        if not self.errors and not self.warnings:
            print("✅ VALIDATION PASSED - No issues found")
            print("="*70)
        elif not self.errors:
            print(f"⚠️  VALIDATION PASSED WITH WARNINGS - {len(self.warnings)} warnings")
            print("="*70)
        else:
            print(f"❌ VALIDATION FAILED - {len(self.errors)} errors found")
            print("="*70)
        
        print()


def main():
    parser = argparse.ArgumentParser(
        description='P-OS Executable Markdown Validator - Level 5 Compliance'
    )
    parser.add_argument(
        'file',
        help='Path to markdown file to validate'
    )
    parser.add_argument(
        '--strict',
        action='store_true',
        help='Enable strict validation mode (warnings become errors)'
    )
    
    args = parser.parse_args()
    
    validator = ExecutableMarkdownValidator(strict_mode=args.strict)
    success = validator.validate_file(args.file)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
