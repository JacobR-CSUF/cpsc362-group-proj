from minio import Minio
from minio.error import S3Error
import os
import json
from io import BytesIO
from typing import Optional

class MinIOService:

    def __init__(self):
        self.client = Minio(
            os.getenv("MINIO_ENDPOINT", "localhost:9000"),
            access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
            secure=False
        )
        self.bucket_name = "social-media-uploads"
        self._ensure_bucket()
        self._set_bucket_policy()

    def _ensure_bucket(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
        except S3Error as e:
            print(f"Error creating bucket: {e}")

    def _set_bucket_policy(self):
        """Set bucket policy for public read access"""
        try:
            # Public read policy
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                    }
                ]
            }
            self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
        except S3Error as e:
            print(f"Warning: Could not set bucket policy: {e}")

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
            raise Exception(f"Failed to upload file: {e}")

    def upload_file_bytes(self, file_data: bytes, object_name: str, content_type: str) -> str:
        """Upload file from bytes to MinIO and return URL"""
        try:
            self.client.put_object(
                self.bucket_name,
                object_name,
                BytesIO(file_data),
                len(file_data),
                content_type=content_type
            )
            return self.generate_public_url(object_name)
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}")

    def delete_file(self, object_name: str):
        """Delete file from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            raise Exception(f"Failed to delete file: {e}")

    def generate_public_url(self, object_name: str) -> str:
        """Generate public URL for object"""
        minio_public_endpoint = os.getenv("MINIO_PUBLIC_ENDPOINT", "http://localhost:9000")
        return f"{minio_public_endpoint}/{self.bucket_name}/{object_name}"

    def file_exists(self, object_name: str) -> bool:
        """Check if file exists in bucket"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False

# Singleton instance
minio_service = MinIOService()

# Export convenience functions
def get_minio_service() -> MinIOService:
    """Get MinIO service singleton"""
    return minio_service
