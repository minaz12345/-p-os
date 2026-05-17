#!/usr/bin/env python3
"""
P-OS v8.0 — Facebook Ontology Query Interface
Query and analyze the ingested Facebook conversation ontology

Features:
- Person relationship queries
- Conversation pattern analysis
- Media tracking queries
- Temporal interaction analysis
- Export capabilities
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.db.neo4j_connection import get_neo4j_driver


class FacebookOntologyQuerier:
    """Query interface for Facebook conversation ontology"""
    
    def __init__(self):
        self.driver = get_neo4j_driver()
    
    def get_person_profile(self, person_name: str) -> Dict:
        """Get comprehensive profile for a person"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {name: $name})
                OPTIONAL MATCH (p)-[:PARTICIPATES_IN]->(c:Conversation)
                OPTIONAL MATCH (p)-[r:KNOWS]-(other:Person)
                OPTIONAL MATCH (p)-[:SENT_SAMPLE]->(m:SampleMessage)
                OPTIONAL MATCH (p)-[:SHARED]->(media:Media)
                RETURN p,
                       collect(DISTINCT c) as conversations,
                       collect(DISTINCT {person: other.name, type: r.relationship_type, strength: r.interaction_strength}) as relationships,
                       count(DISTINCT m) as sample_messages,
                       count(DISTINCT media) as shared_media
            """, {'name': person_name})
            
            record = result.single()
            if not record:
                return None
            
            person_data = dict(record['p'])
            return {
                'person': person_data,
                'conversations': [dict(c) for c in record['conversations']],
                'relationships': record['relationships'],
                'sample_messages': record['sample_messages'],
                'shared_media': record['shared_media']
            }
    
    def get_conversation_summary(self, thread_id: str) -> Dict:
        """Get summary of a conversation thread"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (c:Conversation {thread_id: $thread_id})
                OPTIONAL MATCH (p:Person)-[:PARTICIPATES_IN]->(c)
                OPTIONAL MATCH (m:SampleMessage)-[:PART_OF]->(c)
                RETURN c,
                       collect(DISTINCT p.name) as participants,
                       collect(DISTINCT {type: m.sample_type, sender: m.sender, length: m.content_length}) as samples
            """, {'thread_id': thread_id})
            
            record = result.single()
            if not record:
                return None
            
            return {
                'conversation': dict(record['c']),
                'participants': record['participants'],
                'message_samples': record['samples']
            }
    
    def find_relationships_between(self, person1: str, person2: str) -> List[Dict]:
        """Find all relationships between two persons"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p1:Person {name: $person1})-[r]-(p2:Person {name: $person2})
                RETURN type(r) as relationship_type,
                       properties(r) as relationship_properties,
                       p1.name as from_person,
                       p2.name as to_person
            """, {'person1': person1, 'person2': person2})
            
            return [dict(record) for record in result]
    
    def get_interaction_timeline(self, person_name: str) -> List[Dict]:
        """Get temporal interaction timeline for a person"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {name: $name})-[:SENT_SAMPLE]->(m:SampleMessage)
                RETURN m.timestamp_iso as timestamp,
                       m.sample_type as message_type,
                       m.content_length as length,
                       m.mentioned_persons as mentions
                ORDER BY m.timestamp
            """, {'name': person_name})
            
            return [dict(record) for record in result]
    
    def get_media_shared_by_person(self, person_name: str) -> List[Dict]:
        """Get all media shared by a person"""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {name: $name})-[:SHARED]->(media:Media)
                RETURN media.uri as uri,
                       media.type as type,
                       media.creation_timestamp as timestamp
                ORDER BY media.creation_timestamp DESC
            """, {'name': person_name})
            
            return [dict(record) for record in result]
    
    def analyze_conversation_patterns(self) -> Dict:
        """Analyze overall conversation patterns in the database"""
        with self.driver.session() as session:
            # Get all conversations
            conv_result = session.run("""
                MATCH (c:Conversation)
                RETURN count(c) as total_conversations,
                       avg(c.total_messages) as avg_messages,
                       avg(c.duration_days) as avg_duration_days
            """)
            
            conv_stats = dict(conv_result.single())
            
            # Get most active persons
            person_result = session.run("""
                MATCH (p:Person)
                RETURN p.name as name,
                       p.message_count as messages,
                       p.participation_percentage as participation_pct
                ORDER BY p.message_count DESC
                LIMIT 10
            """)
            
            top_persons = [dict(record) for record in person_result]
            
            # Get relationship types distribution
            rel_result = session.run("""
                MATCH ()-[r:KNOWS]-()
                RETURN r.relationship_type as type,
                       count(r) as count,
                       avg(r.interaction_strength) as avg_strength
            """)
            
            relationship_dist = [dict(record) for record in rel_result]
            
            return {
                'conversation_statistics': conv_stats,
                'most_active_persons': top_persons,
                'relationship_distribution': relationship_dist
            }
    
    def export_person_ontology(self, person_name: str, output_path: str = None):
        """Export complete ontology for a person as JSON"""
        profile = self.get_person_profile(person_name)
        
        if not profile:
            print(f"[ERROR] Person '{person_name}' not found")
            return None
        
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'person_profile': profile,
            'relationships': self.find_relationships_between(person_name, '*'),
            'timeline': self.get_interaction_timeline(person_name),
            'media': self.get_media_shared_by_person(person_name)
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            print(f"[OK] Exported to: {output_path}")
        
        return export_data
    
    def close(self):
        """Close database connection"""
        self.driver.close()


def interactive_query():
    """Interactive query interface"""
    querier = FacebookOntologyQuerier()
    
    print("\n" + "=" * 80)
    print("Facebook Ontology Query Interface")
    print("=" * 80)
    print("\nAvailable commands:")
    print("  1. Profile <person_name> - Get person profile")
    print("  2. Relationships <person1> <person2> - Find relationships")
    print("  3. Timeline <person_name> - Get interaction timeline")
    print("  4. Media <person_name> - Get shared media")
    print("  5. Patterns - Analyze conversation patterns")
    print("  6. Export <person_name> [file] - Export ontology")
    print("  7. Quit - Exit")
    print("=" * 80)
    
    while True:
        try:
            command = input("\n> ").strip()
            
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd in ['quit', 'exit', 'q']:
                break
            elif cmd == 'profile' and len(parts) >= 2:
                name = ' '.join(parts[1:])
                profile = querier.get_person_profile(name)
                if profile:
                    print(json.dumps(profile, indent=2, ensure_ascii=False))
                else:
                    print(f"[ERROR] Person '{name}' not found")
            elif cmd == 'relationships' and len(parts) >= 3:
                # Split into two names (assuming format: "Name1" "Name2" or Name1 Name2)
                if len(parts) == 3:
                    person1, person2 = parts[1], parts[2]
                else:
                    # Try to find where second name starts
                    person1 = parts[1]
                    person2 = ' '.join(parts[2:])
                
                rels = querier.find_relationships_between(person1, person2)
                print(json.dumps(rels, indent=2, ensure_ascii=False))
            elif cmd == 'timeline' and len(parts) >= 2:
                name = ' '.join(parts[1:])
                timeline = querier.get_interaction_timeline(name)
                print(json.dumps(timeline, indent=2, ensure_ascii=False))
            elif cmd == 'media' and len(parts) >= 2:
                name = ' '.join(parts[1:])
                media = querier.get_media_shared_by_person(name)
                print(json.dumps(media, indent=2, ensure_ascii=False))
            elif cmd == 'patterns':
                patterns = querier.analyze_conversation_patterns()
                print(json.dumps(patterns, indent=2, ensure_ascii=False))
            elif cmd == 'export' and len(parts) >= 2:
                name = ' '.join(parts[1:-1]) if len(parts) > 2 else parts[1]
                output_file = parts[-1] if len(parts) > 2 else f"{name.replace(' ', '_')}_ontology.json"
                querier.export_person_ontology(name, output_file)
            else:
                print("[ERROR] Invalid command. Use one of the available commands above.")
        
        except KeyboardInterrupt:
            print("\n[INFO] Exiting...")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
    
    querier.close()
    print("[OK] Connection closed")


def main():
    """Main execution"""
    if len(sys.argv) > 1:
        # Command-line mode
        querier = FacebookOntologyQuerier()
        
        command = sys.argv[1].lower()
        
        if command == 'profile' and len(sys.argv) >= 3:
            name = ' '.join(sys.argv[2:])
            profile = querier.get_person_profile(name)
            if profile:
                print(json.dumps(profile, indent=2, ensure_ascii=False))
            else:
                print(f"[ERROR] Person '{name}' not found")
                sys.exit(1)
        
        elif command == 'export' and len(sys.argv) >= 3:
            name = ' '.join(sys.argv[2:-1]) if len(sys.argv) > 3 else sys.argv[2]
            output_file = sys.argv[-1] if len(sys.argv) > 3 else f"{name.replace(' ', '_')}_ontology.json"
            querier.export_person_ontology(name, output_file)
        
        else:
            print("[ERROR] Unknown command or missing arguments")
            print("Usage:")
            print("  python query_facebook_ontology.py profile <person_name>")
            print("  python query_facebook_ontology.py export <person_name> [output_file]")
            sys.exit(1)
        
        querier.close()
    else:
        # Interactive mode
        interactive_query()


if __name__ == '__main__':
    main()
