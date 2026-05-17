#!/usr/bin/env python3
"""
Ingest Paweł Nazaruk Strategic Profile (NOI-O0-ZERO-POINT) into Neo4j
Creates comprehensive Person node with:
- Personal identity and background
- Core personality traits
- Transformation history
- Technical competencies
- Key projects
- Values and archetypes
- Connections to existing Facebook conversation data
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.db.neo4j_connection import get_neo4j_driver


def ingest_pawel_profile():
    """Ingest Paweł Nazaruk's strategic profile into Neo4j"""
    
    print("=" * 80)
    print("P-OS v8.0 — Ingesting Paweł Nazaruk Strategic Profile")
    print("Document: NOI-O0-ZERO-POINT")
    print("=" * 80)
    
    driver = get_neo4j_driver()
    
    with driver.session() as session:
        # 1. Update existing Person node with comprehensive profile
        print("\n[PHASE 1] Updating Person node with strategic profile...")
        
        session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})
            SET p.birth_year = 1980,
                p.location = 'Milejczyce, Podlasie, Polska',
                p.profile_type = 'strategic_operator',
                p.archetype = 'Inżynier odbudowy systemu życia',
                p.motto = 'Pamięć. System. Sprawczość.',
                p.operational_motto = 'Chaos przekształcić w system.',
                p.core_traits = ['realistyczny', 'techniczny', 'strategiczny', 
                                'introspektywny', 'odporny', 'narracyjny'],
                p.values = ['autonomia', 'prawda', 'sprawczość', 
                           'technologia jako narzędzie wyzwolenia',
                           'porządek informacyjny', 'pamięć', 'rozwój', 'odporność'],
                p.communication_style = ['prosty', 'mocny', 'konkretny', 
                                        'bez lania wody', 'osadzony w realiach'],
                p.long_term_goals = ['stworzenie własnego ekosystemu AI',
                                    'budowa osobistej mitologii',
                                    'porządkowanie danych życia',
                                    'rozwój projektów technologicznych',
                                    'tworzenie trwałego dziedzictwa intelektualnego',
                                    'zwiększenie autonomii psychicznej, technologicznej i finansowej'],
                p.recognized_threats = ['uzależnienia', 'chaos społeczny', 
                                       'iluzje sukcesu', 'degrengolada psychiczna',
                                       'stagnacja', 'manipulacja systemowa', 
                                       'utrata sprawczości'],
                p.last_updated = timestamp(),
                p.profile_source = 'NOI-O0-ZERO-POINT'
        """)
        
        print("   ✓ Updated Person node with strategic profile")
        
        # 2. Create transformation history nodes
        print("\n[PHASE 2] Creating transformation history...")
        
        transformations = [
            {
                'phase': 1,
                'name': 'Fundament lokalny',
                'description': 'Wychowanie w realiach Podlasia, silne zakorzenienie kulturowe, obserwacja transformacji społeczno-ekonomicznej Polski',
                'keywords': ['Podlasie', 'zakorzenienie kulturowe', 'transformacja']
            },
            {
                'phase': 2,
                'name': 'Migracja i doświadczenie zagraniczne',
                'description': 'Praca poza krajem, zdobycie perspektywy ekonomicznej i społecznej, konfrontacja z systemami zachodnimi',
                'keywords': ['migracja', 'perspektywa ekonomiczna', 'systemy zachodnie']
            },
            {
                'phase': 3,
                'name': 'Kryzysy osobiste',
                'description': 'Doświadczenia psychiatryczne, walka o stabilność, przebudowa własnej tożsamości',
                'keywords': ['kryzys', 'doświadczenia psychiatryczne', 'przebudowa tożsamości']
            },
            {
                'phase': 4,
                'name': 'Powrót i rekonstrukcja',
                'description': 'Powrót do Milejczyc, reorganizacja życia, tworzenie własnych projektów, budowa autonomicznej narracji życiowej',
                'keywords': ['powrót', 'Milejczyce', 'rekonstrukcja', 'autonomia']
            }
        ]
        
        for transformation in transformations:
            session.run("""
                MATCH (p:Person {name: 'Pawel Nazaruk'})
                MERGE (t:TransformationPhase {person: 'Pawel Nazaruk', phase: $phase})
                SET t.name = $name,
                    t.description = $description,
                    t.keywords = $keywords,
                    t.order = $phase,
                    t.created_at = timestamp()
                MERGE (p)-[:EXPERIENCED]->(t)
            """, transformation)
        
        print(f"   ✓ Created {len(transformations)} transformation phases")
        
        # 3. Create technical competencies
        print("\n[PHASE 3] Creating technical competencies...")
        
        competencies = [
            'elektroenergetyka', 'Linux/PC', 'CLI', 'Python', 
            'automatyzacja danych', 'analiza systemowa', 'AI workflows',
            'Raspberry Pi', 'ESP32', 'Arduino', 'WS2812B', 
            'infrastruktura wiedzy'
        ]
        
        work_style = [
            'preferencja terminala', 'pragmatyzm', 'modularność',
            'długofalowe projektowanie', 'wysoka potrzeba kontroli nad systemem'
        ]
        
        for competency in competencies:
            session.run("""
                MATCH (p:Person {name: 'Pawel Nazaruk'})
                MERGE (c:Competency {name: $name, category: 'technical'})
                SET c.domain = 'engineering_and_technology',
                    c.proficiency_level = 'advanced',
                    c.created_at = timestamp()
                MERGE (p)-[:HAS_COMPETENCY]->(c)
            """, {'name': competency})
        
        # Create work style as properties on Person node
        session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})
            SET p.work_style = $work_style
        """, {'work_style': work_style})
        
        print(f"   ✓ Created {len(competencies)} technical competencies")
        
        # 4. Create key projects
        print("\n[PHASE 4] Creating key projects...")
        
        projects = [
            {
                'name': 'Legacy AI Expert',
                'description': 'Rozwój eksperckiego systemu wiedzy, integracja pamięci, organizacja narracyjna, budowa cyfrowej tożsamości projektowej',
                'type': 'AI_system',
                'status': 'active'
            },
            {
                'name': 'P-OS / Ontologie systemowe',
                'description': 'Bezpieczeństwo, architektura pluginów, semantyka, warstwowe modele wiedzy',
                'type': 'operating_system',
                'status': 'active'
            },
            {
                'name': 'Milejczyce AI',
                'description': 'Lokalna historia, rozwój regionalny, OZE, cyfrowa mitologia miejsca',
                'type': 'local_development',
                'status': 'active'
            },
            {
                'name': 'Automitologia osobista',
                'description': 'Rekonstrukcja biografii, mapowanie relacji, organizacja wspomnień, narracja tożsamościowa',
                'type': 'personal_narrative',
                'status': 'active'
            }
        ]
        
        for project in projects:
            session.run("""
                MATCH (p:Person {name: 'Pawel Nazaruk'})
                MERGE (proj:Project {name: $name})
                SET proj.description = $description,
                    proj.type = $type,
                    proj.status = $status,
                    proj.owner = 'Pawel Nazaruk',
                    proj.created_at = timestamp()
                MERGE (p)-[:OWNS]->(proj)
            """, project)
        
        print(f"   ✓ Created {len(projects)} key projects")
        
        # 5. Connect to existing Facebook conversation data
        print("\n[PHASE 5] Connecting to existing data...")
        
        # Link to Facebook conversation
        session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})
            MATCH (c:Conversation {title: 'Kasia Ju'})
            MERGE (p)-[:PARTICIPATES_IN {role: 'active_participant', messages_sent: 3910}]->(c)
        """)
        
        # Count existing relationships
        result = session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})-[r]->()
            RETURN count(r) as total_relationships
        """)
        
        total_rels = result.single()['total_relationships']
        print(f"   ✓ Connected to existing graph ({total_rels} total relationships)")
        
        # 6. Create psychological profile
        print("\n[PHASE 6] Creating psychological profile...")
        
        personality_core = {
            'system_thinking': 'high',
            'long_term_analysis': 'high',
            'psychological_resilience': 'high_post_crisis',
            'autonomy_need': 'very_high',
            'critical_view': 'high',
            'agency_rebuilding': 'active'
        }
        
        relational_psychology = {
            'analyzes_relationships': 'intensive',
            'studies_dominance_dynamics': True,
            'maps_social_structures': True,
            'seeks_authenticity': True,
            'cautious_of_manipulation': True,
            'values_loyalty': 'very_high',
            'values_truthfulness': 'very_high'
        }
        
        analysis_domains = ['rodzina', 'znajomi', 'lokalne środowisko',
                           'relacje pokoleniowe', 
                           'społeczne mechanizmy upadku i odbudowy']
        
        session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})
            SET p.personality_core_system_thinking = $personality.system_thinking,
                p.personality_core_long_term_analysis = $personality.long_term_analysis,
                p.personality_core_psychological_resilience = $personality.psychological_resilience,
                p.personality_core_autonomy_need = $personality.autonomy_need,
                p.personality_core_critical_view = $personality.critical_view,
                p.personality_core_agency_rebuilding = $personality.agency_rebuilding,
                p.relational_analyzes_relationships = $relational.analyzes_relationships,
                p.relational_studies_dominance_dynamics = $relational.studies_dominance_dynamics,
                p.relational_maps_social_structures = $relational.maps_social_structures,
                p.relational_seeks_authenticity = $relational.seeks_authenticity,
                p.relational_cautious_of_manipulation = $relational.cautious_of_manipulation,
                p.relational_values_loyalty = $relational.values_loyalty,
                p.relational_values_truthfulness = $relational.values_truthfulness,
                p.analysis_domains = $domains
        """, {'personality': personality_core, 'relational': relational_psychology, 'domains': analysis_domains})
        
        print("   ✓ Created psychological profile")
        
        # 7. Create operational identity
        print("\n[PHASE 7] Creating operational identity...")
        
        session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})
            SET p.operator_title = 'Operator Wielki Elektronik',
                p.identity_formula = 'Paweł = Paweł Nazaruk Operator Wielki Elektronik',
                p.strategic_role = 'system_reconstruction_engineer',
                p.transformation_profile = 'crisis_to_system_builder'
        """)
        
        print("   ✓ Created operational identity")
        
        # 8. Verification query
        print("\n[PHASE 8] Verifying ingestion...")
        
        result = session.run("""
            MATCH (p:Person {name: 'Pawel Nazaruk'})
            OPTIONAL MATCH (p)-[:EXPERIENCED]->(t:TransformationPhase)
            OPTIONAL MATCH (p)-[:HAS_COMPETENCY]->(c:Competency)
            OPTIONAL MATCH (p)-[:CREATED|:OWNS]->(proj:Project)
            OPTIONAL MATCH (p)-[:PARTICIPATES_IN]->(conv:Conversation)
            RETURN p.name as name,
                   p.archetype as archetype,
                   p.motto as motto,
                   count(DISTINCT t) as transformation_phases,
                   count(DISTINCT c) as competencies,
                   count(DISTINCT proj) as projects,
                   count(DISTINCT conv) as conversations
        """)
        
        record = result.single()
        print(f"\n   ✅ Verification Results:")
        print(f"      Name: {record['name']}")
        print(f"      Archetype: {record['archetype']}")
        print(f"      Motto: {record['motto']}")
        print(f"      Transformation Phases: {record['transformation_phases']}")
        print(f"      Competencies: {record['competencies']}")
        print(f"      Projects: {record['projects']}")
        print(f"      Conversations: {record['conversations']}")
        
    driver.close()
    
    print("\n" + "=" * 80)
    print("[SUCCESS] Paweł Nazaruk Strategic Profile ingested successfully!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Query profile: python scripts/query_facebook_ontology.py profile 'Pawel Nazaruk'")
    print("2. View in Neo4j Browser: MATCH (p:Person {name: 'Pawel Nazaruk'}) RETURN p")
    print("3. Explore connections: MATCH (p:Person {name: 'Pawel Nazaruk'})-->() RETURN count(*)")
    print("=" * 80)


if __name__ == '__main__':
    try:
        ingest_pawel_profile()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
