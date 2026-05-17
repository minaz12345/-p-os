# Facebook Conversation Ontology Schema

## Overview

This document describes the ontology schema used to store Facebook Messenger conversation data in Neo4j as a condensed knowledge graph representation.

## Design Principles

1. **Condensed Storage**: Store aggregated statistics and sample messages instead of every individual message
2. **Relationship Inference**: Derive social relationships from conversation patterns
3. **Temporal Tracking**: Maintain temporal aspects of interactions
4. **Media Tracking**: Reference media files without storing binary data
5. **Idempotent Ingestion**: Safe to run multiple times without duplication

## Node Types

### 1. Person (FacebookUser)

Represents participants in conversations.

**Properties:**
- `name` (string, unique identifier)
- `source` = 'facebook_messenger'
- `message_count` (integer) - Total messages sent
- `participation_percentage` (float) - Percentage of total conversation
- `role_in_conversation` (string) - Inferred role:
  - `primary_contributor` (>70% of messages)
  - `active_participant` (40-70%)
  - `occasional_participant` (20-40%)
  - `minimal_participant` (<20%)
- `last_updated` (timestamp)

**Labels:** `Person`, `FacebookUser`

### 2. Conversation (FacebookThread)

Represents a conversation thread with aggregated statistics.

**Properties:**
- `thread_id` (string, unique identifier) - Derived from thread_path or title
- `title` (string) - Conversation title
- `thread_path` (string) - Original Facebook thread path
- `total_messages` (integer) - Total message count
- `participant_count` (integer) - Number of participants
- `duration_days` (float) - Conversation span in days
- `start_date` (ISO datetime) - First message timestamp
- `end_date` (ISO datetime) - Last message timestamp
- `avg_message_length` (float) - Average characters per message
- `total_characters` (integer) - Total characters in conversation
- `media_summary` (map) - Count of photos, videos, gifs, etc.
- `ingested_at` (timestamp)
- `data_source` = 'facebook_export'

**Labels:** `Conversation`, `FacebookThread`

### 3. Message (SampleMessage)

Represents strategically selected sample messages (not all messages).

**Sample Types:**
- `first_message` - Chronologically first message
- `last_message` - Chronologically last message
- `longest_message` - Message with most characters
- `shortest_message` - Message with fewest characters
- `recent_week_sample_0..9` - Up to 10 messages from final week

**Properties:**
- `thread_id` (string) - Parent conversation
- `sample_type` (string) - Type of sample
- `content` (string, max 1000 chars) - Message text
- `sender` (string) - Person who sent it
- `timestamp` (integer) - Unix timestamp in milliseconds
- `timestamp_iso` (ISO datetime) - Human-readable timestamp
- `content_length` (integer) - Character count
- `mentioned_persons` (list) - Names mentioned in content
- `has_media` (boolean) - Whether message contains media
- `stored_at` (timestamp)

**Labels:** `Message`, `SampleMessage`

### 4. Media

Represents media files shared in conversations.

**Properties:**
- `uri` (string, unique identifier) - File path/URI
- `type` (string) - 'photo', 'video', 'gif', 'audio', 'file'
- `sender` (string) - Person who shared it
- `creation_timestamp` (integer) - When media was created
- `tracked_at` (timestamp) - When ingested

**Labels:** `Media`, plus specific type (Photo, Video, etc.)

## Relationship Types

### 1. PARTICIPATES_IN

**Pattern:** `(Person)-[:PARTICIPATES_IN]->(Conversation)`

Links persons to conversations they participated in.

**Properties:** None (structural relationship)

### 2. SENT_SAMPLE

**Pattern:** `(Person)-[:SENT_SAMPLE {type: sample_type}]->(Message)`

Links person to their sample messages.

**Properties:**
- `type` (string) - Sample type (first_message, last_message, etc.)

### 3. PART_OF

**Pattern:** `(Message)-[:PART_OF]->(Conversation)`

Links sample messages to their parent conversation.

**Properties:** None (structural relationship)

### 4. KNOWS

**Pattern:** `(Person)-[r:KNOWS]-(Person)`

Bidirectional relationship between conversation participants.

**Properties:**
- `relationship_type` (string) - Inferred type:
  - `peer` - Balanced conversation (±30%)
  - `initiator_responder` - One person initiates more
  - `responder_initiator` - Other person initiates more
- `interaction_strength` (float, 0-1) - Ratio of min messages to total
- `conversation_context` = 'facebook_messenger'
- `first_observed` (ISO datetime) - Earliest message
- `last_observed` (ISO datetime) - Latest message
- `evidence` = 'conversation_analysis'

### 5. MENTIONS

**Pattern:** `(Person)-[r:MENTIONS]->(Person)`

Directional relationship when one person mentions another.

**Properties:**
- `mention_count` (integer) - Number of times mentioned
- `last_mentioned` (timestamp) - Most recent mention

### 6. SHARED

**Pattern:** `(Person)-[:SHARED]->(Media)`

Links person to media they shared.

**Properties:** None (structural relationship)

## Example Queries

### Get Person Profile

```cypher
MATCH (p:Person {name: 'Pawel Nazaruk'})
OPTIONAL MATCH (p)-[:PARTICIPATES_IN]->(c:Conversation)
OPTIONAL MATCH (p)-[r:KNOWS]-(other:Person)
RETURN p, 
       collect(c.title) as conversations,
       collect({person: other.name, type: r.relationship_type}) as relationships
```

### Find All Relationships Between Two People

```cypher
MATCH (p1:Person {name: 'Kasia Ju'})-[r]-(p2:Person {name: 'Pawel Nazaruk'})
RETURN type(r) as relationship, properties(r) as details
```

### Get Conversation Statistics

```cypher
MATCH (c:Conversation)
RETURN c.title,
       c.total_messages,
       c.duration_days,
       c.participant_count,
       c.media_summary
ORDER BY c.total_messages DESC
```

### Timeline of Interactions

```cypher
MATCH (p:Person {name: 'Pawel Nazaruk'})-[:SENT_SAMPLE]->(m:SampleMessage)
RETURN m.timestamp_iso, m.sample_type, m.content_length
ORDER BY m.timestamp
```

### Media Shared by Person

```cypher
MATCH (p:Person {name: 'Kasia Ju'})-[:SHARED]->(media:Media)
RETURN media.type, media.uri, media.creation_timestamp
ORDER BY media.creation_timestamp DESC
```

## Condensed Storage Strategy

Instead of storing all ~61,861 messages, we store:

1. **Aggregated Statistics** (in Conversation node):
   - Total message count
   - Participant distribution
   - Time range and duration
   - Average message length
   - Media counts

2. **Strategic Samples** (5-15 messages per conversation):
   - First message (conversation start)
   - Last message (conversation end)
   - Longest message (most detailed)
   - Shortest message (briefest)
   - Recent week samples (up to 10, showing current state)

3. **Inferred Relationships**:
   - KNOWS relationships with strength metrics
   - MENTIONS relationships with counts
   - Role classifications based on participation

This reduces storage by ~99.9% while preserving semantic meaning and enabling relationship analysis.

## Usage

### Ingestion

```bash
python scripts/ingest_facebook_conversation_ontology.py
```

### Querying (Interactive)

```bash
python scripts/query_facebook_ontology.py
```

### Querying (Command Line)

```bash
# Get person profile
python scripts/query_facebook_ontology.py profile "Pawel Nazaruk"

# Export ontology
python scripts/query_facebook_ontology.py export "Kasia Ju" kasia_ontology.json
```

## Integration with P-OS v8.0

This ontology integrates with the existing P-OS knowledge graph:

- Uses same Neo4j connection manager (`core.db.neo4j_connection`)
- Follows established Person node pattern from `ingest_milejczyce_ontology.py`
- Compatible with existing query interfaces
- Extends ontology with social interaction layer

## Future Enhancements

1. **NLP Analysis**: Sentiment analysis, topic modeling
2. **Network Analysis**: Centrality measures, community detection
3. **Temporal Patterns**: Activity heatmaps, response time analysis
4. **Cross-Conversation Links**: Connect related conversations
5. **Entity Extraction**: Named entity recognition from message content
