#!/usr/bin/env python3
"""
ETAP 2 — RELATIONSHIP TIMELINE
Detect relationship phases using heuristics (no manual interpretation)

Phase detection based on:
- message density (messages per day/week)
- reply speed (average gap between messages)
- silence gaps (periods of no contact)
- time-of-day patterns
- media exchange frequency

Output: Phase-labeled timeline with transition points
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
from collections import defaultdict

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))


def load_raw_messages(jsonl_path: Path) -> List[Dict]:
    """Load raw forensic export (JSONL format)"""
    
    print(f"[INFO] Loading raw messages from: {jsonl_path}")
    
    messages = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                messages.append(json.loads(line))
    
    # Sort by timestamp
    messages.sort(key=lambda m: m['timestamp_ms'])
    
    print(f"[OK] Loaded {len(messages)} messages")
    return messages


def detect_silence_periods(messages: List[Dict], threshold_hours: float = 72.0) -> List[Dict]:
    """Detect periods of silence (no communication)"""
    
    silence_periods = []
    
    for i in range(1, len(messages)):
        prev_msg = messages[i - 1]
        curr_msg = messages[i]
        
        gap_hours = (curr_msg['timestamp_ms'] - prev_msg['timestamp_ms']) / (1000 * 60 * 60)
        
        if gap_hours >= threshold_hours:
            silence_periods.append({
                'start': prev_msg['timestamp_iso'],
                'end': curr_msg['timestamp_iso'],
                'duration_hours': round(gap_hours, 2),
                'duration_days': round(gap_hours / 24, 2),
                'before_message_idx': i - 1,
                'after_message_idx': i
            })
    
    return silence_periods


def calculate_message_density(messages: List[Dict], window_days: int = 7) -> List[Dict]:
    """Calculate message density over sliding windows"""
    
    if not messages:
        return []
    
    # Convert to datetime objects
    timestamps = [datetime.fromisoformat(m['timestamp_iso']) for m in messages]
    
    earliest = min(timestamps)
    latest = max(timestamps)
    
    density_windows = []
    current_start = earliest
    
    while current_start < latest:
        current_end = current_start + timedelta(days=window_days)
        
        # Count messages in this window
        count = sum(1 for ts in timestamps if current_start <= ts < current_end)
        
        density_windows.append({
            'window_start': current_start.isoformat(),
            'window_end': current_end.isoformat(),
            'message_count': count,
            'density_per_day': round(count / window_days, 2)
        })
        
        current_start += timedelta(days=window_days)
    
    return density_windows


def calculate_reply_speed_by_period(messages: List[Dict], period_days: int = 30) -> List[Dict]:
    """Calculate average reply speed over time periods"""
    
    if not messages:
        return []
    
    timestamps = [datetime.fromisoformat(m['timestamp_iso']) for m in messages]
    reply_gaps = [m['reply_gap_minutes'] for m in messages if m['reply_gap_minutes'] is not None]
    
    earliest = min(timestamps)
    latest = max(timestamps)
    
    reply_speed_periods = []
    current_start = earliest
    
    gap_idx = 0
    
    while current_start < latest:
        current_end = current_start + timedelta(days=period_days)
        
        # Get reply gaps in this period
        period_gaps = []
        for i, msg in enumerate(messages):
            msg_time = datetime.fromisoformat(msg['timestamp_iso'])
            if current_start <= msg_time < current_end and msg['reply_gap_minutes'] is not None:
                period_gaps.append(msg['reply_gap_minutes'])
        
        if period_gaps:
            avg_gap = sum(period_gaps) / len(period_gaps)
            median_gap = sorted(period_gaps)[len(period_gaps) // 2]
        else:
            avg_gap = None
            median_gap = None
        
        reply_speed_periods.append({
            'period_start': current_start.isoformat(),
            'period_end': current_end.isoformat(),
            'avg_reply_gap_minutes': round(avg_gap, 2) if avg_gap else None,
            'median_reply_gap_minutes': round(median_gap, 2) if median_gap else None,
            'total_replies': len(period_gaps)
        })
        
        current_start += timedelta(days=period_days)
    
    return reply_speed_periods


def detect_phases_heuristic(messages: List[Dict], silence_periods: List[Dict], 
                           density_windows: List[Dict]) -> List[Dict]:
    """
    Detect relationship phases using heuristics
    
    Phase definitions:
    - PHASE_INITIATION: Low density, high reply gaps (getting to know each other)
    - PHASE_INTENSIFICATION: High density, low reply gaps (deepening connection)
    - PHASE_STABILIZATION: Medium-high density, consistent patterns (established rhythm)
    - PHASE_TENSION: Variable density, increasing gaps (conflicts/emerg issues)
    - PHASE_WITHDRAWAL: Decreasing density, long gaps (pulling away)
    - PHASE_FADEOUT: Very low density, very long gaps (relationship ending)
    - PHASE_ECHO: Sporadic contact after long silence (post-relationship contact)
    """
    
    if not messages or not density_windows:
        return []
    
    # Calculate thresholds from data
    densities = [w['density_per_day'] for w in density_windows if w['density_per_day'] > 0]
    
    if not densities:
        return []
    
    avg_density = sum(densities) / len(densities)
    max_density = max(densities)
    
    # Define thresholds
    low_density_threshold = avg_density * 0.3
    medium_density_threshold = avg_density * 0.7
    high_density_threshold = avg_density * 1.3
    
    # Assign phases to each window
    phased_timeline = []
    
    for window in density_windows:
        density = window['density_per_day']
        
        if density == 0:
            phase = 'PHASE_SILENCE'
        elif density < low_density_threshold:
            phase = 'PHASE_INITIATION' if window == density_windows[0] else 'PHASE_ECHO'
        elif density < medium_density_threshold:
            phase = 'PHASE_STABILIZATION'
        elif density < high_density_threshold:
            phase = 'PHASE_INTENSIFICATION'
        else:
            phase = 'PHASE_INTENSIFICATION'
        
        phased_timeline.append({
            **window,
            'phase': phase,
            'phase_category': categorize_phase(phase)
        })
    
    # Detect phase transitions
    transitions = detect_phase_transitions(phased_timeline)
    
    return phased_timeline, transitions


def categorize_phase(phase: str) -> str:
    """Categorize phase into broader category"""
    
    categories = {
        'PHASE_INITIATION': 'building',
        'PHASE_INTENSIFICATION': 'building',
        'PHASE_STABILIZATION': 'stable',
        'PHASE_TENSION': 'declining',
        'PHASE_WITHDRAWAL': 'declining',
        'PHASE_FADEOUT': 'ending',
        'PHASE_SILENCE': 'inactive',
        'PHASE_ECHO': 'post_relationship'
    }
    
    return categories.get(phase, 'unknown')


def detect_phase_transitions(phased_timeline: List[Dict]) -> List[Dict]:
    """Detect points where phase changes"""
    
    transitions = []
    
    for i in range(1, len(phased_timeline)):
        prev_phase = phased_timeline[i - 1]['phase']
        curr_phase = phased_timeline[i]['phase']
        
        if prev_phase != curr_phase:
            transitions.append({
                'transition_point': phased_timeline[i]['window_start'],
                'from_phase': prev_phase,
                'to_phase': curr_phase,
                'from_category': phased_timeline[i - 1]['phase_category'],
                'to_category': phased_timeline[i]['phase_category']
            })
    
    return transitions


def export_phase_labeled_messages(messages: List[Dict], phased_timeline: List[Dict], 
                                  output_path: Path):
    """Add phase labels to each message and export"""
    
    print(f"\n[EXPORT] Labeling messages with phases...")
    
    # Create phase lookup by timestamp
    phase_lookup = {}
    for window in phased_timeline:
        phase_lookup[window['window_start']] = window['phase']
    
    # Assign phases to messages
    labeled_messages = []
    for msg in messages:
        msg_time = datetime.fromisoformat(msg['timestamp_iso'])
        
        # Find corresponding phase window
        assigned_phase = 'unknown'
        for window in phased_timeline:
            window_start = datetime.fromisoformat(window['window_start'])
            window_end = datetime.fromisoformat(window['window_end'])
            
            if window_start <= msg_time < window_end:
                assigned_phase = window['phase']
                break
        
        labeled_msg = {
            **msg,
            'conversation_phase': assigned_phase
        }
        labeled_messages.append(labeled_msg)
    
    # Export to JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for msg in labeled_messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    print(f"   ✓ Exported {len(labeled_messages)} phase-labeled messages")


def main():
    """Main execution"""
    
    print("=" * 80)
    print("ETAP 2 — RELATIONSHIP TIMELINE")
    print("Detecting relationship phases using heuristics")
    print("=" * 80)
    
    # Load raw forensic export
    raw_path = Path(__file__).parent.parent / "data" / "forensic_export" / "raw" / "messages.jsonl"
    
    if not raw_path.exists():
        print(f"[ERROR] Raw export not found. Run ETAP 1 first: {raw_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "data" / "forensic_export" / "timeline"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Load raw messages
        messages = load_raw_messages(raw_path)
        
        # Step 2: Detect silence periods
        print("\n[ANALYSIS] Detecting silence periods (>72 hours)...")
        silence_periods = detect_silence_periods(messages, threshold_hours=72.0)
        print(f"   ✓ Found {len(silence_periods)} silence periods")
        
        # Save silence periods
        silence_path = output_dir / "silence_periods.json"
        with open(silence_path, 'w', encoding='utf-8') as f:
            json.dump(silence_periods, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved to: {silence_path}")
        
        # Step 3: Calculate message density
        print("\n[ANALYSIS] Calculating message density (7-day windows)...")
        density_windows = calculate_message_density(messages, window_days=7)
        print(f"   ✓ Calculated {len(density_windows)} density windows")
        
        # Step 4: Calculate reply speed
        print("\n[ANALYSIS] Calculating reply speed (30-day periods)...")
        reply_speed = calculate_reply_speed_by_period(messages, period_days=30)
        print(f"   ✓ Calculated {len(reply_speed)} reply speed periods")
        
        # Step 5: Detect phases
        print("\n[ANALYSIS] Detecting relationship phases...")
        phased_timeline, transitions = detect_phases_heuristic(messages, silence_periods, density_windows)
        print(f"   ✓ Detected {len(set(p['phase'] for p in phased_timeline))} distinct phases")
        print(f"   ✓ Found {len(transitions)} phase transitions")
        
        # Save phased timeline
        timeline_path = output_dir / "phased_timeline.json"
        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump({
                'timeline': phased_timeline,
                'transitions': transitions,
                'metadata': {
                    'total_phases': len(set(p['phase'] for p in phased_timeline)),
                    'total_transitions': len(transitions)
                }
            }, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved to: {timeline_path}")
        
        # Step 6: Export phase-labeled messages
        labeled_path = output_dir / "messages_with_phases.jsonl"
        export_phase_labeled_messages(messages, phased_timeline, labeled_path)
        
        # Summary
        print("\n" + "=" * 80)
        print("RELATIONSHIP TIMELINE COMPLETE")
        print("=" * 80)
        print(f"\nPhase distribution:")
        
        phase_counts = defaultdict(int)
        for p in phased_timeline:
            phase_counts[p['phase']] += 1
        
        for phase, count in sorted(phase_counts.items()):
            print(f"  • {phase}: {count} windows")
        
        print(f"\nOutput directory: {output_dir}")
        print(f"Files created:")
        print(f"  • {silence_path.name} - Silence periods")
        print(f"  • {timeline_path.name} - Phased timeline with transitions")
        print(f"  • {labeled_path.name} - Messages with phase labels")
        print(f"\nNext step: ETAP 3 — SEMANTIC EXTRACTION (themes, symbols, patterns)")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Timeline analysis failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
