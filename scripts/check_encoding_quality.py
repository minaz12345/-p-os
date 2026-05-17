#!/usr/bin/env python3
"""
Encoding quality check for forensic export pipeline

Checks for mojibake artifacts and non-ASCII characters in analytical fields.

Expected result for text_ascii and text_clean:
    OK: no obvious mojibake markers
    non_ascii_chars: 0
"""

from pathlib import Path
import pandas as pd
import re

INPUT = Path("data/forensic_export/raw/messages.jsonl")

BAD_PATTERNS = [
    "Å", "Ä", "Ã", "Â", "â", "€", "œ"
]


def main():
    """Check encoding quality of forensic export"""
    
    print("=" * 80)
    print("ENCODING QUALITY CHECK")
    print("=" * 80)
    
    if not INPUT.exists():
        print(f"\n[ERROR] Input file not found: {INPUT}")
        print("Run forensic_export_raw.py first!")
        return
    
    df = pd.read_json(INPUT, lines=True)
    
    print(f"\nTotal messages: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Check each relevant column
    for col in ["text", "text_ascii", "text_clean"]:
        if col not in df.columns:
            print(f"\n{'='*80}")
            print(f"COLUMN: {col}")
            print(f"{'='*80}")
            print("[MISSING] Column not found in dataset")
            continue
        
        print(f"\n{'='*80}")
        print(f"COLUMN: {col}")
        print(f"{'='*80}")
        
        # Sample first 5000 rows for efficiency
        joined = "\n".join(df[col].fillna("").astype(str).head(5000))
        
        # Check for bad encoding markers
        hits = {}
        for pattern in BAD_PATTERNS:
            count = joined.count(pattern)
            if count:
                hits[pattern] = count
        
        if hits:
            print("⚠️  BAD ENCODING MARKERS FOUND:")
            for marker, count in sorted(hits.items(), key=lambda x: x[1], reverse=True):
                print(f"   '{marker}': {count} occurrences")
        else:
            print("✅ OK: no obvious mojibake markers")
        
        # Count non-ASCII characters
        non_ascii = sum(1 for ch in joined if ord(ch) > 127)
        print(f"non_ascii_chars: {non_ascii}")
        
        if non_ascii == 0 and not hits:
            print("✅ PASS: Clean ASCII encoding")
        elif col in ["text_ascii", "text_clean"]:
            print(f"⚠️  FAIL: {col} should be ASCII-only but has {non_ascii} non-ASCII chars")
        else:
            print(f"ℹ️  INFO: {col} may contain original Polish diacritics (expected)")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    # Final verdict
    ascii_cols_ok = True
    for col in ["text_ascii", "text_clean"]:
        if col in df.columns:
            joined = "\n".join(df[col].fillna("").astype(str).head(5000))
            non_ascii = sum(1 for ch in joined if ord(ch) > 127)
            has_bad = any(joined.count(p) > 0 for p in BAD_PATTERNS)
            
            if non_ascii > 0 or has_bad:
                ascii_cols_ok = False
                print(f"❌ {col}: FAILED ({non_ascii} non-ASCII, {sum(joined.count(p) for p in BAD_PATTERNS)} mojibake)")
            else:
                print(f"✅ {col}: PASSED")
    
    if ascii_cols_ok:
        print("\n🎉 All analytical fields are clean ASCII! Ready for packaging.")
    else:
        print("\n⚠️  Encoding issues detected. Re-run forensic_export_raw.py before packaging.")


if __name__ == "__main__":
    main()
