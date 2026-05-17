#!/usr/bin/env python3
"""
Quick verification of ETAP 3 semantic extraction output
"""

import pandas as pd
from pathlib import Path

base = Path("data/forensic_export/semantic")

for name in [
    "keywords_by_phase.csv",
    "ngrams_by_phase.csv",
    "repeated_phrases.csv",
    "question_patterns.csv",
    "emotional_markers.csv",
    "named_entities_candidates.csv",
]:
    path = base / name
    if path.exists():
        df = pd.read_csv(path)
        print(f"\n{'='*80}")
        print(name)
        print(f"{'='*80}")
        print(df.head(10))
        print(f"\nTotal rows: {len(df)}")
    else:
        print(f"\n[MISSING] {name}")
