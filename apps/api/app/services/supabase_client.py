from supabase import create_client, Client
import os
from typing import Optional

class SupabaseService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL", "http://localhost:3100")
        key = os.getenv("SUPABASE_KEY", "your-anon-key")
        self.client: Client = create_client(url, key)

    async def store_media_reference(self, user_id: str, minio_url: str, media_type: str):
        """Store MinIO URL reference in Supabase"""
        data = {
            "user_id": user_id,
            "media_url": minio_url,
            "media_type": media_type,
            "created_at": "now()"
        }
        result = self.client.table("media").insert(data).execute()
        return result

    async def get_user_media(self, user_id: str):
        """Retrieve all media URLs for a user"""
        result = self.client.table("media").select("*").eq("user_id", user_id).execute()
        return result.data
