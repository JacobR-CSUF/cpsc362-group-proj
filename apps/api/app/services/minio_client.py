from minio import Minio
from minio.error import S3Error
import os

class MinIOService:

    
    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
            secure=False  # Set to True in production with SSL
        )
        self.bucket_name = "social-media-uploads"
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")

    def upload_file(self, file_path: str, object_name: str) -> str:
        """Upload file to MinIO and return URL"""
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path
            )
            return f"http://localhost:9000/{self.bucket_name}/{object_name}"
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}\n")