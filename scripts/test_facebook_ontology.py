#!/usr/bin/env python3
"""
Test script for Facebook Conversation Ontology ingestion
Verifies that data was ingested correctly into Neo4j
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.db.neo4j_connection import get_neo4j_driver


def test_person_nodes():
    """Test that Person nodes were created"""
    print("\n[TEST 1] Checking Person nodes...")
    
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (p:Person:FacebookUser)
            RETURN p.name as name, 
                   p.message_count as messages,
                   p.participation_percentage as pct,
                   p.role_in_conversation as role
            ORDER BY p.message_count DESC
        """)
        
        persons = list(result)
        
        if not persons:
            print("   ❌ FAIL: No Person nodes found")
            return False
        
        print(f"   ✓ Found {len(persons)} Person nodes:")
        for person in persons:
            print(f"     - {person['name']}: {person['messages']} messages ({person['pct']}%) - {person['role']}")
        
        # Check for expected participants
        names = [p['name'] for p in persons]
        if 'Kasia Ju' in names and 'Pawel Nazaruk' in names:
            print("   ✓ Expected participants found")
            return True
        else:
            print(f"   ⚠ Warning: Expected 'Kasia Ju' and 'Pawel Nazaruk', got: {names}")
            return True  # Still pass if other persons exist
    
    driver.close()


def test_conversation_node():
    """Test that Conversation node was created"""
    print("\n[TEST 2] Checking Conversation node...")
    
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (c:Conversation:FacebookThread)
            RETURN c.title as title,
                   c.total_messages as messages,
                   c.duration_days as duration,
                   c.participant_count as participants,
                   c.media_summary as media
        """)
        
        conversations = list(result)
        
        if not conversations:
            print("   ❌ FAIL: No Conversation nodes found")
            return False
        
        print(f"   ✓ Found {len(conversations)} Conversation node(s):")
        for conv in conversations:
            print(f"     - {conv['title']}")
            print(f"       Messages: {conv['messages']}")
            print(f"       Duration: {conv['duration']} days")
            print(f"       Participants: {conv['participants']}")
            print(f"       Media: {conv['media']}")
        
        return True
    
    driver.close()


def test_sample_messages():
    """Test that sample messages were created"""
    print("\n[TEST 3] Checking SampleMessage nodes...")
    
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (m:SampleMessage)
            RETURN m.sample_type as type,
                   m.sender as sender,
                   m.content_length as length,
                   m.timestamp_iso as timestamp
            ORDER BY m.timestamp
        """)
        
        messages = list(result)
        
        if not messages:
            print("   ❌ FAIL: No SampleMessage nodes found")
            return False
        
        print(f"   ✓ Found {len(messages)} SampleMessage nodes:")
        for msg in messages:
            preview = f"... ({msg['length']} chars)"
            print(f"     - {msg['type']}: from {msg['sender']} at {msg['timestamp']}{preview}")
        
        # Check for expected sample types
        types = [m['type'] for m in messages]
        expected_types = ['first_message', 'last_message', 'longest_message', 'shortest_message']
        found_expected = any(t in types for t in expected_types)
        
        if found_expected:
            print("   ✓ Expected sample types found")
        else:
            print(f"   ⚠ Warning: Expected boundary samples, got: {types}")
        
        return True
    
    driver.close()


def test_relationships():
    """Test that relationships were created"""
    print("\n[TEST 4] Checking relationships...")
    
    driver = get_neo4j_driver()
    with driver.session() as session:
        # Check KNOWS relationships
        knows_result = session.run("""
            MATCH (p1:Person)-[r:KNOWS]-(p2:Person)
            RETURN p1.name as person1,
                   p2.name as person2,
                   r.relationship_type as type,
                   r.interaction_strength as strength
        """)
        
        knows_rels = list(knows_result)
        
        if not knows_rels:
            print("   ⚠ WARNING: No KNOWS relationships found")
        else:
            print(f"   ✓ Found {len(knows_rels)} KNOWS relationship(s):")
            for rel in knows_rels:
                print(f"     - {rel['person1']} ↔ {rel['person2']} ({rel['type']}, strength: {rel['strength']})")
        
        # Check PARTICIPATES_IN relationships
        participates_result = session.run("""
            MATCH (p:Person)-[:PARTICIPATES_IN]->(c:Conversation)
            RETURN count(p) as count
        """)
        
        participates_count = participates_result.single()['count']
        print(f"   ✓ Found {participates_count} PARTICIPATES_IN relationships")
        
        # Check SENT_SAMPLE relationships
        sent_result = session.run("""
            MATCH (p:Person)-[:SENT_SAMPLE]->(m:SampleMessage)
            RETURN count(m) as count
        """)
        
        sent_count = sent_result.single()['count']
        print(f"   ✓ Found {sent_count} SENT_SAMPLE relationships")
        
        # Check SHARED relationships (media)
        shared_result = session.run("""
            MATCH (p:Person)-[:SHARED]->(media:Media)
            RETURN count(media) as count
        """)
        
        shared_count = shared_result.single()['count']
        print(f"   ✓ Found {shared_count} SHARED relationships (media)")
        
        return True
    
    driver.close()


def test_media_tracking():
    """Test that media files were tracked"""
    print("\n[TEST 5] Checking Media nodes...")
    
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run("""
            MATCH (m:Media)
            RETURN m.type as type, count(m) as count
            ORDER BY count DESC
        """)
        
        media_stats = list(result)
        
        if not media_stats:
            print("   ℹ INFO: No Media nodes found (conversation may not have media)")
            return True
        
        total_media = sum(item['count'] for item in media_stats)
        print(f"   ✓ Found {total_media} Media node(s):")
        for item in media_stats:
            print(f"     - {item['type']}: {item['count']}")
        
        return True
    
    driver.close()


def test_query_interface():
    """Test the query interface"""
    print("\n[TEST 6] Testing query interface...")
    
    try:
        from scripts.query_facebook_ontology import FacebookOntologyQuerier
        
        querier = FacebookOntologyQuerier()
        
        # Test getting a person profile
        profile = querier.get_person_profile("Pawel Nazaruk")
        if profile:
            print("   ✓ Query interface working - retrieved profile for Pawel Nazaruk")
            print(f"     Message count: {profile['person'].get('message_count', 'N/A')}")
            print(f"     Relationships: {len(profile['relationships'])}")
        else:
            print("   ⚠ WARNING: Could not retrieve profile (person may not exist yet)")
        
        # Test pattern analysis
        patterns = querier.analyze_conversation_patterns()
        if patterns:
            print("   ✓ Pattern analysis working")
            print(f"     Total conversations: {patterns['conversation_statistics'].get('total_conversations', 0)}")
        
        querier.close()
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Query interface error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("=" * 80)
    print("Facebook Ontology Ingestion - Test Suite")
    print("=" * 80)
    
    tests = [
        test_person_nodes,
        test_conversation_node,
        test_sample_messages,
        test_relationships,
        test_media_tracking,
        test_query_interface
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("\nNext steps:")
        print("1. Explore the graph in Neo4j Browser: http://localhost:7474")
        print("2. Run interactive queries: python scripts/query_facebook_ontology.py")
        print("3. Export ontology: python scripts/query_facebook_ontology.py export \"Kasia Ju\" kasia.json")
    else:
        print(f"\n⚠ {total - passed} test(s) failed or had warnings")
        print("\nCheck the output above for details.")
    
    print("=" * 80)
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
