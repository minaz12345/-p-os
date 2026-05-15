#!/usr/bin/env python3
"""
P-OS v7.5 - Milejczyce Ontology Ingestion (NOI-O1)
Ingests the core knowledge graph from the certified ontology document.
"""

from neo4j import GraphDatabase
import sys

# Configuration
NEO4J_URI = "bolt+ssc://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "YU54kxF&ahGu@FNQrtNDXlfS%sHkukJD"

def ingest_ontology(driver):
    """Ingest the Milejczyce Core Ontology into Neo4j"""
    
    with driver.session() as session:
        print("[PHASE 1] Ingesting Executive & Legislative Actors...")
        
        # 1. Wójt and Deputy
        session.run("""
            MERGE (w:Person {name: 'Sebastian Sawicki'})
            SET w.role = 'Wójt', w.elected = 2024, w.mandate_pct = 59.65, 
                w.grandfather = 'Ananiasz Sawicki', w.vision = 'Uzdrowisko'
            MERGE (d:Person {name: 'Piotr Hryniewicki'})
            SET d.role = 'Zastępca Wójta / Kierownik RI', d.specialty = 'Infrastruktura/Drogi'
            MERGE (w)-[:DELEGATES_TO]->(d)
        """)

        # 2. Key Administration
        session.run("""
            MERGE (s:Person {name: 'Bogumiła Dietrich'}) SET s.role = 'Sekretarz Gminy'
            MERGE (t:Person {name: 'Joanna'}) SET t.role = 'Skarbnik Gminy'
            MERGE (g:Person {name: 'Piotr Robert Molski'}) SET g.role = 'Kierownik GOPS'
            MERGE (u:Person {name: 'Urszula Molska'}) SET u.role = 'Dyrektor SP Milejczyce'
            MERGE (k:Person {name: 'Katarzyna Wysocka'}) SET k.role = 'Kierownik Biblioteki'
            MERGE (m:Person {name: 'Monika Bałut'}) SET m.role = 'Dyrektor GOK'
        """)

        # 3. Council Leadership
        session.run("""
            MERGE (c1:Person {name: 'Tomasz Nesterowicz'}) SET c1.role = 'Przewodniczący Rady'
            MERGE (c2:Person {name: 'Aleksander Oniśkiewicz'}) SET c2.role = 'Wiceprzewodniczący Rady'
            MERGE (c1)-[:CHAIRS]->(:Commission {name: 'Rada Gminy'})
            MERGE (c2)-[:CHAIRS]->(:Commission {name: 'Komisja Budżetu i Rozwoju'})
        """)

        print("[PHASE 2] Ingesting Historical Legitimacy...")
        
        # 4. Historical Events
        session.run("""
            MERGE (h1:HistoricalEvent {year: 1136, name: 'Bulla Gnieźnieńska'})
            SET h1.description = 'Pierwsza wzmianka imienia Milejko'
            MERGE (h2:HistoricalEvent {year: 1516, name: 'Nadanie Praw Miejskich'})
            SET h2.description = 'Zygmunt I Stary, Stacja Królewska'
            MERGE (h3:HistoricalEvent {year: 1566, name: 'Nadanie Herbu'})
            SET h3.description = 'Złote rogi jelenia z dębu na czerwonym polu'
            MERGE (h4:HistoricalEvent {year: 1918, name: 'Administracja UNR'})
            SET h4.description = 'Krótki okres ukraińskiej administracji i szkolnictwa'
        """)

        print("[PHASE 3] Ingesting Strategic Projects (Uzdrowisko)...")
        
        # 5. Uzdrowisko Strategy
        session.run("""
            MERGE (p:Project {name: 'Status Uzdrowiska'})
            SET p.status = 'Faza A: Badania Klimatyczne', p.duration_years = 2,
                p.political_weight = 2.0, p.resolution_date = '2026-03'
            MERGE (p)-[:REQUIRES]->(:LegalBasis {name: 'Uchwała o Zobowiązaniach Wieloletnich'})
            MERGE (p)-[:AIMS_TO_CREATE]->(:Concept {name: 'Tarcza Ekologiczna'})
        """)

        print("[PHASE 4] Ingesting Social Graph & Organizations...")
        
        # 6. Community Organizations
        session.run("""
            MERGE (o1:CommunityOrganization {name: 'OSP Milejczyce'})
            SET o1.president = 'Dominik Dobrowolski', o1.type = 'Fire Brigade'
            MERGE (o2:CommunityOrganization {name: 'KGW Pokaniewo Kolonia'})
            SET o2.award = 'Top Regionu 2020'
            MERGE (o3:CommunityOrganization {name: 'Stowarzyszenie Wędkarskie "Raczek"'})
            SET o3.focus = 'Zbiornik Wał, Retencja Wód'
        """)

        print("[COMPLETE] Ontology Ingestion Finished.")

def main():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        driver.verify_connectivity()
        print("[OK] Connected to Neo4j for Ontology Ingestion\n")
        ingest_ontology(driver)
    except Exception as e:
        print(f"[ERROR] {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
