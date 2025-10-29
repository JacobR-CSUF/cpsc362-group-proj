# API Quick Reference

## Base URL
```
http://localhost:8989
```

## Authentication
```bash
# Add to all protected endpoints
Authorization: Bearer <jwt-token>
```

---

## Endpoints

### Health & Info

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | No | API info |
| GET | `/health` | No | Health check |
| GET | `/docs` | No | Swagger UI |

### Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/v1/users/me` | Yes | Get own profile (includes email) |
| GET | `/api/v1/users/{id}` | No | Get public profile |
| PUT | `/api/v1/users/me` | Yes | Update own profile |
| DELETE | `/api/v1/users/me` | Yes | Delete own account |

---

## Request Examples

### Get Own Profile
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8989/api/v1/users/me
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "067eb4b2-8bfb-4007-bacd-c6d437901a15",
    "username": "alice_johnson",
    "email": "alice@example.com",
    "profile_pic": "https://i.pravatar.cc/150?img=4",
    "created_at": "2024-10-23T12:34:56"
  }
}
```

### Get Public Profile
```bash
curl http://localhost:8989/api/v1/users/31bb8718-2823-4cbe-b772-915f911bf13b
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "31bb8718-2823-4cbe-b772-915f911bf13b",
    "username": "john_doe",
    "profile_pic": "https://i.pravatar.cc/150?img=1",
    "created_at": "2024-10-23T12:34:56"
  }
}
```

### Update Profile
```bash
curl -X PUT \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"username": "new_username", "profile_pic": "https://example.com/pic.jpg"}' \
     http://localhost:8989/api/v1/users/me
```

**Request Body:**
```json
{
  "username": "new_username",
  "email": "newemail@example.com",
  "profile_pic": "https://example.com/pic.jpg"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "067eb4b2-8bfb-4007-bacd-c6d437901a15",
    "username": "new_username",
    "email": "newemail@example.com",
    "profile_pic": "https://example.com/pic.jpg",
    "created_at": "2024-10-23T12:34:56"
  },
  "message": "Profile updated successfully"
}
```

### Delete Account
```bash
curl -X DELETE \
     -H "Authorization: Bearer <token>" \
     http://localhost:8989/api/v1/users/me
```

**Response:**
```json
{
  "success": true,
  "message": "Account deleted successfully"
}
```

---

## Response Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed |
| 400 | Bad Request | Invalid input |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | User doesn't exist |
| 500 | Server Error | Internal error |

---

## Error Response Format

```json
{
  "success": false,
  "error": "Error type",
  "detail": "Detailed error message"
}
```

**Examples:**
```json
// Expired token
{
  "detail": "Token has expired"
}

// User not found
{
  "detail": "User with ID abc123 not found"
}

// Invalid input
{
  "detail": "Username must be between 3 and 30 characters"
}
```

---

## Authentication Flow

### 1. Generate Token
```bash
python scripts/generate_test_token.py
```

### 2. Use Token
```bash
# Linux/Mac
export TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -H "Authorization: Bearer $TOKEN" http://localhost:8989/api/v1/users/me

# Windows CMD
set TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
curl -H "Authorization: Bearer %TOKEN%" http://localhost:8989/api/v1/users/me

# Windows PowerShell
$TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
curl -H "Authorization: Bearer $TOKEN" http://localhost:8989/api/v1/users/me
```

### 3. Token Structure
```json
{
  "sub": "user-uuid",
  "username": "john_doe",
  "email": "john@example.com",
  "aud": "authenticated",
  "iss": "supabase",
  "iat": 1729687227,
  "exp": 1729773627
}
```

---

## Validation Rules

### Username
- Length: 3-30 characters
- Format: Alphanumeric + underscore

### Email
- Must be valid email format
- Unique in database

### Profile Picture
- Must be valid URL
- Must start with `http://` or `https://`

---

## Testing Workflow

### 1. Start Services
```bash
docker-compose up -d
cd apps/api
uvicorn app.main:app --reload --port 8989
```

### 2. Seed Database
```bash
python scripts/seed_database.py
# Choose option 1, 2, or 3
```

### 3. Generate Tokens
```bash
python scripts/generate_test_token.py
# Choose option 3 to generate for all users
```

### 4. Test Endpoints
```bash
# Health check
curl http://localhost:8989/health

# Public endpoint
curl http://localhost:8989/api/v1/users/<user-id>

# Protected endpoint
export TOKEN="<your-token>"
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8989/api/v1/users/me
```

### 5. Interactive Testing
Open http://localhost:8989/docs for Swagger UI

---

## Common Commands

### Development
```bash
# Start API (dev mode)
uvicorn app.main:app --reload --port 8989

# Start API (production)
uvicorn app.main:app --host 0.0.0.0 --port 8989 --workers 4

# Run with logs
uvicorn app.main:app --reload --port 8989 --log-level debug
```

### Database
```bash
# Seed database
python scripts/seed_database.py

# Test RLS
python scripts/test_rls.py

# Apply RLS (via Supabase UI)
# Copy scripts/enable_rls_hybrid.sql
# Paste in http://localhost:3100 SQL Editor
```

### Testing
```bash
# Generate tokens
python scripts/generate_test_token.py

# Health check
curl http://localhost:8989/health

# API docs
open http://localhost:8989/docs  # Mac
start http://localhost:8989/docs  # Windows
```

---

## Environment Variables

```env
SUPABASE_URL=http://localhost:8000
SUPABASE_SERVICE_ROLE_KEY=<your-service-key>
SUPABASE_ANON_KEY=<your-anon-key>
JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long
API_PORT=8989
DEBUG=True
```

---

## Data Models

### UserPublicProfile
```json
{
  "id": "uuid",
  "username": "string",
  "profile_pic": "string (optional)",
  "created_at": "datetime"
}
```

### UserPrivateProfile
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "profile_pic": "string (optional)",
  "created_at": "datetime"
}
```

### UserUpdateRequest
```json
{
  "username": "string (optional)",
  "email": "string (optional)",
  "profile_pic": "string (optional)"
}
```

---

## Useful Links

- **API Base:** http://localhost:8989
- **Swagger UI:** http://localhost:8989/docs
- **ReDoc:** http://localhost:8989/redoc
- **Supabase:** http://localhost:3100
- **MinIO:** http://localhost:9001

---

## Tips & Tricks

### Quick Test
```bash
# All-in-one test
curl http://localhost:8989/health && \
python scripts/generate_test_token.py && \
curl -H "Authorization: Bearer <token>" http://localhost:8989/api/v1/users/me
```

### Save Token
```bash
# Save to file
python scripts/generate_test_token.py
# Choose option 3
# Save when prompted
# Use from file: export TOKEN=$(cat test_tokens.txt | grep "Token:" | head -1 | cut -d' ' -f2)
```

### Batch Testing
```bash
# Test multiple users
for user_id in $(curl -s http://localhost:8989/api/v1/users | jq -r '.[]'); do
  curl http://localhost:8989/api/v1/users/$user_id
done
```

### Debug Mode
```env
# In .env
DEBUG=True  # Shows full stack traces
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | Change `API_PORT` in `.env` |
| Token expired | Generate new: `python scripts/generate_test_token.py` |
| User not found | Run: `python scripts/seed_database.py` |
| Connection error | Start: `docker-compose up -d` |
| Import error | Install: `pip install -r requirements.txt` |

---

**Quick Start:** `docker-compose up -d && cd apps/api && uvicorn app.main:app --reload --port 8989`

**Interactive Docs:** http://localhost:8989/docs
