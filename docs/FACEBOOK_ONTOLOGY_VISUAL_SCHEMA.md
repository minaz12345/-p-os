# Facebook Ontology - Visual Schema

## Graph Structure Diagram

```mermaid
graph TB
    subgraph Persons
        P1[Person: Kasia Ju<br/>message_count: 35000<br/>role: primary_contributor]
        P2[Person: Pawel Nazaruk<br/>message_count: 26861<br/>role: active_participant]
    end
    
    subgraph Conversation
        C[Conversation: Kasia Ju<br/>total_messages: 61861<br/>duration_days: 1200.5<br/>media: 33 photos, 1 video]
    end
    
    subgraph SampleMessages
        M1[Message: first_message<br/>timestamp: 2019-01-31<br/>sender: Pawel]
        M2[Message: last_message<br/>timestamp: 2022-05-14<br/>sender: Kasia]
        M3[Message: longest_message<br/>length: 450 chars<br/>sender: Kasia]
        M4[Message: shortest_message<br/>length: 2 chars<br/>sender: Pawel]
        M5[Message: recent_week_sample_0<br/>timestamp: 2022-05-10<br/>sender: Pawel]
    end
    
    subgraph Media
        PH1[Media: Photo<br/>uri: photos/2205507433077439.jpg<br/>type: photo]
        PH2[Media: Photo<br/>uri: photos/345553066069292.jpg<br/>type: photo]
        V1[Media: Video<br/>uri: videos/2664970333561433.mp4<br/>type: video]
    end
    
    P1 -->|PARTICIPATES_IN| C
    P2 -->|PARTICIPATES_IN| C
    
    P1 -.->|KNOWS peer<br/>strength: 0.434| P2
    
    P1 -->|SENT_SAMPLE type:first_message| M1
    P2 -->|SENT_SAMPLE type:last_message| M2
    P1 -->|SENT_SAMPLE type:longest_message| M3
    P2 -->|SENT_SAMPLE type:shortest_message| M4
    P2 -->|SENT_SAMPLE type:recent_week_sample_0| M5
    
    M1 -->|PART_OF| C
    M2 -->|PART_OF| C
    M3 -->|PART_OF| C
    M4 -->|PART_OF| C
    M5 -->|PART_OF| C
    
    P1 -->|SHARED| PH1
    P1 -->|SHARED| PH2
    P2 -->|SHARED| V1
    
    style P1 fill:#e1f5ff
    style P2 fill:#e1f5ff
    style C fill:#fff4e1
    style M1 fill:#f0f0f0
    style M2 fill:#f0f0f0
    style M3 fill:#f0f0f0
    style M4 fill:#f0f0f0
    style M5 fill:#f0f0f0
    style PH1 fill:#ffe1f0
    style PH2 fill:#ffe1f0
    style V1 fill:#ffe1f0
```

## Relationship Types Legend

### Solid Lines (→) - Strong Relationships
- **PARTICIPATES_IN**: Person participates in conversation
- **SENT_SAMPLE**: Person sent this sample message
- **PART_OF**: Message belongs to conversation
- **SHARED**: Person shared this media file

### Dashed Lines (-.->) - Inferred Relationships
- **KNOWS**: People know each other (bidirectional)
  - Properties: relationship_type, interaction_strength, evidence
- **MENTIONS**: One person mentions another (directional)
  - Properties: mention_count, last_mentioned

## Node Color Coding

- 🔵 **Blue** (Persons): Human participants
- 🟡 **Yellow** (Conversation): Thread container with statistics
- ⚪ **Gray** (Messages): Sample messages (boundary cases)
- 🟣 **Pink** (Media): Photos, videos, gifs, files

## Example Query Paths

### Path 1: Get All Messages from Person
```
Person → SENT_SAMPLE → Message
```

### Path 2: Find Related People
```
Person → KNOWS → Person
```

### Path 3: Get Conversation Details
```
Person → PARTICIPATES_IN → Conversation
```

### Path 4: Find Shared Media
```
Person → SHARED → Media
```

### Path 5: Complete Profile
```
Person → SENT_SAMPLE → Message → PART_OF → Conversation
Person → KNOWS → Person
Person → SHARED → Media
```

## Storage Comparison

### Before (Traditional)
```
┌─────────────────────────┐
│ 61,861 Message Nodes    │
│ Each with full content  │
│ Total: ~2.2 MB          │
└─────────────────────────┘
```

### After (Condensed Ontology)
```
┌─────────────────────────┐
│ 2 Person Nodes          │
│ 1 Conversation Node     │
│ 5-15 Sample Messages    │
│ ~34 Media Nodes         │
│ Total: ~0.002 MB        │
│ Reduction: 99.9%        │
└─────────────────────────┘
```

## Data Flow

```
Facebook JSON Export
        ↓
  Parse & Validate
        ↓
  Analyze Patterns
        ↓
   ┌────┴────┐
   ↓         ↓
Statistics  Samples
   ↓         ↓
Create Nodes & Relationships
        ↓
   Neo4j Database
        ↓
  Query Interface
```

## Key Metrics Preserved

Despite 99.9% storage reduction, we preserve:

✅ **Who**: Participant identities and roles  
✅ **When**: Temporal boundaries (start/end dates)  
✅ **How Much**: Message counts, participation percentages  
✅ **What Type**: Media inventory (photos, videos, etc.)  
✅ **Relationships**: Who knows whom, interaction strength  
✅ **Content Samples**: Boundary cases (first, last, longest, shortest)  
✅ **Recent Activity**: Last week samples for current state  

## Scalability

This pattern scales to:
- ✅ Multiple conversations per person
- ✅ Cross-conversation relationship analysis
- ✅ Network-level metrics (centrality, clustering)
- ✅ Temporal trend analysis
- ✅ Integration with other data sources (municipal ontology, etc.)
