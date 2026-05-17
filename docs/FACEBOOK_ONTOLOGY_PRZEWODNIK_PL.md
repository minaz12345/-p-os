# Interfejs Ontologii Konwersacji Facebook - Przewodnik

## Przegląd

Stworzono kompletny interfejs do zapisu danych z konwersacji Facebook w bazie Neo4j w postaci skondensowanej ontologii osób i ich relacji.

## Struktura Ontologii

### Węzły (Nodes)

1. **Person (Osoba)** - Uczestnicy konwersacji
   - Imię i nazwisko
   - Liczba wiadomości
   - Procent udziału w rozmowie
   - Rola w konwersacji

2. **Conversation (Konwersacja)** - Wątek rozmowy ze statystykami
   - Tytuł konwersacji
   - Łączna liczba wiadomości
   - Zakres czasowy
   - Podsumowanie mediów

3. **Message (Wiadomość)** - Wybrane przykładowe wiadomości
   - Pierwsza wiadomość
   - Ostatnia wiadomość
   - Najdłuższa/najkrótsza
   - Próbki z ostatniego tygodnia

4. **Media** - Pliki multimedialne
   - Zdjęcia, wideo, GIF-y
   - Ścieżki do plików
   - Metadane

### Relacje

- **KNOWS** - Osoby znają się (dwukierunkowa)
- **MENTIONS** - Jedna osoba wspomina drugą
- **PARTICIPATES_IN** - Osoba uczestniczy w konwersacji
- **SENT_SAMPLE** - Osoba wysłała przykładową wiadomość
- **SHARED** - Osoba udostępniła media

## Instalacja i Użycie

### 1. Import Danych

```bash
cd d:\pos7
python scripts/ingest_facebook_conversation_ontology.py
```

Skrypt automatycznie:
- ✓ Wczyta konwersację z `Facebook/kasiaju_1977350892357109/message_1.json`
- ✓ Przeanalizuje wzorce konwersacji
- ✓ Utworzy węzły Person dla Kasia Ju i Pawel Nazaruk
- ✓ StworzyConversation ze statystykami
- ✓ Zapisze przykładowe wiadomości
- ✓ Wywnioskuje relacje KNOWS między osobami
- ✓ Śledzi pliki multimedialne

### 2. Zapytania Interaktywne

```bash
python scripts/query_facebook_ontology.py
```

Dostępne komendy:
- `profile <nazwa>` - Profil osoby
- `relationships <osoba1> <osoba2>` - Relacje między osobami
- `timeline <nazwa>` - Oś czasu interakcji
- `media <nazwa>` - Udostępnione media
- `patterns` - Analiza wzorców konwersacji
- `export <nazwa> [plik]` - Eksport ontologii do JSON
- `quit` - Wyjście

### 3. Zapytania z Linii Poleceń

```bash
# Profil osoby
python scripts/query_facebook_ontology.py profile "Pawel Nazaruk"

# Eksport ontologii
python scripts/query_facebook_ontology.py export "Kasia Ju" kasia_ontology.json
```

## Przykłady Zapytań Cypher

### Profil Pawła

```cypher
MATCH (p:Person {name: 'Pawel Nazaruk'})
RETURN p.name, p.message_count, p.participation_percentage, p.role_in_conversation
```

### Relacje między Kasią i Pawłem

```cypher
MATCH (k:Person {name: 'Kasia Ju'})-[r]-(p:Person {name: 'Pawel Nazaruk'})
RETURN type(r) as typ_relacji, r.relationship_type, r.interaction_strength
```

### Statystyki Konwersacji

```cypher
MATCH (c:Conversation)
RETURN c.title, c.total_messages, c.duration_days, c.media_summary
```

### Oś Czasu Wiadomości Pawła

```cypher
MATCH (p:Person {name: 'Pawel Nazaruk'})-[:SENT_SAMPLE]->(m:SampleMessage)
RETURN m.timestamp_iso, m.sample_type, m.content_length
ORDER BY m.timestamp
```

## Strategia Skondensowanego Zapisu

Zamiast zapisywać wszystkie ~61,861 wiadomości, system zapisuje:

1. **Statystyki Agregowane** (w węźle Conversation):
   - Łączna liczba wiadomości
   - Rozkład między uczestników
   - Zakres czasowy
   - Średnia długość wiadomości
   - Liczba plików multimedialnych

2. **Strategiczne Próbki** (5-15 wiadomości):
   - Pierwsza wiadomość (początek rozmowy)
   - Ostatnia wiadomość (koniec rozmowy)
   - Najdłuższa wiadomość (najbardziej szczegółowa)
   - Najkrótsza wiadomość (najbardziej zwięzła)
   - Do 10 próbek z ostatniego tygodnia

3. **Wywnioskowane Relacje**:
   - KNOWS z metrykami siły interakcji
   - MENTIONS z licznikami
   - Klasyfikacje ról na podstawie udziału

**Redukcja存储: ~99.9%** przy zachowaniu znaczenia semantycznego!

## Dokumentacja

Pełna dokumentacja schematu ontologii:
- `docs/FACEBOOK_ONTOLOGY_SCHEMA.md` - Szczegółowy opis schematu

## Integracja z P-OS v8.0

Interfejs integruje się z istniejącym systemem:
- ✓ Używa tego samego menedżera połączeń Neo4j
- ✓ Zachowuje zgodność z istniejącymi węzłami Person
- ✓ Kompatybilny z istniejącymi interfejsami zapytań
- ✓ Rozszerza graf wiedzy o warstwę interakcji społecznych

## Następne Kroki

Po zaimportowaniu danych możesz:

1. **Analizować relacje** między osobami
2. **Eksportować ontologie** do dalszej analizy
3. **Wizualizować graf** w Neo4j Browser
4. **Łączyć z innymi danymi** w grafie wiedzy P-OS
5. **Rozbudowywać** o analizę NLP (sentiment, tematy)

## Rozwiązywanie Problemów

### Błąd Połączenia z Neo4j

Upewnij się, że Neo4j jest uruchomiony:
```bash
# Sprawdź status Neo4j
neo4j status

# Uruchom jeśli potrzeba
neo4j start
```

### Brak Danych po Importie

Sprawdź czy plik konwersacji istnieje:
```bash
ls Facebook/kasiaju_1977350892357109/message_1.json
```

### Błędy Kodowania

Skrypt automatycznie obsługuje kodowanie UTF-8 dla polskich znaków.

## Autor

Stworzono dla systemu P-OS v8.0 jako część infrastruktury ontologicznej.
