#!/usr/bin/env python3
"""
ETAP 1 — RAW FORENSIC EXPORT
Extract all Facebook conversation data into neutral, uninterpreted format

Output formats:
- JSONL (one message per line)
- CSV (tabular format)
- Timeline index (metadata only)

NO interpretation at this stage. Pure data extraction.
"""

import json
import csv
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.db.neo4j_connection import get_neo4j_driver
from core.normalization.ascii_pl import to_ascii_pl


def extract_raw_messages(conversation_path: Path) -> List[Dict]:
    """Extract raw messages from Facebook JSON export"""
    
    print(f"[INFO] Loading conversation from: {conversation_path}")
    
    with open(conversation_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    messages = data.get('messages', [])
    participants = [p['name'] for p in data.get('participants', [])]
    
    print(f"[OK] Loaded {len(messages)} messages from {len(participants)} participants")
    
    return messages, participants


def calculate_reply_gaps(messages: List[Dict]) -> List[Dict]:
    """Calculate reply gaps between messages (in minutes)"""
    
    # Sort by timestamp
    sorted_msgs = sorted(messages, key=lambda m: m.get('timestamp_ms', 0))
    
    enriched_messages = []
    
    for i, msg in enumerate(sorted_msgs):
        raw_text = msg.get('content', '') or ''
        
        enriched = {
            'message_id': f"msg_{i+1:06d}",
            'timestamp': datetime.fromtimestamp(msg.get('timestamp_ms', 0) / 1000).isoformat(),
            'date': datetime.fromtimestamp(msg.get('timestamp_ms', 0) / 1000).strftime('%Y-%m-%d'),
            'sender': msg.get('sender_name', 'Unknown'),
            'text': raw_text,
            'text_ascii': to_ascii_pl(raw_text),
            'text_clean': to_ascii_pl(raw_text).lower(),
            'message_length': len(to_ascii_pl(raw_text)),
            'has_media': any(k in msg for k in ['photos', 'videos', 'gifs', 'audio_files', 'files']),
            'media_type': None,
            'reply_gap_minutes': None,
            'conversation_day_index': None  # Will be calculated after sorting
        }
        
        # Determine media type
        if 'photos' in msg:
            enriched['media_type'] = 'photo'
        elif 'videos' in msg:
            enriched['media_type'] = 'video'
        elif 'gifs' in msg:
            enriched['media_type'] = 'gif'
        elif 'audio_files' in msg:
            enriched['media_type'] = 'audio'
        elif 'files' in msg:
            enriched['media_type'] = 'file'
        
        # Calculate reply gap from previous message
        if i > 0:
            prev_msg = sorted_msgs[i - 1]
            gap_ms = msg.get('timestamp_ms', 0) - prev_msg.get('timestamp_ms', 0)
            gap_minutes = gap_ms / (1000 * 60)
            enriched['reply_gap_minutes'] = round(gap_minutes, 2)
        
        enriched_messages.append(enriched)
    
    return enriched_messages


def add_conversation_day_index(messages: List[Dict]) -> List[Dict]:
    """Add conversation day index (day 0, 1, 2, ... from start)"""
    
    if not messages:
        return messages
    
    # Get earliest date
    earliest_date = datetime.fromisoformat(messages[0]['timestamp']).date()
    
    for msg in messages:
        msg_date = datetime.fromisoformat(msg['timestamp']).date()
        day_index = (msg_date - earliest_date).days
        msg['conversation_day_index'] = day_index
    
    return messages


def export_to_jsonl(messages: List[Dict], output_path: Path):
    """Export messages to JSONL format (one JSON object per line)"""
    
    print(f"\n[EXPORT] Writing JSONL to: {output_path}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for msg in messages:
            f.write(json.dumps(msg, ensure_ascii=False) + '\n')
    
    print(f"   ✓ Exported {len(messages)} messages to JSONL")


def export_to_csv(messages: List[Dict], output_path: Path):
    """Export messages to CSV format"""
    
    print(f"[EXPORT] Writing CSV to: {output_path}")
    
    if not messages:
        return
    
    fieldnames = [
        'message_id',
        'timestamp',
        'date',
        'sender',
        'text',
        'text_ascii',
        'text_clean',
        'message_length',
        'has_media',
        'media_type',
        'reply_gap_minutes',
        'conversation_day_index'
    ]
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for msg in messages:
            # Escape text for CSV (handle newlines, commas, quotes)
            row = msg.copy()
            row['text'] = msg['text'].replace('\n', ' ').replace('\r', '')
            writer.writerow(row)
    
    print(f"   ✓ Exported {len(messages)} messages to CSV")


def create_timeline_index(messages: List[Dict], output_path: Path):
    """Create timeline index with aggregate metadata"""
    
    print(f"[EXPORT] Creating timeline index: {output_path}")
    
    # Calculate timeline statistics
    timestamps = []
    for m in messages:
        try:
            ts = datetime.fromisoformat(m['timestamp'])
            timestamps.append(ts.timestamp() * 1000)  # Convert to ms
        except:
            continue
    
    if not timestamps:
        return
    
    earliest = min(timestamps)
    latest = max(timestamps)
    duration_days = (latest - earliest) / (1000 * 60 * 60 * 24)
    
    # Count by sender
    sender_counts = {}
    for msg in messages:
        sender = msg['sender']
        sender_counts[sender] = sender_counts.get(sender, 0) + 1
    
    # Count media types
    media_counts = {}
    for msg in messages:
        if msg['media_type']:
            media_counts[msg['media_type']] = media_counts.get(msg['media_type'], 0) + 1
    
    # Calculate average reply gap
    reply_gaps = [m['reply_gap_minutes'] for m in messages if m['reply_gap_minutes'] is not None]
    avg_reply_gap = sum(reply_gaps) / len(reply_gaps) if reply_gaps else 0
    
    timeline_index = {
        'export_metadata': {
            'generated_at': datetime.now().isoformat(),
            'source': 'facebook_messenger_export',
            'total_messages': len(messages),
            'format': 'raw_forensic_export'
        },
        'time_range': {
            'earliest': datetime.fromtimestamp(earliest / 1000).isoformat(),
            'latest': datetime.fromtimestamp(latest / 1000).isoformat(),
            'duration_days': round(duration_days, 2)
        },
        'participant_statistics': sender_counts,
        'media_statistics': media_counts,
        'interaction_metrics': {
            'average_reply_gap_minutes': round(avg_reply_gap, 2),
            'min_reply_gap_minutes': round(min(reply_gaps), 2) if reply_gaps else 0,
            'max_reply_gap_minutes': round(max(reply_gaps), 2) if reply_gaps else 0
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(timeline_index, f, indent=2, ensure_ascii=False)
    
    print(f"   ✓ Created timeline index")


def main():
    """Main execution"""
    
    print("=" * 80)
    print("ETAP 1 — RAW FORENSIC EXPORT")
    print("Extracting uninterpreted conversation data")
    print("=" * 80)
    
    # Path to Facebook conversation
    conversation_path = Path(__file__).parent.parent / "Facebook" / "kasiaju_1977350892357109" / "message_1.json"
    
    if not conversation_path.exists():
        print(f"[ERROR] Conversation file not found: {conversation_path}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent / "data" / "forensic_export" / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Extract raw messages
        messages, participants = extract_raw_messages(conversation_path)
        
        # Step 2: Enrich with reply gaps and metadata
        print("\n[PROCESSING] Calculating reply gaps and enriching metadata...")
        enriched_messages = calculate_reply_gaps(messages)
        
        # Step 2.5: Add conversation day index
        print("[PROCESSING] Adding conversation day index...")
        enriched_messages = add_conversation_day_index(enriched_messages)
        
        # Step 3: Export to JSONL
        jsonl_path = output_dir / "messages.jsonl"
        export_to_jsonl(enriched_messages, jsonl_path)
        
        # Step 4: Export to CSV
        csv_path = output_dir / "messages.csv"
        export_to_csv(enriched_messages, csv_path)
        
        # Step 5: Create timeline index
        index_path = output_dir / "timeline_index.json"
        create_timeline_index(enriched_messages, index_path)
        
        # Summary
        print("\n" + "=" * 80)
        print("RAW FORENSIC EXPORT COMPLETE")
        print("=" * 80)
        print(f"\nOutput directory: {output_dir}")
        print(f"Files created:")
        print(f"  • {jsonl_path.name} - JSONL format ({len(enriched_messages)} messages)")
        print(f"  • {csv_path.name} - CSV format ({len(enriched_messages)} messages)")
        print(f"  • {index_path.name} - Timeline index with metadata")
        print(f"\nParticipants: {', '.join(participants)}")
        print(f"Time range: {enriched_messages[-1]['timestamp']} → {enriched_messages[0]['timestamp']}")
        print(f"\nNext step: ETAP 2 — RELATIONSHIP TIMELINE (phase detection)")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Export failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
