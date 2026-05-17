#!/usr/bin/env python3
"""
Analyze relationship using RAW DATA (pandas-based)
Calculates basic metrics WITHOUT interpretation

Metrics calculated:
- messages_count per person
- avg/median message length
- media share percentage
- avg/median reply gap
- days opened (who starts conversation)
- days closed (who ends conversation)
"""

import pandas as pd
from pathlib import Path
import sys
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

INPUT = project_root / "data" / "forensic_export" / "raw" / "messages.jsonl"
OUTPUT_DIR = project_root / "data" / "forensic_export" / "metrics"
OUTPUT = OUTPUT_DIR / "relationship_basic_metrics.csv"


def compute_per_person_metrics(messages: List[Dict]) -> pd.DataFrame:
    """
    Compute per-person relationship metrics from message list.
    
    Args:
        messages: List of enriched message dicts (from forensic_export_raw)
    
    Returns:
        DataFrame with columns: sender, messages_count, avg_message_length, etc.
    """
    
    # Convert to DataFrame
    df = pd.DataFrame(messages)
    
    if len(df) == 0:
        return pd.DataFrame()
    
    # Parse timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], format='ISO8601')
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    df["weekday"] = df["timestamp"].dt.day_name()
    
    # Ensure text is string for length calculation
    df["text"] = df["text"].fillna("")
    df["message_length"] = df["text"].str.len()
    
    # Media detection
    df["has_media"] = df["media_type"].notna()
    
    # Sort chronologically
    df = df.sort_values("timestamp").reset_index(drop=True)
    
    # Calculate reply gaps (only when sender changes)
    df["previous_sender"] = df["sender"].shift(1)
    df["previous_timestamp"] = df["timestamp"].shift(1)
    
    df["reply_gap_minutes"] = (
        (df["timestamp"] - df["previous_timestamp"])
        .dt.total_seconds()
        .div(60)
    )
    
    # Reply gap only counts when sender changes
    df.loc[df["sender"] == df["previous_sender"], "reply_gap_minutes"] = None
    
    # Per-person metrics
    person_metrics = df.groupby("sender").agg(
        messages_count=("message_id", "count"),
        avg_message_length=("message_length", "mean"),
        median_message_length=("message_length", "median"),
        media_messages=("has_media", "sum"),
        avg_reply_gap_minutes=("reply_gap_minutes", "mean"),
        median_reply_gap_minutes=("reply_gap_minutes", "median"),
    ).reset_index()
    
    # Calculate media share percentage
    person_metrics["media_share_percent"] = (
        person_metrics["media_messages"] / person_metrics["messages_count"] * 100
    ).round(2)
    
    # Daily initiative: who writes first each day
    daily_first = df.sort_values("timestamp").groupby("date").first().reset_index()
    initiative = daily_first.groupby("sender").size().reset_index(name="days_opened")
    
    # Daily closing: who writes last each day
    daily_last = df.sort_values("timestamp").groupby("date").last().reset_index()
    closing = daily_last.groupby("sender").size().reset_index(name="days_closed")
    
    # Merge all metrics
    result = (
        person_metrics
        .merge(initiative, on="sender", how="left")
        .merge(closing, on="sender", how="left")
        .fillna(0)
    )
    
    # Round numeric columns
    numeric_cols = ['avg_message_length', 'median_message_length', 
                   'avg_reply_gap_minutes', 'median_reply_gap_minutes']
    result[numeric_cols] = result[numeric_cols].round(2)
    
    # Convert integer columns
    int_cols = ['messages_count', 'media_messages', 'days_opened', 'days_closed']
    result[int_cols] = result[int_cols].astype(int)
    
    # Add percentage column
    total_msgs = result['messages_count'].sum()
    result['percentage'] = (result['messages_count'] / total_msgs * 100).round(2)
    
    # Count questions (simple heuristic: messages ending with '?')
    df['is_question'] = df['text'].str.strip().str.endswith('?').fillna(False)
    questions_by_sender = df.groupby('sender')['is_question'].sum().reset_index(name='questions_count')
    result = result.merge(questions_by_sender, on='sender', how='left')
    result['questions_count'] = result['questions_count'].fillna(0).astype(int)
    
    return result


def main():
    """Main analysis"""
    
    print("=" * 80)
    print("RELATIONSHIP METRICS ANALYSIS (RAW DATA)")
    print("Calculating basic metrics from forensic export")
    print("=" * 80)
    
    if not INPUT.exists():
        print(f"[ERROR] Input file not found: {INPUT}")
        print("Run ETAP 1 first: python scripts/forensic_export_raw.py")
        sys.exit(1)
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        print(f"\n[LOAD] Reading: {INPUT}")
        df = pd.read_json(INPUT, lines=True)
        messages = df.to_dict('records')
        print(f"[OK] Loaded {len(messages)} messages")
        
        # Compute metrics using reusable function
        result = compute_per_person_metrics(messages)
        
        # Save to CSV
        result.to_csv(OUTPUT, index=False, encoding="utf-8")
        
        # Display results
        print("\n" + "=" * 80)
        print("RELATIONSHIP BASIC METRICS")
        print("=" * 80)
        print(result.to_string(index=False))
        
        print(f"\n[SAVED] Output: {OUTPUT}")
        
        # Additional insights
        print("\n" + "=" * 80)
        print("KEY INSIGHTS")
        print("=" * 80)
        
        total_msgs = result['messages_count'].sum()
        for _, row in result.iterrows():
            print(f"\n{row['sender']}:")
            print(f"  • Messages: {row['messages_count']} ({row['messages_count']/total_msgs*100:.1f}%)")
            print(f"  • Avg length: {row['avg_message_length']} chars")
            print(f"  • Media share: {row['media_share_percent']}%")
            print(f"  • Avg reply gap: {row['avg_reply_gap_minutes']:.2f} min")
            print(f"  • Days opened: {int(row['days_opened'])}")
            print(f"  • Days closed: {int(row['days_closed'])}")
        
        # Initiative ratio
        total_days = result['days_opened'].sum()
        for _, row in result.iterrows():
            if total_days > 0:
                init_pct = row['days_opened'] / total_days * 100
                print(f"\n{row['sender']} initiates {init_pct:.1f}% of conversation days")
        
        print("\n" + "=" * 80)
        print("Next step: ETAP 2 — Timeline phase detection")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
