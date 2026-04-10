"""
Presto Connection Module for watsonx.data

This module provides a reusable connection wrapper for connecting to watsonx.data
via the Presto SQL query engine. It handles authentication, SSL configuration, and
query execution.

Key Features:
    - Automatic configuration from .env file
    - Support for password authentication
    - SSL/TLS connection support
    - Connection validation
    - Reusable query execution

Usage:
    from presto_connection import PrestoConnection
    
    presto = PrestoConnection()
    presto.connect()
    columns, results = presto.execute_query("SELECT * FROM my_table LIMIT 10")
    presto.close()

Environment Variables Required:
    PRESTO_HOST: Hostname of watsonx.data instance
    PRESTO_PORT: Port number (default: 8443)
    PRESTO_USER: Username for authentication
    PRESTO_PASSWORD: Password (optional, leave empty if not required)
    PRESTO_CATALOG: Catalog name (default: lab_catalog01)
    PRESTO_SCHEMA: Schema name (default: analytics)
    PRESTO_USE_SSL: Use SSL connection (default: true)

Author: Bob
Created: 2026
"""

import prestodb
from prestodb import transaction
import os
from dotenv import load_dotenv

# Load environment variables from .env file
# This reads the .env file in the same directory and loads all key=value pairs
load_dotenv()


class PrestoConnection:
    """
    Wrapper class for watsonx.data Presto connections.
    
    This class encapsulates all connection logic for Presto, making it easy to
    connect, execute queries, and manage the connection lifecycle.
    
    Attributes:
        host (str): Presto server hostname
        port (int): Presto server port
        user (str): Username for authentication
        password (str): Password for authentication (optional)
        catalog (str): Default catalog to use
        schema (str): Default schema to use
        use_ssl (bool): Whether to use SSL/TLS
        conn: Active connection object (None until connected)
    
    Raises:
        ValueError: If required environment variables are missing
        Exception: If connection fails
    """
    
    def __init__(self):
        """
        Initialize connection parameters from environment variables.
        
        Reads configuration from .env file and validates required parameters.
        Does not establish connection yet - call connect() to connect.
        
        Raises:
            ValueError: If PRESTO_HOST or PRESTO_USER are not set
        """
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
        Establish connection to Presto server.
        
        Creates a connection using the parameters loaded from environment variables.
        Supports both password and non-password authentication. Uses SSL by default
        for secure connections.
        
        Connection Parameters:
            - host: Server hostname
            - port: Server port (typically 8443 for SSL)
            - user: Username
            - catalog: Default catalog (e.g., 'lab_catalog01')
            - schema: Default schema (e.g., 'analytics')
            - http_scheme: 'https' if SSL enabled, 'http' otherwise
            - auth: BasicAuthentication if password provided
        
        Returns:
            Connection: Active Presto connection object
            
        Raises:
            Exception: If connection fails (network, authentication, etc.)
            
        Example:
            >>> presto = PrestoConnection()
            >>> conn = presto.connect()
            ✓ Connected to Presto at hostname:8443
              Catalog: lab_catalog01
              Schema: analytics
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
        Execute a SQL query and return results.
        
        Executes the provided SQL query against the connected Presto server.
        Automatically connects if not already connected. Returns both column
        names and result data for easy processing.
        
        Args:
            query (str): SQL query to execute (e.g., "SELECT * FROM table")
            
        Returns:
            tuple: A tuple containing:
                - columns (list): List of column names from the result set
                - results (list): List of tuples, each tuple is a row of data
                
        Example:
            >>> columns, results = presto.execute_query("SELECT name, age FROM users")
            >>> print(columns)
            ['name', 'age']
            >>> print(results)
            [('Alice', 30), ('Bob', 25)]
            
        Note:
            - Fetches all results into memory (use LIMIT for large datasets)
            - Column names preserve case from the query
            - Results are tuples (immutable) for each row
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
        """
        Close the Presto connection.
        
        Properly closes the connection to free resources. Always call this
        when done with queries to avoid connection leaks.
        
        Example:
            >>> presto = PrestoConnection()
            >>> presto.connect()
            >>> # ... execute queries ...
            >>> presto.close()
            ✓ Connection closed
        """
        if self.conn:
            self.conn.close()
            print("✓ Connection closed")


# Test the connection when run directly
# This allows testing the connection by running: python presto_connection.py
if __name__ == "__main__":
    """
    Test script to verify Presto connection.
    
    Run this script directly to test your connection configuration:
        python presto_connection.py
    
    This will:
        1. Load configuration from .env file
        2. Attempt to connect to Presto
        3. Execute a simple test query (SELECT CURRENT_TIMESTAMP)
        4. Display the result
        5. Close the connection
    
    If successful, you'll see:
        ✓ Connected to Presto at hostname:8443
        ✓ Connection test successful!
    
    If it fails, check:
        - .env file exists and has correct values
        - Network connectivity to watsonx.data host
        - Credentials are valid
        - Port 8443 is accessible
    """
    print("Testing Presto Connection...")
    print("=" * 60)
    
    try:
        # Create connection instance
        presto = PrestoConnection()
        
        # Establish connection
        presto.connect()
        
        # Test query - get current timestamp from server
        print("\nExecuting test query...")
        columns, results = presto.execute_query("SELECT CURRENT_TIMESTAMP")
        print(f"Current Timestamp: {results[0][0]}")
        
        # Clean up
        presto.close()
        print("\n✓ Connection test successful!")
        
    except Exception as e:
        print(f"\n✗ Connection test failed: {str(e)}")
        print("\nPlease check:")
        print("  1. .env file exists and is configured correctly")
        print("  2. watsonx.data host is accessible")
        print("  3. Credentials are valid")
        print("  4. Port 8443 is open and accessible")

