# apps/ai/app/utils/url_resolver.py

import re
from urllib.parse import urlparse, urlunparse
from app.core.config import settings


def resolve_minio_url(url: str) -> str:
    """
    Convert external MinIO URLs to internal Docker network URLs.

    Examples:
        http://localhost:9000/bucket/file.jpg -> http://minio:9000/bucket/file.jpg
        http://100.92.51.75:9000/bucket/file.jpg -> http://minio:9000/bucket/file.jpg
        http://minio:9000/bucket/file.jpg -> http://minio:9000/bucket/file.jpg (unchanged)

    Args:
        url: Original URL from media.py or posts.py

    Returns:
        Resolved URL using Docker network hostname
    """
    if not url:
        return url

    parsed = urlparse(url)

    # Check if it's a MinIO URL (port 9000 is the indicator)
    if parsed.port == 9000:
        # Replace hostname with 'minio' for Docker network
        resolved = urlunparse((
            parsed.scheme,           # http
            f'minio:{parsed.port}',  # minio:9000
            parsed.path,             # /bucket/file.jpg
            parsed.params,
            parsed.query,            # presigned params
            parsed.fragment
        ))
        return resolved

    # Not a MinIO URL, return as-is
    return url


def is_local_minio_url(url: str) -> bool:
    """Check if URL points to our MinIO instance"""
    parsed = urlparse(url)
    return parsed.port == 9000 and parsed.hostname in ('localhost', 'minio', '100.92.51.75')
