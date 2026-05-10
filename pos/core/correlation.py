"""
P-OS CLI Core - Correlation ID Generation

Generates unique correlation IDs for tracking all CLI operations
throughout their lifecycle for forensic traceability.

Format: pos-YYYYMMDD-HHMMSS-XXXXXX
Example: pos-20260510-143022-a91f3b
"""

import uuid
from datetime import datetime


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID for CLI operation tracking.
    
    Returns:
        str: Correlation ID in format pos-YYYYMMDD-HHMMSS-XXXXXX
        
    Example:
        >>> generate_correlation_id()
        'pos-20260510-143022-a91f3b'
    """
    timestamp = datetime.utcnow()
    date_part = timestamp.strftime("%Y%m%d")
    time_part = timestamp.strftime("%H%M%S")
    unique_part = str(uuid.uuid4())[:6]
    
    return f"pos-{date_part}-{time_part}-{unique_part}"


def parse_correlation_id(correlation_id: str) -> dict:
    """
    Parse a correlation ID to extract metadata.
    
    Args:
        correlation_id: Correlation ID string
        
    Returns:
        dict: Extracted metadata including date, time, and unique identifier
        
    Example:
        >>> parse_correlation_id('pos-20260510-143022-a91f3b')
        {
            'date': '20260510',
            'time': '143022',
            'unique': 'a91f3b',
            'full': 'pos-20260510-143022-a91f3b'
        }
    """
    if not correlation_id.startswith("pos-"):
        raise ValueError(f"Invalid correlation ID format: {correlation_id}")
    
    parts = correlation_id.split("-")
    if len(parts) != 4:
        raise ValueError(f"Invalid correlation ID structure: {correlation_id}")
    
    return {
        "date": parts[1],
        "time": parts[2],
        "unique": parts[3],
        "full": correlation_id,
    }
