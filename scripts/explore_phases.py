#!/usr/bin/env python3
"""
Quick exploration of relationship phases
Shows key patterns without interpretation
"""

import pandas as pd
from pathlib import Path

phases_path = Path("data/forensic_export/timeline/relationship_phases.csv")

if not phases_path.exists():
    print("[ERROR] Run ETAP 2 first: python scripts/detect_relationship_phases.py")
    exit(1)

phases = pd.read_csv(phases_path)

print("=" * 80)
print("RELATIONSHIP PHASES EXPLORATION")
print("=" * 80)

# Phase distribution
print("\n1. PHASE DISTRIBUTION:")
print(phases["phase_type"].value_counts())

# Most intense weeks
print("\n2. TOP 10 MOST INTENSE WEEKS:")
print(phases.sort_values("total_messages", ascending=False).head(10)[
    ["week", "phase_type", "total_messages", "pawel_messages", 
     "kasia_messages", "dominant_sender"]
].to_string(index=False))

# Longest silences
print("\n3. TOP 10 LONGEST SILENCES:")
print(phases.sort_values("max_gap_days", ascending=False).head(10)[
    ["week", "phase_type", "max_gap_days", "total_messages", "active_days"]
].to_string(index=False))

# Dominance shifts
print("\n4. DOMINANCE PATTERN:")
for _, row in phases.iterrows():
    marker = "→" if row["dominant_sender"] != "balanced" else "="
    print(f"{row['week']}: {marker} {row['dominant_sender']} ({row['total_messages']} msgs)")
