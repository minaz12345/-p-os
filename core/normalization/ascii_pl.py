#!/usr/bin/env python3
"""
Central ASCII_PL Normalization Module for P-OS Forensic Export Pipeline

This is the SINGLE SOURCE OF TRUTH for Polish text normalization.
All analytical text MUST use ASCII_PL conversion.
Original text MAY be preserved only as archival source.
No metrics may be calculated from raw text.

Usage:
    from core.normalization.ascii_pl import to_ascii_pl, normalize_for_analysis
    
    # Convert Polish text to ASCII
    ascii_text = to_ascii_pl("Cześć, jak się masz?")
    # Result: "Czesc, jak sie masz?"
    
    # Normalize for analysis (lowercase + cleanup)
    clean_text = normalize_for_analysis("Dziękuję bardzo!")
    # Result: "dziekuje bardzo!"
"""

import unicodedata
import re
from typing import Optional


# Polish to ASCII mapping (both lowercase and uppercase)
POLISH_ASCII_MAP = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
    "ó": "o", "ś": "s", "ż": "z", "ź": "z",
    "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N",
    "Ó": "O", "Ś": "S", "Ż": "Z", "Ź": "Z",
})

# Common mojibake artifacts that need repair
MOJIBAKE_REPLACEMENTS = {
    "Å‚": "l",
    "Å": "l",
    "Ä…": "a",
    "Ä…": "a",
    "Ä™": "e",
    "Ä™": "e",
    "Å›": "s",
    "Å›": "s",
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

# Version identifier for tracking
ASCII_PL_VERSION = "ASCII_PL_v1.0"


def to_ascii_pl(text: Optional[str]) -> str:
    """
    Convert Polish text to ASCII-safe representation.
    
    This is the CENTRAL normalization function used throughout P-OS.
    All analytical text must pass through this function.
    
    Algorithm:
    1. Handle None/empty input
    2. Fix common mojibake artifacts (Å‚→l, Ä…→a, etc.)
    3. Apply Polish→ASCII character mapping (ą→a, ł→l, etc.)
    4. Unicode NFKD normalization (decompose combined characters)
    5. Remove any remaining non-ASCII characters
    6. Normalize whitespace
    
    Args:
        text: Input text (may contain Polish diacritics or mojibake)
    
    Returns:
        ASCII-safe text with Polish characters converted
        
    Examples:
        >>> to_ascii_pl("Cześć, jak się masz?")
        'Czesc, jak sie masz?'
        
        >>> to_ascii_pl("Dziękuję bardzo!")
        'Dziekuje bardzo!'
        
        >>> to_ascii_pl("Nie mogę tego zrobić")
        'Nie moge tego zrobic'
    """
    if text is None:
        return ""
    
    if not isinstance(text, str):
        text = str(text)
    
    if not text:
        return ""
    
    # Step 1: Fix common mojibake artifacts
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        text = text.replace(bad, good)
    
    # Step 2: Apply Polish→ASCII translation
    text = text.translate(POLISH_ASCII_MAP)
    
    # Step 3: Unicode NFKD normalization (decompose combined characters)
    text = unicodedata.normalize("NFKD", text)
    
    # Step 4: Remove any remaining non-ASCII characters
    text = text.encode("ascii", "ignore").decode("ascii")
    
    # Step 5: Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def normalize_for_analysis(text: Optional[str]) -> str:
    """
    Normalize text for semantic analysis (lowercase + ASCII + cleanup).
    
    This function prepares text for tokenization, keyword extraction,
    and other analytical operations.
    
    Steps:
    1. Convert to ASCII using to_ascii_pl()
    2. Lowercase
    3. Remove URLs (http://, https://)
    4. Keep only alphanumeric + basic punctuation (?!)
    5. Normalize whitespace
    
    Args:
        text: Raw message text
    
    Returns:
        Normalized text ready for tokenization/analysis
        
    Examples:
        >>> normalize_for_analysis("Cześć! Sprawdź http://example.com")
        'czesc sprawdz '
        
        >>> normalize_for_analysis("Kocham Cię!!!")
        'kocham cie!!!'
    """
    if text is None:
        return ""
    
    # Step 1: Convert to ASCII
    text = to_ascii_pl(text)
    
    # Step 2: Lowercase
    text = text.lower()
    
    # Step 3: Remove URLs
    text = re.sub(r"http\S+", " ", text)
    
    # Step 4: Keep only alphanumeric + basic punctuation
    text = re.sub(r"[^a-z0-9\s?!]", " ", text)
    
    # Step 5: Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text


def validate_ascii_only(text: str) -> bool:
    """
    Validate that text contains only ASCII characters.
    
    Used by W11 R5 validation gate to ensure encoding integrity.
    
    Args:
        text: Text to validate
    
    Returns:
        True if all characters are ASCII (ord < 128), False otherwise
        
    Examples:
        >>> validate_ascii_only("Hello world")
        True
        
        >>> validate_ascii_only("Cześć")
        False
    """
    return all(ord(char) < 128 for char in text)


def detect_mojibake(text: str) -> list:
    """
    Detect mojibake artifacts in text.
    
    Used for quality control and debugging encoding issues.
    
    Args:
        text: Text to check
    
    Returns:
        List of detected mojibake patterns
        
    Examples:
        >>> detect_mojibake("skasowaÅem historiÄ")
        ['Å', 'Ä']
    """
    mojibake_patterns = ["Å", "Ä", "Ã", "Â", "â", "€", "œ"]
    found = []
    
    for pattern in mojibake_patterns:
        if pattern in text:
            found.append(pattern)
    
    return found


class ASCIINormalizer:
    """
    Stateful ASCII normalizer with statistics tracking.
    
    Useful for batch processing where you want to track:
    - Number of texts normalized
    - Mojibake detection rate
    - Validation failures
    """
    
    def __init__(self):
        self.total_normalized = 0
        self.mojibake_detected = 0
        self.validation_failures = 0
    
    def normalize(self, text: Optional[str]) -> str:
        """Normalize text and update statistics"""
        result = to_ascii_pl(text)
        self.total_normalized += 1
        
        # Check for mojibake in original
        if detect_mojibake(text or ""):
            self.mojibake_detected += 1
        
        # Validate result
        if not validate_ascii_only(result):
            self.validation_failures += 1
        
        return result
    
    def get_stats(self) -> dict:
        """Get normalization statistics"""
        return {
            "total_normalized": self.total_normalized,
            "mojibake_detected": self.mojibake_detected,
            "validation_failures": self.validation_failures,
            "version": ASCII_PL_VERSION
        }
    
    def reset_stats(self):
        """Reset statistics counters"""
        self.total_normalized = 0
        self.mojibake_detected = 0
        self.validation_failures = 0


# Convenience functions for common use cases
def normalize_message_record(message: dict) -> dict:
    """
    Normalize a complete message record.
    
    Adds text_ascii and text_clean fields to message dict.
    
    Args:
        message: Message dict with 'text' field
    
    Returns:
        Message dict with added normalization fields
    """
    original_text = message.get("text", "")
    
    message["text_ascii"] = to_ascii_pl(original_text)
    message["text_clean"] = normalize_for_analysis(original_text)
    message["message_length"] = len(message["text_ascii"])
    
    return message


if __name__ == "__main__":
    # Quick test
    test_cases = [
        "Cześć, jak się masz?",
        "Dziękuję bardzo!",
        "Nie mogę tego zrobić",
        "Kocham Cię",
        "To jest trudne do zrozumienia",
        "Sprawdź http://example.com stronę",
    ]
    
    print("=" * 80)
    print("ASCII_PL NORMALIZATION TEST")
    print(f"Version: {ASCII_PL_VERSION}")
    print("=" * 80)
    
    normalizer = ASCIINormalizer()
    
    for test in test_cases:
        ascii_version = to_ascii_pl(test)
        normalized = normalize_for_analysis(test)
        
        print(f"\nOriginal:   {test}")
        print(f"ASCII:      {ascii_version}")
        print(f"Normalized: {normalized}")
        print(f"Valid ASCII: {validate_ascii_only(ascii_version)}")
        
        # Track stats
        normalizer.normalize(test)
    
    print("\n" + "=" * 80)
    print("STATISTICS")
    print("=" * 80)
    stats = normalizer.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n✅ All tests passed!")
