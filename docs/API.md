
---

## **API.md**

---

# API Documentation

## Overview

This project uses a **self-hosted Supabase backend** with MinIO storage, exposing APIs through Kong API Gateway.

**SUPABASE URL**: `http://localhost:8100`
**KONG GATEWAY**: `http://localhost:8000`

## Authentication

All authenticated requests require a JWT token in the `Authorization` header:

```bash
Authorization: Bearer &lt;your-jwt-token&gt;
```

### Available Keys
| Key Type | Usage | Security |
|----------|----------|----------|
| ANON_KEY | Frontend, client-side requests | Public, respects RLS |
| SERVICE_ROLE_KEY | Backend, server-side operations | Private, bypasses RLS |

**ANON_KEY**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
```

**SERVICE_ROLE_KEY**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
```
---
## Auth API

**Base Path:** /auth/v1

### Sign Up
**Endpoint:** POST /auth/v1/signup

**Request:**
```bash
curl -X POST http://localhost:8000/auth/v1/signup \
  -H &quot;Content-Type: application/json&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot; \
  -d &#x27;{
    &quot;email&quot;: &quot;user@example.com&quot;,
    &quot;password&quot;: &quot;securepassword123&quot;
  }&#x27;
```

**Response (200 OK):**
```Json
{
  &quot;access_token&quot;: &quot;eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&quot;,
  &quot;token_type&quot;: &quot;bearer&quot;,
  &quot;expires_in&quot;: 3600,
  &quot;refresh_token&quot;: &quot;...&quot;,
  &quot;user&quot;: {
    &quot;id&quot;: &quot;123e4567-e89b-12d3-a456-426614174000&quot;,
    &quot;email&quot;: &quot;user@example.com&quot;,
    &quot;created_at&quot;: &quot;2025-10-04T19:00:00Z&quot;
  }
}
```

### Sign in
**Endpoint:** POST /auth/v1/token?grant_type=password

**Request:**
```bash
curl -X POST http://localhost:8000/auth/v1/token?grant_type=password \
  -H &quot;Content-Type: application/json&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot; \
  -d &#x27;{
    &quot;email&quot;: &quot;user@example.com&quot;,
    &quot;password&quot;: &quot;securepassword123&quot;
  }&#x27;
```

**Response (200 OK):**
```Json
{
  &quot;access_token&quot;: &quot;eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...&quot;,
  &quot;token_type&quot;: &quot;bearer&quot;,
  &quot;expires_in&quot;: 3600,
  &quot;refresh_token&quot;: &quot;...&quot;
}
```

### Get User
**Endpoint:** GET /auth/v1/user

**Request:**
```Bash
curl http://localhost:8000/auth/v1/user \
  -H &quot;Authorization: Bearer &lt;ACCESS_TOKEN&gt;&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot;
```

### Sign Out
**Endpoint:** POST /auth/v1/logout

**Request:**
```Bash
curl -X POST http://localhost:8000/auth/v1/logout \
  -H &quot;Authorization: Bearer &lt;ACCESS_TOKEN&gt;&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot;
```
---

## Storage API

**Base Path:** /storage/v1

### List Buckets
**Endpoint:** GET /storage/v1/bucket

**Request:**
```Bash
curl http://localhost:8000/storage/v1/bucket \
  -H &quot;Authorization: Bearer &lt;SERVICE_ROLE_KEY&gt;&quot;
```

### Upload File
**Endpoint:** POST /storage/v1/object/{bucket_name}/{file_path}

**Request:**
```Bash
curl -X POST http://localhost:8000/storage/v1/object/supabase-storage/uploads/image.jpg \
  -H &quot;Authorization: Bearer &lt;SERVICE_ROLE_KEY&gt;&quot; \
  -H &quot;Content-Type: image/jpeg&quot; \
  --data-binary @image.jpg
```

**Response (200 OK):**
```Json
{
  &quot;Key&quot;: &quot;uploads/image.jpg&quot;
}
```

### Download File
**Endpoint:** GET /storage/v1/object/{bucket_name}/{file_path}

**Request:**
```Bash
curl http://localhost:8000/storage/v1/object/supabase-storage/uploads/image.jpg \
  -H &quot;Authorization: Bearer &lt;SERVICE_ROLE_KEY&gt;&quot; \
  --output image.jpg
```

### List Files
**Endpoint:** POST /storage/v1/object/list/{bucket_name}

**Request:**
```Bash
curl -X POST http://localhost:8000/storage/v1/object/list/supabase-storage \
  -H &quot;Authorization: Bearer &lt;SERVICE_ROLE_KEY&gt;&quot; \
  -H &quot;Content-Type: application/json&quot; \
  -d &#x27;{
    &quot;limit&quot;: 100,
    &quot;offset&quot;: 0,
    &quot;sortBy&quot;: { &quot;column&quot;: &quot;name&quot;, &quot;order&quot;: &quot;asc&quot; }
  }&#x27;
```

### Delete File
**Endpoint:** DELETE /storage/v1/object/{bucket_name}/{file_path}

**Request:**
```Bash
curl -X DELETE http://localhost:8000/storage/v1/object/supabase-storage/uploads/image.jpg \
  -H &quot;Authorization: Bearer &lt;SERVICE_ROLE_KEY&gt;&quot;
```
---
## Database API (PostgREST)
**Base Path:** /rest/v1

### Query Table
**Endpoint:** GET /rest/v1/{table_name}

**Request:**
```Bash
curl http://localhost:8000/rest/v1/posts?select=*&amp;limit=10 \
  -H &quot;Authorization: Bearer &lt;ANON_KEY&gt;&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot;
```

### Insert Record
**Endpoint:** POST /rest/v1/{table_name}

**Request:**
```Bash
curl -X POST http://localhost:8000/rest/v1/posts \
  -H &quot;Authorization: Bearer &lt;ACCESS_TOKEN&gt;&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot; \
  -H &quot;Content-Type: application/json&quot; \
  -d &#x27;{
    &quot;user_id&quot;: &quot;123e4567-e89b-12d3-a456-426614174000&quot;,
    &quot;content&quot;: &quot;Hello World!&quot;,
    &quot;media_url&quot;: &quot;https://example.com/image.jpg&quot;
  }&#x27;
```

### Update Record
**Endpoint:** PATCH /rest/v1/{table_name}?id=eq.{record_id}

**Request:**
```Bash
curl -X PATCH &quot;http://localhost:8000/rest/v1/posts?id=eq.abc123&quot; \
  -H &quot;Authorization: Bearer &lt;ACCESS_TOKEN&gt;&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot; \
  -H &quot;Content-Type: application/json&quot; \
  -d &#x27;{
    &quot;content&quot;: &quot;Updated content&quot;
  }&#x27;
```

### Delete Record
**Endpoint:** DELETE /rest/v1/{table_name}?id=eq.{record_id}

**Request:**
```Bash
curl -X DELETE &quot;http://localhost:8000/rest/v1/posts?id=eq.abc123&quot; \
  -H &quot;Authorization: Bearer &lt;ACCESS_TOKEN&gt;&quot; \
  -H &quot;apikey: &lt;ANON_KEY&gt;&quot;
```
---
## Error Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201   | Created |
| 400	| Bad Request - Invalid parameters |
| 401	| Unauthorized - Missing or invalid token |
| 403	| Forbidden - Insufficient permissions |
| 404	| Not Found - Resource doesn't exist |
| 409	| Conflict - Resource already exists |
| 500	| Internal Server Error |
---
## Testing API

### Using Python (Supabase Client)

**To test, must install supabase client locally to import library:** `pip3 install supabase`

```Python
from supabase import create_client

supabase = create_client(
    &quot;http://localhost:8000&quot;,
    &quot;your-anon-key&quot;
)

# Sign up
response = supabase.auth.sign_up({
    &quot;email&quot;: &quot;user@example.com&quot;,
    &quot;password&quot;: &quot;password123&quot;
})

# Upload file
with open(&quot;image.jpg&quot;, &quot;rb&quot;) as f:
    supabase.storage.from_(&quot;supabase-storage&quot;).upload(
        &quot;uploads/image.jpg&quot;,
        f
    )
```