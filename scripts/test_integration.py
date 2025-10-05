"""
Simple script to continuously upload test files to Supabase Storage
Watch the files appear in MinIO console at http://localhost:9001
"""

import time
from datetime import datetime
from supabase import create_client

# Configuration
SUPABASE_URL = "http://localhost:8000"
SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU"
BUCKET_NAME = "supabase-storage"

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SERVICE_KEY)

print("=" * 60)
print("SUPABASE STORAGE UPLOAD TEST")
print("=" * 60)
print(f"Uploading to bucket: {BUCKET_NAME}")
print("Press Ctrl+C to stop")
print("\nWatch files appear in MinIO console:")
print("http://localhost:9001 (login: minioadmin / minioadmin123)")
print("=" * 60)
print()

counter = 1
while True:
    try:
        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_{counter:03d}_{timestamp}.txt"

        # Create test content
        content = f"""Test File #{counter}
Created: {datetime.now().isoformat()}
This file was uploaded via Supabase Storage API
and is stored in MinIO backend.
"""

        # Upload to Supabase Storage
        print(f"[{counter}] Uploading: {filename}...", end=" ")

        response = supabase.storage.from_(BUCKET_NAME).upload(
            path=f"test-uploads/{filename}",
            file=content.encode('utf-8'),
            file_options={"content-type": "text/plain"}
        )

        print("✓ SUCCESS")

        # Wait before next upload
        time.sleep(3)  # Upload every 3 seconds
        counter += 1

    except KeyboardInterrupt:
        print("\n\nStopped by user.")
        print(f"Total files uploaded: {counter - 1}")
        break
    except Exception as e:
        print(f"✗ FAILED: {e}")
        time.sleep(3)
        counter += 1