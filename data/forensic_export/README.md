# Forensic Relationship Export Package v1.0

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
