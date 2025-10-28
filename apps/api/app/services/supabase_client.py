"""
Supabase Client Module
Provides a singleton Supabase client for database and auth operations.
"""
import os
from typing import Optional
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
    def query(cls, table: str, columns: str = "*"):
        """
        Helper function for SELECT queries
        
        Args:
            table: Table name to query
            columns: Columns to select (default: "*")
            
        Returns:
            Query builder object
        """
        try:
            client = cls.get_client()
            return client.table(table).select(columns)
        except Exception as e:
            raise Exception(f"Query failed: {str(e)}")

    @classmethod
    def insert(cls, table: str, data: dict | list):
        """
        Helper function for INSERT operations
        
        Args:
            table: Table name
            data: Data to insert (dict or list of dicts)
            
        Returns:
            Insert operation result
        """
        try:
            client = cls.get_client()
            return client.table(table).insert(data).execute()
        except Exception as e:
            raise Exception(f"Insert failed: {str(e)}")

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
    def delete(cls, table: str):
        """
        Helper function for DELETE operations
        
        Args:
            table: Table name
            
        Returns:
            Query builder for delete (needs .eq() or .match() before .execute())
        """
        try:
            client = cls.get_client()
            return client.table(table).delete()
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