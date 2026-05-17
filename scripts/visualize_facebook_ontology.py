#!/usr/bin/env python3
"""
Quick visualization of Facebook Ontology in Neo4j
Displays the graph structure in text format
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.db.neo4j_connection import get_neo4j_driver

def visualize_graph():
    """Query and display the Facebook ontology graph"""
    
    print("=" * 80)
    print("Facebook Conversation Ontology - Graph Visualization")
    print("=" * 80)
    
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        # 1. Show all nodes by type
        print("\n📊 NODE SUMMARY:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] as node_type, count(n) as count
            ORDER BY count DESC
        """)
        
        for record in result:
            print(f"   {record['node_type']:25} : {record['count']}")
        
        # 2. Show Person details
        print("\n👥 PERSONS:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (p:Person)
            RETURN p.name as name, 
                   p.message_count as messages,
                   p.participation_percentage as pct,
                   p.role_in_conversation as role
            ORDER BY p.message_count DESC
        """)
        
        for record in result:
            print(f"   • {record['name']}")
            print(f"     Messages: {record['messages']} ({record['pct']}%)")
            print(f"     Role: {record['role']}")
            print()
        
        # 3. Show Conversation details
        print("\n💬 CONVERSATION:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (c:Conversation)
            RETURN c.title as title,
                   c.total_messages as messages,
                   c.duration_days as duration,
                   c.start_date as start,
                   c.end_date as end,
                   c.media_photos as photos,
                   c.media_videos as videos
        """)
        
        for record in result:
            print(f"   Title: {record['title']}")
            print(f"   Total Messages: {record['messages']}")
            print(f"   Duration: {record['duration']:.2f} days")
            print(f"   Period: {record['start']} → {record['end']}")
            print(f"   Media: {record['photos']} photos, {record['videos']} videos")
            print()
        
        # 4. Show Relationships
        print("\n🔗 RELATIONSHIPS:")
        print("-" * 80)
        
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as rel_type, count(r) as count
            ORDER BY count DESC
        """)
        
        for record in result:
            print(f"   {record['rel_type']:25} : {record['count']}")
        
        # 5. Show KNOWS relationship details
        print("\n🤝 SOCIAL CONNECTIONS:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (p1:Person)-[r:KNOWS]-(p2:Person)
            RETURN p1.name as person1,
                   p2.name as person2,
                   r.relationship_type as type,
                   r.interaction_strength as strength
        """)
        
        for record in result:
            print(f"   {record['person1']} ←→ {record['person2']}")
            print(f"     Type: {record['type']}")
            print(f"     Strength: {record['strength']:.3f}")
            print()
        
        # 6. Show Sample Messages
        print("\n📝 SAMPLE MESSAGES:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (m:SampleMessage)
            RETURN m.sample_type as type,
                   m.sender as sender,
                   m.content_length as length,
                   left(m.content, 80) as preview
            ORDER BY m.timestamp
        """)
        
        for record in result:
            preview = record['preview'].replace('\n', ' ')[:80]
            print(f"   [{record['type']}]")
            print(f"     From: {record['sender']}")
            print(f"     Length: {record['length']} chars")
            print(f"     Preview: {preview}...")
            print()
        
        # 7. Show Media
        print("\n📸 MEDIA FILES:")
        print("-" * 80)
        
        result = session.run("""
            MATCH (m:Media)
            RETURN m.type as type, count(m) as count
            ORDER BY count DESC
        """)
        
        for record in result:
            print(f"   {record['type']:15} : {record['count']}")
        
        # 8. Complete graph query
        print("\n🌐 GRAPH STRUCTURE QUERY:")
        print("-" * 80)
        print("To visualize in Neo4j Browser, run:")
        print()
        print("   MATCH (n) RETURN n LIMIT 25")
        print()
        print("Or for relationships:")
        print()
        print("   MATCH (p1:Person)-[r]-(p2:Person) RETURN p1, r, p2")
        print()
        
    driver.close()
    
    print("=" * 80)
    print("✅ Graph visualization complete!")
    print("=" * 80)


if __name__ == '__main__':
    try:
        visualize_graph()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
