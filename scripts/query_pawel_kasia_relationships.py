#!/usr/bin/env python3
"""
Query relationships between Paweł and Kasia Ju
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.db.neo4j_connection import get_neo4j_driver

def query_pawel_kasia_relationships():
    """Query all relationships between Paweł and Kasia Ju"""
    
    print("=" * 80)
    print("Relationships: Paweł Nazaruk ←→ Kasia Ju")
    print("=" * 80)
    
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        # Query all relationships between them
        print("\n🔗 ALL RELATIONSHIPS:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (p1:Person {name: 'Pawel Nazaruk'})-[r]-(p2:Person {name: 'Kasia Ju'})
            RETURN type(r) as relationship_type,
                   properties(r) as details,
                   p1.name as from_person,
                   p2.name as to_person,
                   elementId(r) as rel_id
        """)
        
        relationships = []
        for record in result:
            rel_data = {
                'type': record['relationship_type'],
                'from': record['from_person'],
                'to': record['to_person'],
                'properties': dict(record['details']),
                'id': record['rel_id']
            }
            relationships.append(rel_data)
            
            print(f"\n   Type: {record['relationship_type']}")
            print(f"   Direction: {record['from_person']} → {record['to_person']}")
            print(f"   Properties:")
            for key, value in record['details'].items():
                if isinstance(value, float):
                    print(f"     • {key}: {value:.3f}")
                else:
                    print(f"     • {key}: {value}")
        
        if not relationships:
            print("   No direct relationships found!")
        
        # Query conversation context
        print("\n\n💬 CONVERSATION CONTEXT:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (p1:Person {name: 'Pawel Nazaruk'})-[:PARTICIPATES_IN]->(c:Conversation)<-[:PARTICIPATES_IN]-(p2:Person {name: 'Kasia Ju'})
            RETURN c.title as conversation,
                   c.total_messages as messages,
                   c.duration_days as duration,
                   c.start_date as start,
                   c.end_date as end,
                   c.media_photos as photos,
                   c.media_videos as videos
        """)
        
        for record in result:
            print(f"   Conversation: {record['conversation']}")
            print(f"   Total Messages: {record['messages']}")
            print(f"   Duration: {record['duration']:.2f} days")
            print(f"   Period: {record['start']} → {record['end']}")
            print(f"   Media Shared: {record['photos']} photos, {record['videos']} videos")
        
        # Query message samples exchanged
        print("\n\n📝 MESSAGE SAMPLES:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (p:Person)-[:SENT_SAMPLE]->(m:SampleMessage)-[:PART_OF]->(c:Conversation)
            WHERE p.name IN ['Pawel Nazaruk', 'Kasia Ju']
            RETURN p.name as sender,
                   m.sample_type as type,
                   m.timestamp_iso as timestamp,
                   m.content_length as length,
                   left(m.content, 100) as preview
            ORDER BY m.timestamp
        """)
        
        for record in result:
            preview = record['preview'].replace('\n', ' ').replace('\r', '')[:100]
            print(f"\n   From: {record['sender']}")
            print(f"   Type: {record['type']}")
            print(f"   Time: {record['timestamp']}")
            print(f"   Length: {record['length']} chars")
            print(f"   Preview: {preview}...")
        
        # Query media shared by each person
        print("\n\n📸 MEDIA SHARED:")
        print("-" * 80)
        
        print("\n   Paweł Nazaruk:")
        result = session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})-[:SHARED]->(m:Media)
            RETURN m.type as type, count(m) as count
        """)
        
        for record in result:
            print(f"     • {record['type']}: {record['count']}")
        
        print("\n   Kasia Ju:")
        result = session.run("""
            MATCH (p:Person {name: 'Kasia Ju'})-[:SHARED]->(m:Media)
            RETURN m.type as type, count(m) as count
        """)
        
        for record in result:
            print(f"     • {record['type']}: {record['count']}")
        
        # Summary statistics
        print("\n\n📊 RELATIONSHIP SUMMARY:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (p1:Person {name: 'Pawel Nazaruk'})-[r:KNOWS]-(p2:Person {name: 'Kasia Ju'})
            RETURN r.relationship_type as type,
                   r.interaction_strength as strength,
                   r.conversation_context as context,
                   r.first_observed as first_seen,
                   r.last_observed as last_seen,
                   r.evidence as evidence
        """)
        
        for record in result:
            print(f"   Relationship Type: {record['type']}")
            print(f"   Interaction Strength: {record['strength']:.3f}")
            print(f"   Context: {record['context']}")
            print(f"   First Observed: {record['first_seen']}")
            print(f"   Last Observed: {record['last_seen']}")
            print(f"   Evidence: {record['evidence']}")
        
        # Export to JSON
        print("\n\n💾 EXPORT:")
        print("-" * 80)
        
        export_data = {
            'persons': ['Pawel Nazaruk', 'Kasia Ju'],
            'relationships': relationships,
            'timestamp': '2026-05-17'
        }
        
        output_file = Path(__file__).parent.parent / 'data' / 'pawel_kasia_relationships.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"   Data exported to: {output_file}")
        
    driver.close()
    
    print("\n" + "=" * 80)
    print("✅ Query complete!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        query_pawel_kasia_relationships()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
