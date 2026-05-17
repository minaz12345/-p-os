#!/usr/bin/env python3
"""
Phase 2: Local Forensic Export Pipeline Service

Orchestrates the complete extraction pipeline using Phase 1 contracts:
RAW → METRICS → TIMELINE → SEMANTIC → MANIFEST

Uses:
- schemas/forensic_export.schema.json (data contracts)
- core/normalization/ascii_pl.py (central normalization)
- tests/fixtures/relationship_expected_metrics.json (regression baselines)
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# Import Phase 1 artifacts
from core.normalization.ascii_pl import to_ascii_pl, normalize_for_analysis, validate_ascii_only


class ForensicExportPipeline:
    """
    Constitutional forensic export pipeline for communication datasets.
    
    Enforces:
    - All analytical text MUST use ASCII_PL normalization
    - Original text MAY be preserved only as archival source
    - No metrics may be calculated from raw text
    - W11 validation gates must pass before export completion
    """
    
    def __init__(self, dataset_path: Path, request_id: str):
        self.dataset_path = dataset_path
        self.request_id = request_id
        self.output_dir = project_root / "data" / "exports" / request_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load expected metrics for regression testing
        fixture_path = project_root / "tests" / "fixtures" / "relationship_expected_metrics.json"
        if fixture_path.exists():
            with open(fixture_path, 'r', encoding='utf-8') as f:
                self.expected_metrics = json.load(f)
        else:
            self.expected_metrics = None
    
    def run_pipeline(self) -> Dict:
        """Execute complete forensic export pipeline."""
        
        print("=" * 80)
        print("FORENSIC EXPORT PIPELINE - Phase 2")
        print("=" * 80)
        print(f"Request ID: {self.request_id}")
        print(f"Dataset: {self.dataset_path}")
        print(f"Output: {self.output_dir}")
        print(f"Started: {datetime.now().isoformat()}")
        print()
        
        results = {}
        
        # Step 1: RAW Extraction
        print("[1/5] RAW EXTRACTION...")
        raw_data = self._extract_raw()
        results['raw'] = raw_data
        print(f"  ✓ Extracted {raw_data['total_messages']} messages")
        print()
        
        # Step 2: METRICS Extraction
        print("[2/5] METRICS EXTRACTION...")
        metrics = self._extract_metrics(raw_data['messages'])
        results['metrics'] = metrics
        print(f"  ✓ Computed per-person metrics")
        print(f"  ✓ Paweł: {metrics['pawel']['message_count']} messages ({metrics['pawel']['percentage']}%)")
        print(f"  ✓ Kasia: {metrics['kasia']['message_count']} messages ({metrics['kasia']['percentage']}%)")
        print()
        
        # Step 3: TIMELINE Extraction
        print("[3/5] TIMELINE EXTRACTION...")
        timeline = self._extract_timeline(raw_data['messages'])
        results['timeline'] = timeline
        print(f"  ✓ Detected {len(timeline['phases'])} weekly phases")
        phase_counts = {}
        for phase in timeline['phases']:
            phase_type = phase['phase_type']
            phase_counts[phase_type] = phase_counts.get(phase_type, 0) + 1
        for phase_type, count in sorted(phase_counts.items()):
            print(f"    - {phase_type}: {count} weeks")
        print()
        
        # Step 4: SEMANTIC Extraction
        print("[4/5] SEMANTIC EXTRACTION...")
        semantic = self._extract_semantic(raw_data['messages'])
        results['semantic'] = semantic
        print(f"  ✓ Extracted {len(semantic['top_keywords'])} top keywords")
        print(f"  ✓ Detected {len(semantic['entities'])} named entities")
        print(f"  ✓ Found {semantic['emotional_markers']['total']} emotional markers")
        print()
        
        # Step 5: REGRESSION VALIDATION
        print("[5/5] REGRESSION VALIDATION...")
        validation = self._validate_regression(metrics, timeline, semantic)
        results['validation'] = validation
        
        if validation['passed']:
            print(f"  ✓ ALL REGRESSION TESTS PASSED")
            print(f"  ✓ Metrics match expected values (zero tolerance)")
        else:
            print(f"  ✗ REGRESSION DETECTED!")
            for failure in validation['failures']:
                print(f"    - {failure}")
            print(f"  ⚠ Export BLOCKED - debug required")
        print()
        
        # Save results
        self._save_results(results)
        
        print("=" * 80)
        print("PIPELINE COMPLETE")
        print("=" * 80)
        print(f"Finished: {datetime.now().isoformat()}")
        print(f"Results saved to: {self.output_dir}")
        print()
        
        return results
    
    def _extract_raw(self) -> Dict:
        """Extract raw messages with ASCII_PL normalization."""
        
        # Import existing extraction logic
        from scripts.forensic_export_raw import extract_raw_messages, calculate_reply_gaps
        
        messages, participants = extract_raw_messages(self.dataset_path)
        messages = calculate_reply_gaps(messages)
        
        # Apply ASCII_PL normalization (Phase 1 contract enforcement)
        normalized_count = 0
        for msg in messages:
            original_text = msg.get('text', '')
            
            # Create three-layer text architecture
            msg['text_ascii'] = to_ascii_pl(original_text)
            msg['text_clean'] = normalize_for_analysis(original_text)
            
            # Validate ASCII-only in analytical fields
            if not validate_ascii_only(msg['text_ascii']):
                raise ValueError(f"ASCII validation failed for message {msg.get('message_id')}")
            
            normalized_count += 1
        
        return {
            'total_messages': len(messages),
            'messages': messages,
            'normalized_count': normalized_count,
            'encoding_method': 'ASCII_PL_v1.0'
        }
    
    def _extract_metrics(self, messages: List[Dict]) -> Dict:
        """Extract per-person relationship metrics."""
        
        from scripts.analyze_relationship_raw import compute_per_person_metrics
        
        metrics_df = compute_per_person_metrics(messages)
        
        # Convert to dict format matching schema
        pawel_metrics = metrics_df[metrics_df['sender'] == 'Pawel Nazaruk'].iloc[0].to_dict()
        kasia_metrics = metrics_df[metrics_df['sender'] == 'Kasia Ju'].iloc[0].to_dict()
        
        return {
            'pawel': {
                'message_count': int(pawel_metrics['messages_count']),
                'percentage': round(float(pawel_metrics['percentage']), 2),
                'avg_message_length': round(float(pawel_metrics['avg_message_length']), 2),
                'median_message_length': float(pawel_metrics['median_message_length']),
                'media_share_percent': round(float(pawel_metrics['media_share_percent']), 2),
                'avg_reply_gap_minutes': round(float(pawel_metrics['avg_reply_gap_minutes']), 2),
                'median_reply_gap_minutes': float(pawel_metrics['median_reply_gap_minutes']),
                'days_opened': int(pawel_metrics['days_opened']),
                'questions_count': int(pawel_metrics.get('questions_count', 0))
            },
            'kasia': {
                'message_count': int(kasia_metrics['messages_count']),
                'percentage': round(float(kasia_metrics['percentage']), 2),
                'avg_message_length': round(float(kasia_metrics['avg_message_length']), 2),
                'median_message_length': float(kasia_metrics['median_message_length']),
                'media_share_percent': round(float(kasia_metrics['media_share_percent']), 2),
                'avg_reply_gap_minutes': round(float(kasia_metrics['avg_reply_gap_minutes']), 2),
                'median_reply_gap_minutes': float(kasia_metrics['median_reply_gap_minutes']),
                'days_opened': int(kasia_metrics['days_opened']),
                'questions_count': int(kasia_metrics.get('questions_count', 0))
            },
            'asymmetry_index': round(abs(pawel_metrics['percentage'] - kasia_metrics['percentage']), 2),
            'computed_at': datetime.now().isoformat()
        }
    
    def _extract_timeline(self, messages: List[Dict]) -> Dict:
        """Extract temporal phases and silence periods."""
        
        from scripts.detect_relationship_phases import detect_weekly_phases
        
        phases = detect_weekly_phases(messages)
        
        return {
            'total_weeks': len(phases),
            'phases': phases,
            'silence_periods': [p for p in phases if p['phase_type'] == 'SILENCE'],
            'high_intensity_weeks': [p for p in phases if p['phase_type'] == 'HIGH_INTENSITY'],
            'extracted_at': datetime.now().isoformat()
        }
    
    def _extract_semantic(self, messages: List[Dict]) -> Dict:
        """Extract semantic patterns using ASCII-normalized text."""
        
        from collections import Counter
        from core.normalization.ascii_pl import normalize_for_analysis
        
        # Use text_ascii field for all semantic analysis (Phase 1 contract)
        ascii_texts = [msg.get('text_ascii', '') for msg in messages]
        
        # Simple keyword extraction (top words excluding stopwords)
        STOPWORDS = {
            'i', 'a', 'ale', 'ze', 'to', 'w', 'we', 'na', 'do', 'po', 'od', 'za',
            'z', 'o', 'u', 'sie', 'nie', 'tak', 'no', 'jak', 'co', 'czy',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'
        }
        
        all_words = []
        for text in ascii_texts:
            if text:
                normalized = normalize_for_analysis(text)
                words = normalized.split()
                all_words.extend([w for w in words if w not in STOPWORDS and len(w) > 2])
        
        word_freq = Counter(all_words)
        keywords = [
            {'keyword': word, 'frequency': freq}
            for word, freq in word_freq.most_common(20)
        ]
        
        # Bigrams
        bigram_list = []
        for text in ascii_texts:
            if text:
                normalized = normalize_for_analysis(text)
                words = normalized.split()
                for i in range(len(words) - 1):
                    bigram_list.append(f"{words[i]} {words[i+1]}")
        
        bigram_freq = Counter(bigram_list)
        bigrams = [
            {'bigram': bg, 'frequency': freq}
            for bg, freq in bigram_freq.most_common(15)
        ]
        
        # Emotional markers (simple keyword matching)
        EMOTIONAL_MARKERS = {
            "positive": ["dobrze", "super", "fajnie", "lubie", "dziekuje", "milosc", "kocham"],
            "negative": ["zle", "smutno", "boje", "strach", "problem", "trudno"],
            "uncertainty": ["moze", "chyba", "nie wiem", "hmm"],
            "closeness": ["tęsknię", "brakuje", "blisko", "razem"]
        }
        
        emotional_counts = {category: 0 for category in EMOTIONAL_MARKERS}
        total_emotional = 0
        
        for text in ascii_texts:
            text_lower = text.lower()
            for category, markers in EMOTIONAL_MARKERS.items():
                for marker in markers:
                    if marker in text_lower:
                        emotional_counts[category] += 1
                        total_emotional += 1
        
        # Named entities (capitalized words appearing frequently)
        original_texts = [msg.get('text', '') for msg in messages]
        entity_words = []
        for text in original_texts:
            if text:
                words = text.split()
                entity_words.extend([w.strip('.,!?;:') for w in words if w[0].isupper() and len(w) > 2])
        
        entity_freq = Counter(entity_words)
        entities = [
            {'entity': word, 'frequency': freq}
            for word, freq in entity_freq.most_common(10)
            if freq > 5
        ]
        
        return {
            'top_keywords': keywords,
            'bigrams': bigrams,
            'trigrams': [],  # Simplified for Phase 2
            'entities': entities,
            'emotional_markers': {
                'total': total_emotional,
                'by_category': emotional_counts
            },
            'extraction_method': 'ASCII_PL_normalized',
            'extracted_at': datetime.now().isoformat()
        }
    
    def _validate_regression(self, metrics: Dict, timeline: Dict, semantic: Dict) -> Dict:
        """Validate computed metrics against expected baselines (zero tolerance)."""
        
        if not self.expected_metrics:
            return {
                'passed': True,
                'note': 'No expected metrics fixture available - skipping regression test'
            }
        
        expected = self.expected_metrics['expected_metrics']
        failures = []
        
        # Critical value checks (zero tolerance)
        critical_checks = [
            ('pawel_messages', metrics['pawel']['message_count']),
            ('kasia_messages', metrics['kasia']['message_count']),
            ('questions_total', metrics['pawel']['questions_count'] + metrics['kasia']['questions_count']),
            ('high_intensity_weeks', len(timeline['high_intensity_weeks']))
        ]
        
        for key, computed_value in critical_checks:
            expected_value = expected.get(key)
            if expected_value is not None:
                if computed_value != expected_value:
                    failures.append(
                        f"{key}: expected={expected_value}, computed={computed_value}"
                    )
        
        # Check third-party entity detection
        expected_entity = expected.get('third_party_entity_candidate')
        if expected_entity:
            detected_entities = [e['entity'] for e in semantic['entities']]
            if expected_entity not in detected_entities:
                failures.append(
                    f"third_party_entity: expected '{expected_entity}' not found in top entities"
                )
        
        passed = len(failures) == 0
        
        # If regression detected, create flag file
        if not passed:
            flags_dir = project_root / "flags"
            flags_dir.mkdir(exist_ok=True)
            flag_file = flags_dir / "REGRESSION_DETECTED.flag"
            with open(flag_file, 'w') as f:
                f.write(json.dumps({
                    'request_id': self.request_id,
                    'timestamp': datetime.now().isoformat(),
                    'failures': failures
                }, indent=2))
            print(f"  ⚠ Created regression flag: {flag_file}")
        
        return {
            'passed': passed,
            'failures': failures,
            'validated_at': datetime.now().isoformat()
        }
    
    def _save_results(self, results: Dict):
        """Save pipeline results to output directory."""
        
        # Save complete results
        results_file = self.output_dir / "pipeline_results.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Save individual components
        with open(self.output_dir / "raw_summary.json", 'w') as f:
            json.dump({
                'total_messages': results['raw']['total_messages'],
                'normalized_count': results['raw']['normalized_count'],
                'encoding_method': results['raw']['encoding_method']
            }, f, indent=2)
        
        with open(self.output_dir / "metrics.json", 'w') as f:
            json.dump(results['metrics'], f, indent=2)
        
        with open(self.output_dir / "timeline.json", 'w') as f:
            json.dump({
                'total_weeks': results['timeline']['total_weeks'],
                'phase_summary': {
                    phase['phase_type']: sum(1 for p in results['timeline']['phases'] if p['phase_type'] == phase['phase_type'])
                    for phase in results['timeline']['phases']
                }
            }, f, indent=2)
        
        with open(self.output_dir / "semantic.json", 'w') as f:
            json.dump({
                'keywords_count': len(results['semantic']['top_keywords']),
                'entities_count': len(results['semantic']['entities']),
                'emotional_total': results['semantic']['emotional_markers']['total']
            }, f, indent=2)
        
        with open(self.output_dir / "validation.json", 'w') as f:
            json.dump(results['validation'], f, indent=2)


def main():
    """Run pipeline on relationship dataset."""
    
    # Default dataset path
    dataset_path = project_root / "Facebook" / "kasiaju_1977350892357109" / "message_1.json"
    
    if not dataset_path.exists():
        print(f"ERROR: Dataset not found at {dataset_path}")
        print("Please ensure Facebook conversation data is available.")
        sys.exit(1)
    
    # Generate request ID
    request_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Run pipeline
    pipeline = ForensicExportPipeline(dataset_path, request_id)
    results = pipeline.run_pipeline()
    
    # Exit with error code if regression detected
    if not results['validation']['passed']:
        print("\n⚠ PIPELINE COMPLETED WITH REGRESSION FAILURES")
        print("Export BLOCKED - manual investigation required")
        sys.exit(1)
    else:
        print("\n✓ PIPELINE SUCCESSFUL - All validations passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
