#!/usr/bin/env python3
"""
ETAP 2: RELATIONSHIP PHASE DETECTION
Classify relationship phases by week using activity metrics

Phase types:
- HIGH_INTENSITY: >=300 messages/week
- STABLE_CONTACT: 80-299 messages/week
- LOW_CONTACT: 20-79 messages/week
- WEAK_CONTACT: <20 messages, <=2 active days
- SILENCE: >=30 days max gap AND <=5 messages
- REACTIVATION: (detected after silence)
- DECLINE: (trend detection in ETAP 3)

Output: data/forensic_export/timeline/relationship_phases.csv
"""

from pathlib import Path
import pandas as pd
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

INPUT = project_root / "data" / "forensic_export" / "raw" / "messages.jsonl"
OUT_DIR = project_root / "data" / "forensic_export" / "timeline"
OUTPUT = OUT_DIR / "relationship_phases.csv"


def classify_phase(row):
    """
    Classify relationship phase based on weekly metrics
    
    Priority order:
    1. SILENCE (long gaps + very low activity)
    2. HIGH_INTENSITY (very high volume)
    3. STABLE_CONTACT (moderate-high volume)
    4. LOW_CONTACT (low volume)
    5. WEAK_CONTACT (minimal activity)
    """
    messages = row["total_messages"]
    max_silence = row["max_gap_days"]
    active_days = row["active_days"]
    
    # Silence: long gap AND minimal activity
    if max_silence >= 30 and messages <= 5:
        return "SILENCE"
    
    # High intensity: very active period
    if messages >= 300:
        return "HIGH_INTENSITY"
    
    # Stable contact: regular communication
    if messages >= 80:
        return "STABLE_CONTACT"
    
    # Weak contact: barely active
    if active_days <= 2 and messages < 20:
        return "WEAK_CONTACT"
    
    # Low contact: some activity but not regular
    if messages >= 20:
        return "LOW_CONTACT"
    
    # Default fallback
    return "LOW_CONTACT"


def main():
    """Main phase detection"""
    
    print("=" * 80)
    print("ETAP 2: RELATIONSHIP PHASE DETECTION")
    print("Classifying weekly relationship phases")
    print("=" * 80)
    
    if not INPUT.exists():
        print(f"[ERROR] Input file not found: {INPUT}")
        print("Run ETAP 1 first: python scripts/forensic_export_raw.py")
        sys.exit(1)
    
    # Create output directory
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load raw data
        print(f"\n[LOAD] Reading: {INPUT}")
        df = pd.read_json(INPUT, lines=True)
        print(f"[OK] Loaded {len(df)} messages")
        
        # Parse timestamps
        print("\n[PROCESS] Parsing timestamps and extracting temporal features...")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        
        # Extract date components
        df["date"] = df["timestamp"].dt.date
        df["week"] = df["timestamp"].dt.to_period("W").astype(str)
        df["month"] = df["timestamp"].dt.to_period("M").astype(str)
        
        # Ensure text fields
        df["text"] = df["text"].fillna("")
        df["message_length"] = df["text"].str.len()
        
        # Media detection
        if "has_media" not in df.columns:
            df["has_media"] = False
        
        # Calculate gaps between consecutive messages
        print("[PROCESS] Calculating inter-message gaps...")
        df["previous_timestamp"] = df["timestamp"].shift(1)
        df["gap_days"] = (
            (df["timestamp"] - df["previous_timestamp"])
            .dt.total_seconds()
            .div(60 * 60 * 24)
        )
        
        print(f"[OK] Calculated {df['gap_days'].notna().sum()} gaps")
        
        # Weekly aggregation
        print("\n[ANALYSIS] Aggregating weekly metrics...")
        weekly = df.groupby("week").agg(
            start_timestamp=("timestamp", "min"),
            end_timestamp=("timestamp", "max"),
            total_messages=("message_id", "count"),
            total_chars=("message_length", "sum"),
            avg_message_length=("message_length", "mean"),
            active_days=("date", "nunique"),
            media_count=("has_media", "sum"),
            max_gap_days=("gap_days", "max"),
        ).reset_index()
        
        print(f"[OK] Created {len(weekly)} weekly windows")
        
        # Per-sender counts per week
        print("[ANALYSIS] Calculating per-sender weekly distribution...")
        sender_counts = (
            df.groupby(["week", "sender"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        
        weekly = weekly.merge(sender_counts, on="week", how="left")
        
        # Ensure both senders exist in columns
        for col in ["Pawel Nazaruk", "Kasia Ju"]:
            if col not in weekly.columns:
                weekly[col] = 0
        
        weekly["pawel_messages"] = weekly["Pawel Nazaruk"]
        weekly["kasia_messages"] = weekly["Kasia Ju"]
        
        # Determine dominant sender each week
        weekly["dominant_sender"] = weekly.apply(
            lambda r: "Pawel Nazaruk"
            if r["pawel_messages"] > r["kasia_messages"]
            else "Kasia Ju"
            if r["kasia_messages"] > r["pawel_messages"]
            else "balanced",
            axis=1
        )
        
        # Calculate share percentages
        weekly["pawel_share_percent"] = (
            weekly["pawel_messages"] / weekly["total_messages"] * 100
        ).round(2)
        
        weekly["kasia_share_percent"] = (
            weekly["kasia_messages"] / weekly["total_messages"] * 100
        ).round(2)
        
        # Average daily messages
        weekly["avg_daily_messages"] = (
            weekly["total_messages"] / weekly["active_days"]
        ).round(2)
        
        # Classify phases
        print("[ANALYSIS] Classifying relationship phases...")
        weekly["phase_type"] = weekly.apply(classify_phase, axis=1)
        
        # Select and order final columns
        weekly = weekly[[
            "week",
            "start_timestamp",
            "end_timestamp",
            "phase_type",
            "total_messages",
            "pawel_messages",
            "kasia_messages",
            "pawel_share_percent",
            "kasia_share_percent",
            "dominant_sender",
            "active_days",
            "avg_daily_messages",
            "avg_message_length",
            "media_count",
            "max_gap_days",
        ]]
        
        # Save to CSV
        weekly.to_csv(OUTPUT, index=False, encoding="utf-8")
        
        print(f"\n[SAVED] Output: {OUTPUT}")
        
        # Display phase distribution
        print("\n" + "=" * 80)
        print("PHASE DISTRIBUTION")
        print("=" * 80)
        phase_counts = weekly["phase_type"].value_counts()
        print(phase_counts)
        
        # Show most intense weeks
        print("\n" + "=" * 80)
        print("TOP 10 MOST INTENSE WEEKS")
        print("=" * 80)
        top_intensity = weekly.sort_values("total_messages", ascending=False).head(10)
        print(top_intensity[["week", "phase_type", "total_messages", "pawel_messages", 
                            "kasia_messages", "dominant_sender"]].to_string(index=False))
        
        # Show longest silences
        print("\n" + "=" * 80)
        print("TOP 10 LONGEST SILENCES")
        print("=" * 80)
        top_silence = weekly.sort_values("max_gap_days", ascending=False).head(10)
        print(top_silence[["week", "phase_type", "max_gap_days", "total_messages", 
                          "active_days"]].to_string(index=False))
        
        # Summary statistics
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total weeks analyzed: {len(weekly)}")
        print(f"Date range: {weekly['start_timestamp'].min()} → {weekly['end_timestamp'].max()}")
        print(f"\nPhase breakdown:")
        for phase, count in phase_counts.items():
            pct = count / len(weekly) * 100
            print(f"  • {phase}: {count} weeks ({pct:.1f}%)")
        
        print(f"\nDominant sender distribution:")
        dom_counts = weekly["dominant_sender"].value_counts()
        for sender, count in dom_counts.items():
            pct = count / len(weekly) * 100
            print(f"  • {sender}: {count} weeks ({pct:.1f}%)")
        
        print("\n" + "=" * 80)
        print("Next step: ETAP 3 — SEMANTIC EXTRACTION (keywords, themes, symbols)")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Phase detection failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
