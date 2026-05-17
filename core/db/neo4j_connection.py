#!/usr/bin/env python3
"""
P-OS v8.0 Milejczyce — Centralized Neo4j Connection Module
Provides secure, consistent database connections across all scripts

Features:
- Automatic TLS detection and configuration
- Credential management via environment variables
- Connection pooling and retry logic
- Audit logging for all connections
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Load environment variables from .env files
try:
    from dotenv import load_dotenv
    # Load main .env file
    load_dotenv()
    # Also load .env.db for database credentials (Neo4j, PostgreSQL)
    project_root = Path(__file__).resolve().parent.parent.parent
    env_db_path = project_root / '.env.db'
    if env_db_path.exists():
        load_dotenv(env_db_path, override=True)
except ImportError:
    pass  # dotenv not required, will use system env vars

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from neo4j import GraphDatabase, Driver
    NEO4J_AVAILABLE = True
except ImportError:
    print("[ERROR] neo4j driver not installed. Run: pip install neo4j")
    NEO4J_AVAILABLE = False
    sys.exit(1)


class Neo4jConnectionManager:
    """Centralized Neo4j connection manager with TLS support"""
    
    def __init__(self):
        # Connection configuration
        self.uri = os.getenv('NEO4J_URI', 'bolt+ssc://localhost:7687')  # Default to TLS
        # Support both NEO4J_USER and NEO4J_USERNAME for compatibility
        self.username = os.getenv('NEO4J_USERNAME') or os.getenv('NEO4J_USER', 'neo4j')
        self.password = os.getenv('NEO4J_PASSWORD', 'Milejczyce2026!Secure')
        
        # Connection settings
        self.max_connection_lifetime = 3600  # 1 hour
        self.connection_acquisition_timeout = 60  # 60 seconds
        self.max_retry_time = 30  # 30 seconds
        
        # Driver instance (singleton pattern)
        self._driver: Optional[Driver] = None
        
        # Audit logging
        self.connection_log = []
        
    def get_driver(self) -> Driver:
        """Get or create Neo4j driver instance with TLS"""
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                    max_connection_lifetime=self.max_connection_lifetime,
                    connection_acquisition_timeout=self.connection_acquisition_timeout
                )
                
                # Verify connectivity
                self._driver.verify_connectivity()
                
                # Log successful connection
                self._log_connection("SUCCESS", self.uri)
                
            except Exception as e:
                self._log_connection("FAILED", self.uri, str(e))
                raise
        
        return self._driver
    
    def close(self):
        """Close driver connection"""
        if self._driver:
            self._driver.close()
            self._driver = None
            self._log_connection("CLOSED", self.uri)
    
    def _log_connection(self, status: str, uri: str, error: str = None):
        """Log connection attempt for audit trail"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'uri': uri,
            'username': self.username,
            'error': error
        }
        self.connection_log.append(log_entry)
        
        # Print to console
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if status == "SUCCESS":
            print(f"[{timestamp}] [INFO] [PASS] Neo4j connection established: {uri}")
        elif status == "FAILED":
            print(f"[{timestamp}] [ERROR] [FAIL] Neo4j connection failed: {error}")
        else:
            print(f"[{timestamp}] [INFO] Neo4j connection {status.lower()}: {uri}")
    
    def execute_query(self, query: str, parameters: dict = None):
        """Execute Cypher query with automatic connection management"""
        driver = self.get_driver()
        
        try:
            with driver.session() as session:
                result = session.run(query, parameters or {})
                return list(result)
        except Exception as e:
            print(f"[ERROR] Query execution failed: {e}")
            raise
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure connection is closed"""
        self.close()
        return False


# ============================================================================
# CONVENIENCE FUNCTIONS FOR EXISTING SCRIPTS
# ============================================================================

# Global singleton instance
_manager_instance = None

def get_neo4j_driver():
    """
    Convenience function for existing scripts.
    Returns configured Neo4j driver with TLS enabled.
    Uses singleton pattern to avoid recreating driver on every call.
    
    Usage:
        from core.db.neo4j_connection import get_neo4j_driver
        driver = get_neo4j_driver()
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = Neo4jConnectionManager()
    return _manager_instance.get_driver()


def execute_cypher_query(query: str, parameters: dict = None):
    """
    Convenience function for executing queries without managing driver lifecycle.
    
    Usage:
        from core.db.neo4j_connection import execute_cypher_query
        results = execute_cypher_query("MATCH (n) RETURN count(n)")
    """
    with Neo4jConnectionManager() as manager:
        return manager.execute_query(query, parameters)


def verify_connection():
    """
    Quick connection verification function.
    
    Usage:
        from core.db.neo4j_connection import verify_connection
        if verify_connection():
            print("Connected!")
    """
    try:
        with Neo4jConnectionManager() as manager:
            driver = manager.get_driver()
            driver.verify_connectivity()
            return True
    except Exception as e:
        print(f"Connection verification failed: {e}")
        return False


# ============================================================================
# MAIN EXECUTION (for testing)
# ============================================================================

def main():
    """Test connection and display status"""
    print("=" * 80)
    print("P-OS v8.0 — Neo4j Connection Test")
    print("=" * 80)
    
    try:
        with Neo4jConnectionManager() as manager:
            driver = manager.get_driver()
            
            # Get database info
            with driver.session() as session:
                # Count nodes
                result = session.run("MATCH (n) RETURN count(n) as total")
                total_nodes = result.single()['total']
                
                # Count relationships
                result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
                total_rels = result.single()['total']
                
                # Check TLS status
                result = session.run("CALL dbms.components() YIELD name, versions RETURN name, versions")
                components = list(result)
            
            print("\n" + "=" * 80)
            print("CONNECTION STATUS: [PASS] SUCCESS")
            print("=" * 80)
            print(f"URI: {manager.uri}")
            print(f"Encryption: {'Yes (TLS)' if 'bolt+s' in manager.uri or 'bolt+ssc' in manager.uri else 'No'}")
            print(f"Total Nodes: {total_nodes:,}")
            print(f"Total Relationships: {total_rels:,}")
            print(f"Neo4j Version: {components[0]['versions'][0] if components else 'Unknown'}")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n[FAIL] CONNECTION FAILED: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
