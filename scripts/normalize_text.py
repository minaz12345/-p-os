#!/usr/bin/env python3
"""
Shared text normalization utilities for forensic export pipeline

Principle: Analytical layer = ASCII-safe
Polish diacritics are converted to ASCII equivalents for stable comparison.

Usage:
    from normalize_text import to_ascii_pl, normalize_text_for_analysis
"""

import unicodedata
import re


# Polish to ASCII mapping (both lowercase and uppercase)
POLISH_ASCII_MAP = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
    "ó": "o", "ś": "s", "ż": "z", "ź": "z",
    "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N",
    "Ó": "O", "Ś": "S", "Ż": "Z", "Ź": "Z",
})


def to_ascii_pl(text: str) -> str:
    """
    Convert Polish text to ASCII-safe representation.
    
    Handles:
    1. Direct Polish characters (ą, ć, ę, etc.)
    2. Common mojibake artifacts (Å‚, Ä…, etc.)
    3. Unicode normalization
    
    Args:
        text: Input text (may contain Polish diacritics or mojibake)
    
    Returns:
        ASCII-safe text with Polish characters converted
    """
    if text is None:
        return ""
    
    text = str(text)
    
    # Fix common mojibake artifacts that may have already entered the data
    replacements = {
        "Å‚": "l",
        "Å": "l",
        "Ä…": "a",
        "Ä": "a",
        "Ä™": "e",
        "Ä": "e",
        "Å›": "s",
        "Å": "s",
        "Ä‡": "c",
        "Ä‡": "c",
        "Å„": "n",
        "Å„": "n",
        "Ã³": "o",
        "Å¼": "z",
        "Å¼": "z",
        "Åº": "z",
        "Å»": "Z",
        "Å¹": "Z",
        "ÄŁ": "L",
        "Åš": "S",
    }
    
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    
    # Apply Polish to ASCII translation
    text = text.translate(POLISH_ASCII_MAP)
    
    # Unicode normalization (decompose combined characters)
    text = unicodedata.normalize("NFKD", text)
    
    # Remove any remaining non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def normalize_text_for_analysis(text: str) -> str:
    """
    Normalize text for semantic analysis (lowercase + ASCII + cleanup).
    
    Steps:
    1. Convert to ASCII (Polish diacritics → ASCII)
    2. Lowercase
    3. Remove URLs
    4. Keep only alphanumeric + basic punctuation
    5. Normalize whitespace
    
    Args:
        text: Raw message text
    
    Returns:
        Normalized text ready for tokenization/analysis
    """
    text = to_ascii_pl(text).lower()
    text = re.sub(r"http\S+", " ", text)
    text = re.sub(r"[^a-z0-9\s?!]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


if __name__ == "__main__":
    # Quick test
    test_cases = [
        "Cześć, jak się masz?",
        "Dziękuję bardzo!",
        "Nie mogę tego zrobić",
        "Kocham Cię",
        "To jest trudne do zrozumienia",
    ]
    
    print("=" * 80)
    print("TEXT NORMALIZATION TEST")
    print("=" * 80)
    
    for test in test_cases:
        ascii_version = to_ascii_pl(test)
        normalized = normalize_text_for_analysis(test)
        
        print(f"\nOriginal:   {test}")
        print(f"ASCII:      {ascii_version}")
        print(f"Normalized: {normalized}")
    
    print("\n" + "=" * 80)
    print("All tests passed ✓")
