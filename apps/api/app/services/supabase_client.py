"""
Supabase Client Module
Provides a singleton Supabase client for database and auth operations.
"""
import os, sys
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv
from pathlib import PureWindowsPath
from pathlib import Path

# Load environment variables - go up to the apps/api level
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from apps/api/.env
dotenv_path = project_root / ".env" 
load_dotenv(dotenv_path)


class SupabaseClient:
    """Singleton Supabase client wrapper"""
    
    _instance: Optional[Client] = None
    _initialized: bool = False

    @classmethod
    def get_client(cls) -> Client:
        """
        Get or create Supabase client instance (singleton pattern)
        
        Returns:
            Client: Initialized Supabase client
            
        Raises:
            ValueError: If required environment variables are missing
        """
        if cls._instance is None:
            cls._instance = cls._initialize_client()
        return cls._instance

    @classmethod
    def _initialize_client(cls) -> Client:
        """
        Initialize Supabase client with environment variables
        
        Returns:
            Client: Configured Supabase client
        """
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role for backend
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
            )
        
        client = create_client(supabase_url, supabase_key)
        cls._initialized = True
        return client

    @classmethod
    async def health_check(cls) -> dict:
        """
        Check connection health by querying auth.users table
        
        Returns:
            dict: Health status with connection info
        """
        try:
            client = cls.get_client()
            # Try to query users table (just check if we can connect)
            response = client.table("users").select("id").limit(1).execute()
            
            return {
                "status": "healthy",
                "connected": True,
                "message": "Successfully connected to Supabase"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e)
            }

    @classmethod
    def query(cls, table: str, columns: str = "*", **filters):
        """
        Query table with filters and return results

        Args:
            table: Table name to query
            columns: Columns to select (default: "*")
            **filters: Keyword arguments for filtering (e.g., id="123", name="John")

        Returns:
            List of dictionaries containing query results
        """
        try:
            client = cls.get_client()
            query = client.table(table).select(columns)

            # Apply filters
            for key, value in filters.items():
                query = query.eq(key, value)

            # Execute and return results
            response = query.execute()
            return response.data if response.data else []

        except Exception as e:
            raise Exception(f"Query failed: {str(e)}")


    # In supabase_client.py
    @staticmethod
    def insert(table: str, data: dict) -> dict:
        """Insert a single row into table"""
        client = SupabaseClient.get_client()
        response = client.table(table).insert(data).execute()

        # Return the first item from response.data (the inserted record)
        if response.data and len(response.data) > 0:
            return response.data[0]  # ← Return the actual dictionary
        else:
            raise Exception("Insert failed - no data returned")


    @classmethod
    def update(cls, table: str, data: dict):
        """
        Helper function for UPDATE operations
        
        Args:
            table: Table name
            data: Data to update
            
        Returns:
            Query builder for update (needs .eq() or .match() before .execute())
        """
        try:
            client = cls.get_client()
            return client.table(table).update(data)
        except Exception as e:
            raise Exception(f"Update failed: {str(e)}")

    @classmethod
    def delete(cls, table: str, **filters):
        """
        Delete records from table based on filters

        Args:
            table: Table name
            **filters: Keyword arguments for filtering (e.g., id="123")

        Returns:
            True if deletion was successful
        """
        try:
            client = cls.get_client()
            query = client.table(table).delete()

            # Apply filters - IMPORTANT!
            for key, value in filters.items():
                query = query.eq(key, value)

            # Execute the delete
            response = query.execute()
            return True

        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")



# Convenience function to get client directly
def get_supabase_client() -> Client:
    """
    Get the Supabase client instance
    
    Returns:
        Client: Supabase client
    """
    return SupabaseClient.get_client()