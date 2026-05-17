#!/usr/bin/env python3
"""
ETAP 3: MECHANICAL SEMANTIC EXTRACTION
Extract semantic patterns WITHOUT interpretation

Output files:
- keywords_by_phase.csv
- ngrams_by_phase.csv
- repeated_phrases.csv
- question_patterns.csv
- emotional_markers.csv
- named_entities_candidates.csv
- semantic_summary_by_phase.json

This is RAW MATERIAL for external analysis (LLM, Gephi, Obsidian, etc.)
NOT psychological interpretation.
"""

from pathlib import Path
import re
import json
from collections import Counter, defaultdict

import pandas as pd
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from core.normalization.ascii_pl import to_ascii_pl, normalize_for_analysis as normalize_text_for_analysis

RAW_INPUT = project_root / "data" / "forensic_export" / "raw" / "messages.jsonl"
PHASES_INPUT = project_root / "data" / "forensic_export" / "timeline" / "relationship_phases.csv"

OUT_DIR = project_root / "data" / "forensic_export" / "semantic"
OUT_DIR.mkdir(parents=True, exist_ok=True)

STOPWORDS_PL = {
    "i", "a", "ale", "ze", "to", "w", "we", "na", "do", "po", "od", "za",
    "z", "o", "u", "sie", "nie", "tak", "no", "jak", "co", "czy",
    "ja", "ty", "on", "ona", "my", "wy", "oni", "one", "mi", "ci", "go",
    "jej", "mu", "mnie", "ciebie", "jest", "sa", "byl", "byla",
    "bylo", "byc", "mam", "masz", "ma", "mamy", "maja", "ten", "ta",
    "te", "tam", "tu", "juz", "sobie", "tez", "dla", "bo", "jakie",
    "ktory", "ktora", "ktore", "oraz", "albo", "lub", "wiec"
}

EMOTIONAL_MARKERS = {
    "positive": [
        "dobrze", "super", "fajnie", "lubie", "dziekuje",
        "ciesze", "milo", "kocham", "ladnie"
    ],
    "negative": [
        "zle", "smutno", "boje", "strach", "problem",
        "trudno", "ciezko", "placz", "wkurza", "kurwa"
    ],
    "uncertainty": [
        "moze", "chyba", "nie wiem", "raczej", "pewnie",
        "zobaczymy", "wydaje", "mysle"
    ],
    "closeness": [
        "tesknie", "brakuje", "blisko", "razem", "przytul",
        "buziak", "serce", "pamietam"
    ],
    "conflict": [
        "czemu", "dlaczego", "przestan", "zostaw",
        "nie chce", "klotnia", "pretensje"
    ]
}


def normalize_text(text: str) -> str:
    """Normalize text for semantic analysis (ASCII + lowercase + cleanup)"""
    return normalize_text_for_analysis(text)


def tokenize(text: str):
    """Tokenize text, removing stopwords and short tokens"""
    text = normalize_text(text)
    tokens = text.split()
    return [
        t for t in tokens
        if len(t) >= 3 and t not in STOPWORDS_PL
    ]


def make_ngrams(tokens, n):
    """Create n-grams from token list"""
    return [
        " ".join(tokens[i:i+n])
        for i in range(len(tokens) - n + 1)
    ]


def assign_week_phase(messages, phases):
    """Assign phase_type to messages based on week"""
    messages["week"] = messages["timestamp"].dt.to_period("W").astype(str)
    return messages.merge(
        phases[["week", "phase_type"]],
        on="week",
        how="left"
    )


def main():
    """Main extraction pipeline"""
    
    print("=" * 80)
    print("ETAP 3: MECHANICAL SEMANTIC EXTRACTION")
    print("Extracting semantic patterns WITHOUT interpretation")
    print("=" * 80)
    
    # Load raw messages
    print(f"\n[LOADING] Raw messages: {RAW_INPUT}")
    messages = pd.read_json(RAW_INPUT, lines=True)
    messages["timestamp"] = pd.to_datetime(messages["timestamp"])
    messages["text"] = messages["text"].fillna("")
    
    # Use text_ascii for analysis (ASCII-safe)
    if "text_ascii" in messages.columns:
        messages["text_ascii"] = messages["text_ascii"].fillna("")
        messages["text_norm"] = messages["text_ascii"].apply(normalize_text)
    else:
        # Fallback: normalize from text field
        messages["text_ascii"] = messages["text"].apply(to_ascii_pl)
        messages["text_norm"] = messages["text_ascii"].apply(normalize_text)
    
    print(f"   Loaded {len(messages)} messages")
    
    # Load phases
    print(f"[LOADING] Phase timeline: {PHASES_INPUT}")
    phases = pd.read_csv(PHASES_INPUT)
    df = assign_week_phase(messages, phases)
    df["phase_type"] = df["phase_type"].fillna("UNCLASSIFIED")
    print(f"   Phases detected: {df['phase_type'].unique()}")
    
    # 1. Keywords by phase and sender
    print("\n[EXTRACTING] 1. Keywords by phase...")
    keyword_rows = []
    
    for (phase, sender), group in df.groupby(["phase_type", "sender"]):
        counter = Counter()
        
        for text in group["text"]:
            counter.update(tokenize(text))
        
        total_tokens = sum(counter.values())
        
        for word, count in counter.most_common(100):
            keyword_rows.append({
                "phase_type": phase,
                "sender": sender,
                "word": word,
                "count": count,
                "share": round(count / total_tokens, 6) if total_tokens else 0
            })
    
    keywords_df = pd.DataFrame(keyword_rows)
    keywords_df.to_csv(
        OUT_DIR / "keywords_by_phase.csv",
        index=False,
        encoding="utf-8"
    )
    print(f"   Saved: {len(keyword_rows)} keyword entries")
    
    # 2. N-grams by phase
    print("[EXTRACTING] 2. N-grams by phase...")
    ngram_rows = []
    
    for (phase, sender), group in df.groupby(["phase_type", "sender"]):
        bigrams = Counter()
        trigrams = Counter()
        
        for text in group["text"]:
            tokens = tokenize(text)
            bigrams.update(make_ngrams(tokens, 2))
            trigrams.update(make_ngrams(tokens, 3))
        
        for phrase, count in bigrams.most_common(100):
            ngram_rows.append({
                "phase_type": phase,
                "sender": sender,
                "ngram_type": "bigram",
                "phrase": phrase,
                "count": count
            })
        
        for phrase, count in trigrams.most_common(100):
            ngram_rows.append({
                "phase_type": phase,
                "sender": sender,
                "ngram_type": "trigram",
                "phrase": phrase,
                "count": count
            })
    
    ngrams_df = pd.DataFrame(ngram_rows)
    ngrams_df.to_csv(
        OUT_DIR / "ngrams_by_phase.csv",
        index=False,
        encoding="utf-8"
    )
    print(f"   Saved: {len(ngram_rows)} n-gram entries")
    
    # 3. Repeated full phrases
    print("[EXTRACTING] 3. Repeated phrases...")
    phrase_counter = Counter()
    
    for text in df["text_norm"]:
        if 5 <= len(text) <= 160:
            phrase_counter[text] += 1
    
    repeated_rows = [
        {"phrase": phrase, "count": count}
        for phrase, count in phrase_counter.most_common()
        if count >= 2
    ]
    
    repeated_df = pd.DataFrame(repeated_rows)
    repeated_df.to_csv(
        OUT_DIR / "repeated_phrases.csv",
        index=False,
        encoding="utf-8"
    )
    print(f"   Saved: {len(repeated_rows)} repeated phrases")
    
    # 4. Question patterns
    print("[EXTRACTING] 4. Question patterns...")
    question_rows = []
    
    questions = df[df["text"].str.contains(r"\?", regex=True, na=False)].copy()
    
    for _, row in questions.iterrows():
        question_rows.append({
            "timestamp": row["timestamp"],
            "sender": row["sender"],
            "phase_type": row["phase_type"],
            "text": row["text"],
            "text_norm": row["text_norm"]
        })
    
    questions_df = pd.DataFrame(question_rows)
    questions_df.to_csv(
        OUT_DIR / "question_patterns.csv",
        index=False,
        encoding="utf-8"
    )
    print(f"   Saved: {len(question_rows)} questions")
    
    # 5. Emotional markers
    print("[EXTRACTING] 5. Emotional markers...")
    emotion_rows = []
    
    for _, row in df.iterrows():
        text_norm = row["text_norm"]
        
        for category, markers in EMOTIONAL_MARKERS.items():
            hits = []
            for marker in markers:
                marker_norm = normalize_text(marker)
                if marker_norm in text_norm:
                    hits.append(marker)
            
            if hits:
                emotion_rows.append({
                    "timestamp": row["timestamp"],
                    "sender": row["sender"],
                    "phase_type": row["phase_type"],
                    "category": category,
                    "markers": "|".join(hits),
                    "text": row["text"]
                })
    
    emotions_df = pd.DataFrame(emotion_rows)
    emotions_df.to_csv(
        OUT_DIR / "emotional_markers.csv",
        index=False,
        encoding="utf-8"
    )
    print(f"   Saved: {len(emotion_rows)} emotional marker hits")
    
    # 6. Named entity candidates: capitalized words from raw text
    print("[EXTRACTING] 6. Named entity candidates...")
    entity_counter = Counter()
    
    for text in df["text"]:
        candidates = re.findall(r"\b[A-ZŁŚŻŹĆŃÓ][a-ząćęłńóśżźA-ZŁŚŻŹĆŃÓ]{2,}\b", str(text))
        entity_counter.update(candidates)
    
    entity_rows = [
        {"entity_candidate": entity, "count": count}
        for entity, count in entity_counter.most_common(200)
    ]
    
    entities_df = pd.DataFrame(entity_rows)
    entities_df.to_csv(
        OUT_DIR / "named_entities_candidates.csv",
        index=False,
        encoding="utf-8"
    )
    print(f"   Saved: {len(entity_rows)} entity candidates")
    
    # 7. Semantic summary by phase
    print("[EXTRACTING] 7. Semantic summary by phase...")
    summary = {}
    
    for phase, group in df.groupby("phase_type"):
        tokens_all = []
        question_count = group["text"].str.contains(r"\?", regex=True, na=False).sum()
        
        for text in group["text"]:
            tokens_all.extend(tokenize(text))
        
        token_counter = Counter(tokens_all)
        
        summary[phase] = {
            "messages": int(len(group)),
            "senders": group["sender"].value_counts().to_dict(),
            "top_keywords": token_counter.most_common(30),
            "question_count": int(question_count),
            "avg_message_length": float(group["text"].str.len().mean())
        }
    
    with open(OUT_DIR / "semantic_summary_by_phase.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    print(f"   Saved: semantic_summary_by_phase.json")
    
    # Final report
    print("\n" + "=" * 80)
    print("ETAP 3 COMPLETE: Semantic extraction finished")
    print("=" * 80)
    print("\nOutput files:")
    for file in sorted(OUT_DIR.iterdir()):
        size_kb = file.stat().st_size / 1024
        print(f"  ✓ {file.name:<40} ({size_kb:.1f} KB)")
    
    print("\nReady for external analysis:")
    print("  - NotebookLM")
    print("  - Local LLM")
    print("  - Gephi")
    print("  - Obsidian")
    print("  - pandas")
    print("  - PDF reports")


if __name__ == "__main__":
    main()
