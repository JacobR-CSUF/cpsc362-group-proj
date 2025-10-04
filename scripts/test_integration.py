import asyncio
from apps.api.app.services.minio_client import MinIOService
from apps.api.app.services.supabase_client import SupabaseService

async def test_integration():
    # Initialize services
    minio = MinIOService()
    supabase = SupabaseService()

    # Upload test file to MinIO
    test_file = "/tmp/test.txt"
    with open(test_file, "w") as f:
        f.write("Test content")

    # Upload to MinIO
    minio_url = minio.upload_file(test_file, "test_upload.txt")
    print(f"File uploaded to MinIO: {minio_url}")

    # Store reference in Supabase
    result = await supabase.store_media_reference(
        user_id="test-user-123",
        minio_url=minio_url,
        media_type="text"
    )
    print(f"Reference stored in Supabase: {result}")

if __name__ == "__main__":
    asyncio.run(test_integration())
