#!/usr/bin/env python3
"""
P-OS v8.0 — Facebook Conversation Ontology Ingestion Interface
Ingests Facebook Messenger conversations as knowledge graph ontology

Ontology Structure:
- Person nodes (participants)
- Message nodes (individual messages with metadata)
- Conversation thread (container for messages)
- Relationships: SENT, REPLIES_TO, MENTIONS, KNOWS, INTERACTED_WITH
- Temporal properties for all interactions

Features:
- Idempotent ingestion (safe to run multiple times)
- Condensed storage (aggregated statistics + sample messages)
- Relationship inference from conversation patterns
- Media file tracking (photos, videos, gifs)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.db.neo4j_connection import get_neo4j_driver


class FacebookOntologyIngester:
    """Ingests Facebook conversation data into Neo4j as ontology"""
    
    def __init__(self, conversation_path: str):
        self.conversation_path = Path(conversation_path)
        self.driver = get_neo4j_driver()
        self.data = None
        self.statistics = {}
        
    def load_conversation(self):
        """Load and parse the conversation JSON file"""
        print(f"[INFO] Loading conversation from: {self.conversation_path}")
        
        with open(self.conversation_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # Basic validation
        if 'participants' not in self.data or 'messages' not in self.data:
            raise ValueError("Invalid conversation format: missing 'participants' or 'messages'")
        
        print(f"[OK] Loaded {len(self.data['messages'])} messages from {len(self.data['participants'])} participants")
        
    def analyze_conversation(self) -> Dict:
        """Analyze conversation patterns for condensed storage"""
        messages = self.data['messages']
        participants = [p['name'] for p in self.data['participants']]
        
        # Message statistics per participant
        sender_counts = Counter(msg['sender_name'] for msg in messages)
        
        # Temporal analysis
        timestamps = [msg['timestamp_ms'] for msg in messages if 'timestamp_ms' in msg]
        if timestamps:
            earliest = min(timestamps)
            latest = max(timestamps)
            duration_days = (latest - earliest) / (1000 * 60 * 60 * 24)
        else:
            earliest = latest = 0
            duration_days = 0
        
        # Content analysis
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        avg_message_length = total_chars / len(messages) if messages else 0
        
        # Media analysis
        media_types = {
            'photos': sum(1 for msg in messages if 'photos' in msg),
            'videos': sum(1 for msg in messages if 'videos' in msg),
            'gifs': sum(1 for msg in messages if 'gifs' in msg),
            'audio': sum(1 for msg in messages if 'audio_files' in msg),
            'files': sum(1 for msg in messages if 'files' in msg)
        }
        
        # Mention detection (names mentioned in content)
        mentions = defaultdict(int)
        for msg in messages:
            content = msg.get('content', '').lower()
            for participant in participants:
                if participant.lower() in content and msg['sender_name'] != participant:
                    mentions[msg['sender_name'] + '->' + participant] += 1
        
        self.statistics = {
            'total_messages': len(messages),
            'participants': participants,
            'message_distribution': dict(sender_counts),
            'time_range': {
                'earliest': datetime.fromtimestamp(earliest / 1000).isoformat(),
                'latest': datetime.fromtimestamp(latest / 1000).isoformat(),
                'duration_days': round(duration_days, 2)
            },
            'content_stats': {
                'total_characters': total_chars,
                'avg_message_length': round(avg_message_length, 2)
            },
            'media_summary': media_types,
            'mentions': dict(mentions)
        }
        
        return self.statistics
    
    def ingest_condensed_ontology(self):
        """
        Ingest condensed ontology representation:
        - Person nodes with relationship metadata
        - Aggregated conversation statistics
        - Sample messages (first, last, longest, most recent)
        - Inferred relationships based on interaction patterns
        """
        print("\n[PHASE 1] Creating Person nodes with relationship metadata...")
        self._ingest_persons()
        
        print("[PHASE 2] Creating conversation thread with statistics...")
        self._ingest_conversation_thread()
        
        print("[PHASE 3] Ingesting sample messages (boundary & significant)...")
        self._ingest_sample_messages()
        
        print("[PHASE 4] Inferring and creating relationships...")
        self._infer_relationships()
        
        print("[PHASE 5] Tracking media files...")
        self._track_media_files()
        
        print("\n[COMPLETE] Condensed ontology ingestion finished.")
    
    def _ingest_persons(self):
        """Create Person nodes with enriched metadata"""
        participants = self.data['participants']
        stats = self.statistics
        
        with self.driver.session() as session:
            for participant in participants:
                name = participant['name']
                message_count = stats['message_distribution'].get(name, 0)
                
                # Calculate participation percentage
                total_msgs = stats['total_messages']
                participation_pct = (message_count / total_msgs * 100) if total_msgs > 0 else 0
                
                # Determine role based on message patterns
                role = self._infer_person_role(name, stats)
                
                session.run("""
                    MERGE (p:Person:FacebookUser {name: $name})
                    SET p.source = 'facebook_messenger',
                        p.message_count = $message_count,
                        p.participation_percentage = round($participation_pct, 2),
                        p.role_in_conversation = $role,
                        p.last_updated = timestamp()
                """, {
                    'name': name,
                    'message_count': message_count,
                    'participation_pct': participation_pct,
                    'role': role
                })
            
            print(f"   ✓ Created/updated {len(participants)} Person nodes")
    
    def _infer_person_role(self, name: str, stats: Dict) -> str:
        """Infer person's role in conversation based on patterns"""
        msg_count = stats['message_distribution'].get(name, 0)
        total = stats['total_messages']
        
        if total == 0:
            return 'unknown'
        
        ratio = msg_count / total
        
        if ratio > 0.7:
            return 'primary_contributor'
        elif ratio > 0.4:
            return 'active_participant'
        elif ratio > 0.2:
            return 'occasional_participant'
        else:
            return 'minimal_participant'
    
    def _ingest_conversation_thread(self):
        """Create conversation thread node with aggregated statistics"""
        stats = self.statistics
        title = self.data.get('title', 'Untitled Conversation')
        thread_path = self.data.get('thread_path', '')
        
        with self.driver.session() as session:
            session.run("""
                MERGE (c:Conversation:FacebookThread {thread_id: $thread_id})
                SET c.title = $title,
                    c.thread_path = $thread_path,
                    c.total_messages = $total_messages,
                    c.participant_count = $participant_count,
                    c.duration_days = $duration_days,
                    c.start_date = $start_date,
                    c.end_date = $end_date,
                    c.avg_message_length = $avg_message_length,
                    c.total_characters = $total_characters,
                    c.media_photos = $media_photos,
                    c.media_videos = $media_videos,
                    c.media_gifs = $media_gifs,
                    c.media_audio = $media_audio,
                    c.media_files = $media_files,
                    c.ingested_at = timestamp(),
                    c.data_source = 'facebook_export'
            """, {
                'thread_id': thread_path or title.replace(' ', '_').lower(),
                'title': title,
                'thread_path': thread_path,
                'total_messages': stats['total_messages'],
                'participant_count': len(stats['participants']),
                'duration_days': stats['time_range']['duration_days'],
                'start_date': stats['time_range']['earliest'],
                'end_date': stats['time_range']['latest'],
                'avg_message_length': stats['content_stats']['avg_message_length'],
                'total_characters': stats['content_stats']['total_characters'],
                'media_photos': stats['media_summary'].get('photos', 0),
                'media_videos': stats['media_summary'].get('videos', 0),
                'media_gifs': stats['media_summary'].get('gifs', 0),
                'media_audio': stats['media_summary'].get('audio', 0),
                'media_files': stats['media_summary'].get('files', 0)
            })
            
            # Link participants to conversation
            for participant_name in stats['participants']:
                session.run("""
                    MATCH (p:Person {name: $name})
                    MATCH (c:Conversation {thread_id: $thread_id})
                    MERGE (p)-[:PARTICIPATES_IN]->(c)
                """, {'name': participant_name, 'thread_id': thread_path or title.replace(' ', '_').lower()})
            
            print(f"   ✓ Created conversation thread with {stats['total_messages']} messages")
    
    def _ingest_sample_messages(self):
        """Ingest strategically selected sample messages"""
        messages = self.data['messages']
        if not messages:
            return
        
        # Select key messages: first, last, longest, shortest, most recent week
        sorted_by_time = sorted(messages, key=lambda m: m.get('timestamp_ms', 0))
        
        samples = {
            'first_message': sorted_by_time[0] if sorted_by_time else None,
            'last_message': sorted_by_time[-1] if sorted_by_time else None,
            'longest_message': max(messages, key=lambda m: len(m.get('content', ''))),
            'shortest_message': min(messages, key=lambda m: len(m.get('content', ''))) if messages else None
        }
        
        # Get messages from last week (most recent 7 days)
        if sorted_by_time:
            latest_ts = sorted_by_time[-1].get('timestamp_ms', 0)
            one_week_ms = 7 * 24 * 60 * 60 * 1000
            recent_cutoff = latest_ts - one_week_ms
            recent_messages = [m for m in sorted_by_time if m.get('timestamp_ms', 0) >= recent_cutoff]
            samples['recent_week_sample'] = recent_messages[:10]  # Limit to 10
        
        thread_id = self.data.get('thread_path', '') or self.data.get('title', '').replace(' ', '_').lower()
        
        with self.driver.session() as session:
            for sample_type, msg in samples.items():
                if msg is None:
                    continue
                
                # Handle list of messages (for recent_week_sample)
                if isinstance(msg, list):
                    for i, single_msg in enumerate(msg):
                        self._store_single_message(session, single_msg, thread_id, f"{sample_type}_{i}")
                else:
                    self._store_single_message(session, msg, thread_id, sample_type)
            
            print(f"   ✓ Stored {len(samples)} message samples")
    
    def _store_single_message(self, session, msg: Dict, thread_id: str, sample_type: str):
        """Store a single message as a sample"""
        content = msg.get('content', '')
        sender = msg.get('sender_name', 'Unknown')
        timestamp_ms = msg.get('timestamp_ms', 0)
        timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000).isoformat() if timestamp_ms else None
        
        # Detect if message contains mentions
        participants = self.statistics['participants']
        mentioned = [p for p in participants if p.lower() in content.lower() and p != sender]
        
        session.run("""
            MERGE (m:Message:SampleMessage {
                thread_id: $thread_id,
                sample_type: $sample_type
            })
            SET m.content = $content,
                m.sender = $sender,
                m.timestamp = $timestamp,
                m.timestamp_iso = $timestamp_iso,
                m.content_length = $content_length,
                m.mentioned_persons = $mentioned,
                m.has_media = $has_media,
                m.stored_at = timestamp()
            
            WITH m
            MATCH (p:Person {name: $sender})
            MERGE (p)-[:SENT_SAMPLE {type: $sample_type}]->(m)
            
            WITH m
            MATCH (c:Conversation {thread_id: $thread_id})
            MERGE (m)-[:PART_OF]->(c)
        """, {
            'thread_id': thread_id,
            'sample_type': sample_type,
            'content': content[:1000],  # Truncate very long messages
            'sender': sender,
            'timestamp': timestamp_ms,
            'timestamp_iso': timestamp_dt,
            'content_length': len(content),
            'mentioned': mentioned,
            'has_media': any(k in msg for k in ['photos', 'videos', 'gifs', 'audio_files', 'files'])
        })
    
    def _infer_relationships(self):
        """Infer relationships between persons based on conversation patterns"""
        stats = self.statistics
        participants = stats['participants']
        
        with self.driver.session() as session:
            # Create KNOWS relationship between all participants
            if len(participants) >= 2:
                for i in range(len(participants)):
                    for j in range(i + 1, len(participants)):
                        person1 = participants[i]
                        person2 = participants[j]
                        
                        # Calculate interaction strength
                        msgs_p1 = stats['message_distribution'].get(person1, 0)
                        msgs_p2 = stats['message_distribution'].get(person2, 0)
                        total = stats['total_messages']
                        
                        interaction_strength = min(msgs_p1, msgs_p2) / total if total > 0 else 0
                        
                        # Determine relationship type based on patterns
                        relationship_type = self._classify_relationship(person1, person2, stats)
                        
                        session.run("""
                            MATCH (p1:Person {name: $person1})
                            MATCH (p2:Person {name: $person2})
                            MERGE (p1)-[r:KNOWS]-(p2)
                            SET r.relationship_type = $rel_type,
                                r.interaction_strength = round($strength, 3),
                                r.conversation_context = 'facebook_messenger',
                                r.first_observed = $first_date,
                                r.last_observed = $last_date,
                                r.evidence = 'conversation_analysis'
                        """, {
                            'person1': person1,
                            'person2': person2,
                            'rel_type': relationship_type,
                            'strength': interaction_strength,
                            'first_date': stats['time_range']['earliest'],
                            'last_date': stats['time_range']['latest']
                        })
            
            # Create INTERACTED_WITH relationships based on mentions
            for mention_key, count in stats['mentions'].items():
                if '->' in mention_key:
                    sender, target = mention_key.split('->')
                    session.run("""
                        MATCH (p1:Person {name: $sender})
                        MATCH (p2:Person {name: $target})
                        MERGE (p1)-[r:MENTIONS]->(p2)
                        SET r.mention_count = coalesce(r.mention_count, 0) + $count,
                            r.last_mentioned = timestamp()
                    """, {'sender': sender, 'target': target, 'count': count})
            
            print(f"   ✓ Created {len(participants) * (len(participants) - 1) // 2} KNOWS relationships")
            print(f"   ✓ Created {len(stats['mentions'])} MENTIONS relationships")
    
    def _classify_relationship(self, person1: str, person2: str, stats: Dict) -> str:
        """Classify relationship type based on conversation patterns"""
        # Simple heuristic - can be enhanced with NLP
        msg_dist = stats['message_distribution']
        
        p1_msgs = msg_dist.get(person1, 0)
        p2_msgs = msg_dist.get(person2, 0)
        
        # Balanced conversation suggests friendship/acquaintance
        if abs(p1_msgs - p2_msgs) < max(p1_msgs, p2_msgs) * 0.3:
            return 'peer'
        # Unbalanced might indicate different social dynamics
        elif p1_msgs > p2_msgs * 2:
            return 'initiator_responder'
        else:
            return 'responder_initiator'
    
    def _track_media_files(self):
        """Track media files referenced in conversation"""
        messages = self.data['messages']
        media_dir = self.conversation_path.parent / self.conversation_path.stem
        
        media_count = 0
        
        with self.driver.session() as session:
            for msg in messages:
                if not any(k in msg for k in ['photos', 'videos', 'gifs', 'audio_files', 'files']):
                    continue
                
                sender = msg.get('sender_name', 'Unknown')
                timestamp_ms = msg.get('timestamp_ms', 0)
                
                # Process photos
                for photo in msg.get('photos', []):
                    uri = photo.get('uri', '')
                    creation_timestamp = photo.get('creation_timestamp', timestamp_ms)
                    
                    session.run("""
                        MATCH (p:Person {name: $sender})
                        MERGE (media:Media:Photo {uri: $uri})
                        SET media.type = 'photo',
                            media.sender = $sender,
                            media.creation_timestamp = $timestamp,
                            media.tracked_at = timestamp()
                        MERGE (p)-[:SHARED]->(media)
                    """, {
                        'sender': sender,
                        'uri': uri,
                        'timestamp': creation_timestamp
                    })
                    media_count += 1
                
                # Process videos
                for video in msg.get('videos', []):
                    uri = video.get('uri', '')
                    creation_timestamp = video.get('creation_timestamp', timestamp_ms)
                    
                    session.run("""
                        MATCH (p:Person {name: $sender})
                        MERGE (media:Media:Video {uri: $uri})
                        SET media.type = 'video',
                            media.sender = $sender,
                            media.creation_timestamp = $timestamp,
                            media.tracked_at = timestamp()
                        MERGE (p)-[:SHARED]->(media)
                    """, {
                        'sender': sender,
                        'uri': uri,
                        'timestamp': creation_timestamp
                    })
                    media_count += 1
            
            print(f"   ✓ Tracked {media_count} media files")
    
    def generate_report(self) -> Dict:
        """Generate ingestion report"""
        return {
            'status': 'success',
            'conversation_title': self.data.get('title', 'Unknown'),
            'statistics': self.statistics,
            'timestamp': datetime.now().isoformat()
        }
    
    def close(self):
        """Close database connection"""
        self.driver.close()
        print("[OK] Database connection closed")


def main():
    """Main execution function"""
    print("=" * 80)
    print("P-OS v8.0 — Facebook Conversation Ontology Ingester")
    print("=" * 80)
    
    # Default path to the conversation
    conversation_path = Path(__file__).parent.parent / "Facebook" / "kasiaju_1977350892357109" / "message_1.json"
    
    if not conversation_path.exists():
        print(f"[ERROR] Conversation file not found: {conversation_path}")
        sys.exit(1)
    
    try:
        # Initialize ingester
        ingester = FacebookOntologyIngester(str(conversation_path))
        
        # Load data
        ingester.load_conversation()
        
        # Analyze conversation patterns
        print("\n[ANALYSIS] Computing conversation statistics...")
        stats = ingester.analyze_conversation()
        
        print(f"\n   Participants: {', '.join(stats['participants'])}")
        print(f"   Total Messages: {stats['total_messages']}")
        print(f"   Time Range: {stats['time_range']['earliest']} → {stats['time_range']['latest']}")
        print(f"   Duration: {stats['time_range']['duration_days']} days")
        print(f"   Message Distribution: {stats['message_distribution']}")
        print(f"   Media Files: {stats['media_summary']}")
        
        # Ingest condensed ontology
        print("\n[INGESTION] Starting condensed ontology ingestion...")
        ingester.ingest_condensed_ontology()
        
        # Generate report
        report = ingester.generate_report()
        print("\n" + "=" * 80)
        print("INGESTION REPORT")
        print("=" * 80)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        
        # Cleanup
        ingester.close()
        
        print("\n" + "=" * 80)
        print("[SUCCESS] Ontology ingestion completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n[ERROR] Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
