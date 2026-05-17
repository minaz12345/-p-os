#!/usr/bin/env python3
"""
ETAP 4: EXTERNAL ANALYSIS PACKAGE
Package forensic export with manifest, documentation, and version info

Creates:
- MANIFEST.json (file descriptions, schemas, timestamps)
- README.md (usage guide, example queries)
- VERSION.txt (data version, source hash, pipeline version)
- forensic_export_v1.0.zip (compressed archive)
"""

import json
import zipfile
from pathlib import Path
from datetime import datetime
import hashlib
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def calculate_file_hash(file_path: Path) -> str:
    """Calculate SHA256 hash of a file"""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file_size_kb(file_path: Path) -> float:
    """Get file size in KB"""
    return file_path.stat().st_size / 1024


def create_manifest(output_dir: Path):
    """Create MANIFEST.json with file metadata"""
    
    print("[PACKAGE] Creating MANIFEST.json...")
    
    manifest = {
        "package_name": "Forensic Relationship Export",
        "version": "1.0",
        "created_at": datetime.now().isoformat(),
        "description": "Complete forensic extraction of Facebook conversation data with phase-labeled timeline and semantic patterns",
        "architecture": "RAW DATA → METRICS → TIMELINE → SEMANTIC (strict separation)",
        "source_data": {
            "conversation_id": "kasiaju_1977350892357109",
            "participants": ["Kasia Ju", "Pawel Nazaruk"],
            "total_messages": 8779,
            "date_range": "2019-01-30 to 2022-05-14"
        },
        "pipeline_version": {
            "forensic_export_raw.py": "v1.0 (ASCII-safe encoding)",
            "analyze_relationship_raw.py": "v1.0",
            "detect_relationship_phases.py": "v1.0",
            "extract_semantic_patterns.py": "v1.0 (ASCII normalization)",
            "check_encoding_quality.py": "v1.0"
        },
        "files": {}
    }
    
    # Document each output directory
    directories = {
        "raw": {
            "description": "Raw forensic export - uninterpreted message data",
            "schema": {
                "message_id": "Unique message identifier (msg_000001 format)",
                "timestamp": "ISO 8601 timestamp",
                "date": "Date string (YYYY-MM-DD)",
                "sender": "Message sender name",
                "text": "Original message text (may contain Polish diacritics)",
                "text_ascii": "ASCII-safe version for analysis (Polish chars converted)",
                "text_clean": "Lowercase ASCII version for tokenization",
                "message_length": "Length of text_ascii in characters",
                "has_media": "Boolean - whether message contains media",
                "media_type": "Type of media (photo/video/gif/audio/file) or null",
                "reply_gap_minutes": "Minutes since previous message (null if same sender)",
                "conversation_day_index": "Days from conversation start (0, 1, 2, ...)"
            }
        },
        "metrics": {
            "description": "Basic relationship metrics per person",
            "columns": [
                "messages_count", "avg_message_length", "median_message_length",
                "media_share_percent", "avg_reply_gap_minutes", "median_reply_gap_minutes",
                "days_opened", "days_closed"
            ]
        },
        "timeline": {
            "description": "Phase-labeled weekly timeline",
            "phases": [
                "HIGH_INTENSITY (≥300 msgs/week)",
                "STABLE_CONTACT (80-299 msgs/week)",
                "LOW_CONTACT (20-79 msgs/week)",
                "WEAK_CONTACT (<20 msgs, ≤2 active days)",
                "SILENCE (≥30 day gap AND ≤5 msgs)"
            ]
        },
        "semantic": {
            "description": "Mechanical semantic extraction (no interpretation)",
            "files": {
                "keywords_by_phase.csv": "Top 100 keywords per phase × sender",
                "ngrams_by_phase.csv": "Bigrams + trigrams per phase × sender",
                "repeated_phrases.csv": "Exact phrases repeated ≥2 times",
                "question_patterns.csv": "All questions with metadata",
                "emotional_markers.csv": "Emotional marker hits (5 categories)",
                "named_entities_candidates.csv": "Capitalized words (people, places)",
                "semantic_summary_by_phase.json": "Phase-level aggregation"
            }
        }
    }
    
    # Scan actual files
    base_dir = project_root / "data" / "forensic_export"
    
    for dir_name, dir_info in directories.items():
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            continue
        
        manifest["files"][dir_name] = {
            "path": str(dir_path.relative_to(project_root)),
            "description": dir_info["description"],
            "contents": []
        }
        
        if "schema" in dir_info:
            manifest["files"][dir_name]["schema"] = dir_info["schema"]
        if "columns" in dir_info:
            manifest["files"][dir_name]["columns"] = dir_info["columns"]
        if "phases" in dir_info:
            manifest["files"][dir_name]["phases"] = dir_info["phases"]
        
        for file_path in sorted(dir_path.iterdir()):
            if file_path.is_file():
                file_entry = {
                    "filename": file_path.name,
                    "size_kb": round(get_file_size_kb(file_path), 1),
                    "hash_sha256": calculate_file_hash(file_path),
                    "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                }
                manifest["files"][dir_name]["contents"].append(file_entry)
    
    # Write manifest
    manifest_path = output_dir / "MANIFEST.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"   ✓ Created MANIFEST.json ({len(manifest['files'])} directories documented)")
    return manifest_path


def create_readme(output_dir: Path):
    """Create README.md with usage guide"""
    
    print("[PACKAGE] Creating README.md...")
    
    readme_content = """# Forensic Relationship Export Package v1.0

## Overview

This package contains a complete forensic extraction of Facebook conversation data between **Kasia Ju** and **Pawel Nazaruk** (2019-2022).

**Architecture**: RAW DATA → METRICS → TIMELINE → SEMANTIC (strict separation of data from interpretation)

---

## Directory Structure

```
forensic_export/
├── raw/              # Raw message data (8,779 messages)
├── metrics/          # Per-person relationship metrics
├── timeline/         # Phase-labeled weekly timeline
└── semantic/         # Mechanical semantic extraction
```

---

## Quick Start

### 1. Load Raw Messages (Python/pandas)

```python
import pandas as pd

df = pd.read_json("data/forensic_export/raw/messages.jsonl", lines=True)
print(f"Loaded {len(df)} messages")
print(df.head())
```

### 2. Analyze Relationship Metrics

```python
metrics = pd.read_csv("data/forensic_export/metrics/relationship_basic_metrics.csv")
print(metrics)
```

### 3. Explore Timeline Phases

```python
phases = pd.read_csv("data/forensic_export/timeline/relationship_phases.csv")
print(phases["phase_type"].value_counts())
```

### 4. Semantic Analysis by Phase

```python
keywords = pd.read_csv("data/forensic_export/semantic/keywords_by_phase.csv")
high_intensity_keywords = keywords[keywords["phase_type"] == "HIGH_INTENSITY"]
print(high_intensity_keywords.head(20))
```

---

## File Descriptions

### RAW (`data/forensic_export/raw/`)

| File | Format | Description |
|------|--------|-------------|
| `messages.jsonl` | JSONL | 8,779 messages (one JSON object per line) |
| `messages.csv` | CSV | Tabular format for Excel/pandas |
| `timeline_index.json` | JSON | Aggregate metadata |

**Key Fields**:
- `text`: Original message text (may contain Polish diacritics)
- `text_ascii`: ASCII-safe version for analysis (**use this for analysis**)
- `text_clean`: Lowercase ASCII for tokenization
- `reply_gap_minutes`: Time gap from previous message
- `conversation_day_index`: Days from conversation start

### METRICS (`data/forensic_export/metrics/`)

| File | Description |
|------|-------------|
| `relationship_basic_metrics.csv` | Per-person metrics (message count, avg length, reply gaps, etc.) |

### TIMELINE (`data/forensic_export/timeline/`)

| File | Description |
|------|-------------|
| `relationship_phases.csv` | 21 weekly windows with phase classification |

**Phase Types**:
- `HIGH_INTENSITY`: ≥300 messages/week
- `STABLE_CONTACT`: 80-299 messages/week
- `LOW_CONTACT`: 20-79 messages/week
- `WEAK_CONTACT`: <20 messages, ≤2 active days
- `SILENCE`: ≥30 day gap AND ≤5 messages

### SEMANTIC (`data/forensic_export/semantic/`)

| File | Rows | Description |
|------|------|-------------|
| `keywords_by_phase.csv` | 657 | Top 100 keywords per phase × sender |
| `ngrams_by_phase.csv` | 1,226 | Bigrams + trigrams per phase × sender |
| `repeated_phrases.csv` | 122 | Exact phrases repeated ≥2 times |
| `question_patterns.csv` | 762 | All questions with metadata |
| `emotional_markers.csv` | 1,624 | Emotional marker hits (5 categories) |
| `named_entities_candidates.csv` | 200 | Capitalized words (people, places) |
| `semantic_summary_by_phase.json` | - | Phase-level aggregation |

---

## Example Queries

### Find Most Intense Week

```python
phases = pd.read_csv("data/forensic_export/timeline/relationship_phases.csv")
most_intense = phases.loc[phases["total_messages"].idxmax()]
print(f"Week: {most_intense['week']}")
print(f"Messages: {most_intense['total_messages']}")
```

### Compare Sender Vocabulary

```python
keywords = pd.read_csv("data/forensic_export/semantic/keywords_by_phase.csv")

pawel_words = keywords[
    (keywords["phase_type"] == "HIGH_INTENSITY") & 
    (keywords["sender"] == "Pawel Nazaruk")
].head(10)

kasia_words = keywords[
    (keywords["phase_type"] == "HIGH_INTENSITY") & 
    (keywords["sender"] == "Kasia Ju")
].head(10)

print("Paweł top words:", pawel_words["word"].tolist())
print("Kasia top words:", kasia_words["word"].tolist())
```

### Analyze Question Patterns

```python
questions = pd.read_csv("data/forensic_export/semantic/question_patterns.csv")
print(f"Total questions: {len(questions)}")
print(questions["phase_type"].value_counts())
```

### Detect Ritual Language

```python
repeated = pd.read_csv("data/forensic_export/semantic/repeated_phrases.csv")
rituals = repeated[repeated["count"] >= 10]
print("Ritual phrases (≥10 occurrences):")
print(rituals)
```

---

## Encoding Note

**Important**: Use `text_ascii` or `text_clean` for analysis, NOT `text`.

- `text`: Original message text (may contain Polish diacritics or mojibake)
- `text_ascii`: ASCII-safe version (Polish chars converted: ą→a, ł→l, etc.)
- `text_clean`: Lowercase ASCII for tokenization

This ensures stable comparison across the dataset without encoding issues.

---

## Pipeline Scripts

All scripts are in `scripts/` directory:

1. `forensic_export_raw.py` - ETAP 1: Raw data extraction
2. `analyze_relationship_raw.py` - Basic metrics calculation
3. `detect_relationship_phases.py` - ETAP 2: Phase detection
4. `extract_semantic_patterns.py` - ETAP 3: Semantic extraction
5. `check_encoding_quality.py` - Encoding validation
6. `package_forensic_export.py` - ETAP 4: Packaging (this script)

**Re-run entire pipeline**:
```bash
python scripts/forensic_export_raw.py
python scripts/analyze_relationship_raw.py
python scripts/detect_relationship_phases.py
python scripts/extract_semantic_patterns.py
python scripts/check_encoding_quality.py
python scripts/package_forensic_export.py
```

---

## Version History

- **v1.0** (2026-05-17): Initial release with ASCII-safe encoding pipeline

---

## License

Internal use only. Contains personal conversation data.

---

## Contact

For questions about this dataset, refer to MANIFEST.json for technical details.
"""
    
    readme_path = output_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"   ✓ Created README.md")
    return readme_path


def create_version_file(output_dir: Path):
    """Create VERSION.txt with version info"""
    
    print("[PACKAGE] Creating VERSION.txt...")
    
    version_content = f"""Forensic Relationship Export Package
Version: 1.0
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Pipeline Version:
- forensic_export_raw.py: v1.0 (ASCII-safe encoding)
- analyze_relationship_raw.py: v1.0
- detect_relationship_phases.py: v1.0
- extract_semantic_patterns.py: v1.0 (ASCII normalization)
- check_encoding_quality.py: v1.0
- package_forensic_export.py: v1.0

Source Data:
- Conversation ID: kasiaju_1977350892357109
- Participants: Kasia Ju, Pawel Nazaruk
- Total Messages: 8,779
- Date Range: 2019-01-30 to 2022-05-14

Architecture:
RAW DATA → METRICS → TIMELINE → SEMANTIC
(strict separation of data from interpretation)

Encoding Principle:
Analytical layer = ASCII-safe
Polish diacritics converted: ą→a, ć→c, ę→e, ł→l, ń→n, ó→o, ś→s, ż→z, ź→z
"""
    
    version_path = output_dir / "VERSION.txt"
    with open(version_path, 'w', encoding='utf-8') as f:
        f.write(version_content)
    
    print(f"   ✓ Created VERSION.txt")
    return version_path


def create_archive(output_dir: Path, manifest_path: Path, readme_path: Path, version_path: Path):
    """Create compressed ZIP archive"""
    
    print("[PACKAGE] Creating forensic_export_v1.0.zip...")
    
    archive_path = output_dir / "forensic_export_v1.0.zip"
    base_dir = project_root / "data" / "forensic_export"
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add manifest, readme, version
        zipf.write(manifest_path, arcname="MANIFEST.json")
        zipf.write(readme_path, arcname="README.md")
        zipf.write(version_path, arcname="VERSION.txt")
        
        # Add all data files
        for dir_path in base_dir.rglob('*'):
            if dir_path.is_file():
                arcname = dir_path.relative_to(base_dir.parent)
                zipf.write(dir_path, arcname=str(arcname))
    
    archive_size_mb = archive_path.stat().st_size / (1024 * 1024)
    print(f"   ✓ Created archive: {archive_path.name} ({archive_size_mb:.1f} MB)")
    return archive_path


def main():
    """Main packaging pipeline"""
    
    print("=" * 80)
    print("ETAP 4: EXTERNAL ANALYSIS PACKAGE")
    print("Packaging forensic export with manifest and documentation")
    print("=" * 80)
    
    output_dir = project_root / "data" / "forensic_export"
    
    # Step 1: Create manifest
    manifest_path = create_manifest(output_dir)
    
    # Step 2: Create README
    readme_path = create_readme(output_dir)
    
    # Step 3: Create version file
    version_path = create_version_file(output_dir)
    
    # Step 4: Create archive
    archive_path = create_archive(output_dir, manifest_path, readme_path, version_path)
    
    # Final report
    print("\n" + "=" * 80)
    print("ETAP 4 COMPLETE: Package ready for external analysis")
    print("=" * 80)
    print(f"\nPackage location: {output_dir}")
    print(f"\nFiles created:")
    print(f"  • MANIFEST.json")
    print(f"  • README.md")
    print(f"  • VERSION.txt")
    print(f"  • forensic_export_v1.0.zip")
    print(f"\nReady for:")
    print(f"  - NotebookLM")
    print(f"  - Local LLM")
    print(f"  - Gephi / Cytoscape")
    print(f"  - Obsidian")
    print(f"  - PDF reports")
    print(f"  - External relational analysis")


if __name__ == "__main__":
    main()
