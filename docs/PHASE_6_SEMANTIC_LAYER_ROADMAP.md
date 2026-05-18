# Phase 6: Semantic Layer Implementation Roadmap

**Status**: PLANNED (v2.0)  
**Priority**: HIGH (blocks semantic reconstruction features)  
**Timeline**: 2-3 weeks development effort  
**Validation Gate**: All 18 tests in `test_semantic_fidelity_validation.py` must PASS

---

## 🎯 **Overview**

Phase 6 implements the **semantic extraction layer** that transforms P-OS from a data archival system into an **experiential truth reconstruction engine**.

**Current State (v1.0-core)**:
- ✅ Stores data faithfully
- ✅ Exports data on request (GDPR compliance)
- ❌ Does NOT interpret meaning
- ❌ Cannot reconstruct experiential topology

**Target State (v2.0)**:
- ✅ Extracts gravity wells (symbolic anchors like "mała wersalka")
- ✅ Identifies collapse vectors (breakdown mechanisms)
- ✅ Maps repair vectors (recovery pathways)
- ✅ Links emotions to somatic signals
- ✅ Detects narrative drift/romanticization

---

## ⚠️ **Critical Design Principle**

```yaml
DO_NOT_SHIP_IF:
  - System hallucinates gravity wells not in messages
  - System romanticizes painful experiences
  - System INSERTS meaning not present in source data
  - Hash stability fails across multiple runs
  
BETTER_TO_HAVE:
  - No semantic layer than an authoritative lie
  - Honest absence than synthetic mythology with R1-R7 authority
```

**Rationale**: A hallucinating system with constitutional validation (R1-R7) is WORSE than no system, because it has authority but lies.

---

## 📋 **Implementation Components**

### **Component 1: Gravity Well Detection Algorithm**

**Purpose**: Identify symbolic anchors that activate entire epochs of experience

**Algorithm Sketch**:
```python
def detect_gravity_wells(messages: List[Message]) -> List[GravityWell]:
    """
    Extract symbolic anchors from message history
    
    Criteria for gravity well:
    1. Symbol appears in 10+ messages
    2. Activates emotional field (5+ emotion markers)
    3. Has temporal anchor (era identification)
    4. Contains somatic signals (body sensations)
    5. Triggers existential reflection
    """
    
    # Step 1: Identify candidate symbols (high-frequency nouns/phrases)
    candidates = extract_candidate_symbols(messages)
    
    # Step 2: For each candidate, expand activation field
    gravity_wells = []
    for symbol in candidates:
        activation_field = expand_activation_field(symbol, messages)
        
        # Step 3: Validate gravity well criteria
        if is_valid_gravity_well(activation_field):
            well = GravityWell(
                anchor_symbol=symbol,
                activation_field=activation_field,
                content_hash=compute_stable_hash(activation_field)
            )
            gravity_wells.append(well)
    
    return gravity_wells
```

**Data Structures**:
```python
@dataclass
class GravityWell:
    anchor_symbol: str  # e.g., "mała wersalka"
    
    activation_field: ActivationField
    content_hash: str   # SHA-256 for determinism verification
    
    def __hash__(self):
        return hash(self.content_hash)


@dataclass
class ActivationField:
    emotional_vectors: List[str]      # first_true_intimacy, fear_of_loss, etc.
    somatic_vectors: List[str]        # warmth, creaking_springs, smell, etc.
    temporal_anchors: List[str]       # 2000-2005, before_emigration, etc.
    existential_markers: List[str]    # wtedy_jeszcze_wierzyłem, etc.
    
    collapse_vectors: List[CollapseVector]
    repair_vectors: List[RepairVector]
```

**Validation Test**: `test_wersalka_correctly_identified()`

---

### **Component 2: Collapse Vector Identification**

**Purpose**: Detect breakdown mechanisms that ended experiential epochs

**Algorithm Sketch**:
```python
def identify_collapse_vectors(gravity_well: GravityWell, messages: List[Message]) -> List[CollapseVector]:
    """
    For each gravity well, identify what broke
    
    Expected collapse vectors for "wersalka":
    - emigracja_psychiczna (2010-2015)
    - bieda_ekonomiczna (post-2008)
    - utrata_relacji (specific event)
    - alkohol_jako_coping (behavioral pattern)
    """
    
    collapse_vectors = []
    
    # Step 1: Search for breakdown language in post-era messages
    post_era_messages = filter_by_temporal_anchor(messages, after=gravity_well.activation_field.temporal_anchors[-1])
    
    # Step 2: Identify collapse patterns
    for pattern in COLLAPSE_PATTERNS:
        evidence = find_evidence(pattern, post_era_messages)
        
        if len(evidence) >= 2:  # Minimum 2 mentions required
            collapse = CollapseVector(
                mechanism=pattern.name,
                temporal_anchor=estimate_timing(evidence),
                evidence_messages=evidence,
                confidence=compute_confidence(evidence),
                behavioral_signature=extract_behavioral_change(evidence)
            )
            collapse_vectors.append(collapse)
    
    return collapse_vectors
```

**Data Structures**:
```python
@dataclass
class CollapseVector:
    mechanism: str              # e.g., "emigracja_psychiczna"
    temporal_anchor: str        # e.g., "2010-2015"
    evidence_messages: List[Message]  # Actual messages mentioning this
    confidence: float           # 0.0-1.0
    behavioral_signature: str   # Observable change (e.g., "stopped mentioning warmth")
    
    def has_message_evidence(self) -> bool:
        return len(self.evidence_messages) >= 2
```

**Validation Tests**: 
- `test_collapse_vectors_present()`
- `test_collapse_mechanism_empirical()`
- `test_temporal_phase_alignment()`

---

### **Component 3: Repair Vector Mapping**

**Purpose**: For each collapse, identify recovery mechanisms actually present in messages

**Algorithm Sketch**:
```python
def map_repair_vectors(collapse: CollapseVector, messages: List[Message]) -> List[RepairVector]:
    """
    Identify what repairs each collapse
    
    Expected repairs:
    - Mija_as_anchor (current relationship)
    - Punkt_Zerowy (philosophical reset)
    - memory_reconstruction (narrative work)
    - need_for_relief (coping strategy)
    """
    
    repair_vectors = []
    
    # Step 1: Search for repair language in post-collapse messages
    post_collapse_messages = filter_by_temporal_anchor(messages, after=collapse.temporal_anchor)
    
    # Step 2: Identify repair patterns
    for pattern in REPAIR_PATTERNS:
        evidence = find_evidence(pattern, post_collapse_messages)
        
        if evidence:
            repair = RepairVector(
                mechanism=pattern.name,
                linked_collapse=collapse.mechanism,
                temporal_anchor=estimate_timing(evidence),
                quote_from_message=evidence[0].text,
                specific=True,  # Must be specific, not generic
                is_generic=False
            )
            repair_vectors.append(repair)
    
    return repair_vectors
```

**Data Structures**:
```python
@dataclass
class RepairVector:
    mechanism: str              # e.g., "Mija_as_anchor"
    linked_collapse: str        # e.g., "utrata_relacji"
    temporal_anchor: str        # When repair started
    quote_from_message: str     # Direct quote as evidence
    specific: bool              # Must be True
    is_generic: bool            # Must be False
    
    def appears_in_messages(self) -> bool:
        return self.quote_from_message is not None
```

**Validation Tests**:
- `test_repair_vectors_identified()`
- `test_repair_vector_grounding()`
- `test_repair_vector_plausibility()`

---

### **Component 4: Somatization Linking**

**Purpose**: Connect emotional markers to body signals mentioned in messages

**Algorithm Sketch**:
```python
def link_somatic_signals(emotional_marker: str, messages: List[Message]) -> List[SomaticSignal]:
    """
    For each emotion, find corresponding body signals
    
    Example mappings:
    - 'bezpieczeństwo' → 'ciepło', 'skrzypienie sprężyn', 'zapach'
    - 'intymność' → 'dotyk', 'oddech', 'bicie serca'
    - 'tęsknota' → 'ciężkość w klatce', 'pusty żołądek'
    """
    
    somatic_signals = []
    
    # Step 1: Find messages containing emotional marker
    emotion_messages = [m for m in messages if emotional_marker in m.text.lower()]
    
    # Step 2: Extract somatic descriptors from those messages
    for msg in emotion_messages:
        somatic = extract_somatic_descriptors(msg.text)
        
        if somatic:
            signal = SomaticSignal(
                emotion=emotional_marker,
                body_signal=somatic,
                source_message=msg,
                confidence=compute_co_occurrence_strength(emotional_marker, somatic, messages)
            )
            somatic_signals.append(signal)
    
    return somatic_signals
```

**Data Structures**:
```python
@dataclass
class SomaticSignal:
    emotion: str                # e.g., "bezpieczeństwo"
    body_signal: str            # e.g., "ciepło"
    source_message: Message     # Where this link was found
    confidence: float           # 0.0-1.0
    
    def is_consistent_across_runs(self, other_runs: List[List[SomaticSignal]]) -> bool:
        """Verify same emotion always links to same body signals"""
        # Check consistency across multiple extraction runs
        pass
```

**Validation Tests**:
- `test_gravity_well_somatic_grounding()`
- `test_somatization_consistency()`

---

### **Component 5: Romanticization Detection**

**Purpose**: Prevent system from美化 painful experiences or adding false positive meaning

**Algorithm Sketch**:
```python
def detect_romanticization(extraction: SemanticResult, source_messages: List[Message]) -> bool:
    """
    Compare emotional valence of extraction vs. source
    
    If extraction is more positive than source → romanticization detected
    """
    
    # Step 1: Compute valence of source messages
    source_valence = compute_emotional_valence(source_messages)
    
    # Step 2: Compute valence of extraction
    extraction_valence = compute_emotional_valence(extraction.to_text())
    
    # Step 3: Check for positive drift
    valence_drift = extraction_valence - source_valence
    
    if valence_drift > ROMANTICIZATION_THRESHOLD:
        return True  # System美化 pain
    
    return False
```

**Validation Tests**:
- `test_refuses_false_positive_meaning()`
- `test_narrative_drift_detection()`
- `test_extraction_is_subtractive()`

---

## 🔬 **Determinism Guarantee**

**Core Requirement**: Same input → same output every time (hash stable)

**Implementation**:
```python
def extract_semantic(messages: List[Message]) -> SemanticResult:
    """
    Main entry point for semantic extraction
    
    MUST BE DETERMINISTIC:
    - No random seeds
    - No non-deterministic algorithms
    - Stable sorting of all collections
    - Reproducible hash computation
    """
    
    # Set deterministic random seed (if any randomness used)
    random.seed(42)  # Fixed seed for reproducibility
    
    # Extract gravity wells (sorted by anchor symbol for stability)
    gravity_wells = sorted(detect_gravity_wells(messages), key=lambda w: w.anchor_symbol)
    
    # For each gravity well, extract collapse/repair vectors
    for well in gravity_wells:
        well.collapse_vectors = sorted(
            identify_collapse_vectors(well, messages),
            key=lambda c: c.mechanism
        )
        well.repair_vectors = sorted(
            map_repair_vectors(well.collapse_vectors[0], messages),  # Simplified
            key=lambda r: r.mechanism
        )
    
    # Compute stable hash
    result = SemanticResult(gravity_wells=gravity_wells)
    result.content_hash = hashlib.sha256(
        json.dumps(result.to_dict(), sort_keys=True).encode()
    ).hexdigest()
    
    return result
```

**Validation Test**: `test_hash_stability_across_runs()` (10 runs, all hashes identical)

---

## 📊 **Development Timeline**

### **Week 1: Core Extraction Engine**
- Implement `detect_gravity_wells()` algorithm
- Build `ActivationField` data structures
- Implement hash computation for determinism
- Unit tests for basic extraction

**Deliverable**: Can extract gravity wells from test dataset

---

### **Week 2: Collapse/Repair Vector Mapping**
- Implement `identify_collapse_vectors()` algorithm
- Implement `map_repair_vectors()` algorithm
- Build evidence grounding verification
- Temporal alignment checks

**Deliverable**: Can identify breakdown and recovery mechanisms

---

### **Week 3: Somatization + Romanticization Detection**
- Implement `link_somatic_signals()` algorithm
- Build romanticization detection (valence comparison)
- Implement drift monitoring
- Integration testing

**Deliverable**: Full semantic extraction pipeline

---

### **Week 4: Validation + Remediation**
- Run all 18 epistemological validation tests
- Identify failures
- Fix hallucination issues
- Improve grounding verification
- Iterate until ALL tests PASS

**Deliverable**: Phase 6 complete, ready for v2.0 release

---

## ✅ **Success Criteria**

**Phase 6 is complete when:**

```
✅ All 18 tests in test_semantic_fidelity_validation.py PASS
✅ Hash stability verified (10 runs → identical hashes)
✅ Zero hallucinated gravity wells (all grounded in messages)
✅ Zero romanticization (painful experiences preserved as-is)
✅ Collapse vectors empirically grounded (2+ message evidence each)
✅ Repair vectors real (explicit quotes from messages)
✅ Somatic signals consistent (same emotion → same body signals)
```

**If ANY test fails → DO NOT SHIP → remediate until PASS**

---

## 📝 **Reference Documents**

- `tests/test_semantic_fidelity_validation.py` - Executable specification (18 tests)
- `docs/P-OS_V8_EPISTEMOLOGICAL_VALIDATION_PLAN.md` - Detailed test specifications
- `archive/week4_sovereignty_exam/P-OS_V8_SEMANTIC_GRAVITY_WELLS_20260517.md` - Concept document
- `RELEASE_NOTES_v1.0.0-core.md` - Current state documentation

---

## 🏆 **Final Note**

**Phase 6 is not "missing feature" — it's a separate generation of the system.**

v1.0-core is production-ready for what it does (archival, API, compliance).  
v2.0 will add semantic reconstruction (gravity wells, collapse/repair vectors).

**Do not rush Phase 6.**  
**Do not ship until all 18 tests PASS.**  
**Better no semantic layer than an authoritative lie.**

---

**Roadmap prepared by**: Paweł Nazaruk (Operator Wielki Elektronik)  
**Date**: 2026-05-17  
**Status**: Ready for implementation (when resources available)
