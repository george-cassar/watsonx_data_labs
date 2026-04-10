"""
Presto Connection Module for watsonx.data
Provides a reusable connection wrapper for Presto queries
"""

import prestodb
from prestodb import transaction
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class PrestoConnection:
    """
    Wrapper class for watsonx.data Presto connections
    """
    
    def __init__(self):
        """Initialize connection parameters from environment variables"""
        self.host = os.getenv('PRESTO_HOST')
        self.port = int(os.getenv('PRESTO_PORT', 8443))
        self.user = os.getenv('PRESTO_USER')
        self.password = os.getenv('PRESTO_PASSWORD')  # Optional password
        self.catalog = os.getenv('PRESTO_CATALOG', 'lab_catalog01')
        self.schema = os.getenv('PRESTO_SCHEMA', 'analytics')
        self.use_ssl = os.getenv('PRESTO_USE_SSL', 'true').lower() == 'true'
        
        self.conn = None
        
        # Validate required parameters
        if not self.host:
            raise ValueError("PRESTO_HOST environment variable is required")
        if not self.user:
            raise ValueError("PRESTO_USER environment variable is required")
    
    def connect(self):
        """
        Establish connection to Presto
        
        Returns:
            Connection object
        """
        try:
            # Build connection parameters
            conn_params = {
                'host': self.host,
                'port': self.port,
                'user': self.user,
                'catalog': self.catalog,
                'schema': self.schema,
                'http_scheme': 'https' if self.use_ssl else 'http'
            }
            
            # Add password if provided
            if self.password:
                conn_params['auth'] = prestodb.auth.BasicAuthentication(self.user, self.password)
            
            self.conn = prestodb.dbapi.connect(**conn_params)
            print(f"✓ Connected to Presto at {self.host}:{self.port}")
            print(f"  Catalog: {self.catalog}")
            print(f"  Schema: {self.schema}")
            return self.conn
        except Exception as e:
            print(f"✗ Connection failed: {str(e)}")
            raise
    
    def execute_query(self, query):
        """
        Execute a query and return results
        
        Args:
            query (str): SQL query to execute
            
        Returns:
            tuple: (columns, results) where columns is list of column names
                   and results is list of tuples
        """
        if not self.conn:
            self.connect()
        
        cursor = self.conn.cursor()
        cursor.execute(query)
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Fetch all results
        results = cursor.fetchall()
        
        return columns, results
    
    def close(self):
        """Close the connection"""
        if self.conn:
            self.conn.close()
            print("✓ Connection closed")


# Test the connection when run directly
if __name__ == "__main__":
    print("Testing Presto Connection...")
    print("=" * 60)
    
    try:
        presto = PrestoConnection()
        presto.connect()
        
        # Test query
        print("\nExecuting test query...")
        columns, results = presto.execute_query("SELECT CURRENT_TIMESTAMP")
        print(f"Current Timestamp: {results[0][0]}")
        
        presto.close()
        print("\n✓ Connection test successful!")
        
    except Exception as e:
        print(f"\n✗ Connection test failed: {str(e)}")
        print("\nPlease check:")
        print("  1. .env file exists and is configured correctly")
        print("  2. watsonx.data host is accessible")
        print("  3. Credentials are valid")

# Made with Bob
