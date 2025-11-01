# XP-38: Backend Comments System API

## 📋 Summary
Complete CRUD API for comments with soft delete support, pagination, authentication, and ownership verification.

---

## 📂 Files Changed/Added

```
cpsc362-group-proj/
├── apps/api/app/
│   ├── main.py                              # ✏️ MODIFIED - Added comments router
│   └── routers/
│       └── comments.py                      # ✅ NEW - Complete comments CRUD
│
├── scripts/
│   ├── sql/
│   │   ├── initial_schema - postgres.sql   # ✏️ MODIFIED - Added updated_at, deleted_at
│   │   └── alter_comments_add_timestamps.sql # ✅ NEW - Migration for existing DBs
│   └── test_comments_api.py                 # ✅ NEW - Interactive test suite
│
└── XP-38-REFERENCE.md                       # ✅ NEW - This file
```

---

## 🗑️ Files to Delete

These files are superseded by this reference:
- ❌ `XP-38-VERIFICATION.md`
- ❌ `XP-38-QUICK-REFERENCE.md`
- ❌ `docs/XP-38-API-TESTING.md`
- ❌ `scripts/sql/migration_001_add_comments_updated_at.sql`

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8989/api/v1/comments
```

### Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/posts/{post_id}/comments` | ✅ Required | Create comment on post |
| GET | `/posts/{post_id}/comments` | ❌ Public | Get all comments (paginated) |
| PUT | `/{comment_id}` | ✅ Required | Update own comment |
| DELETE | `/{comment_id}` | ✅ Required | Soft delete own comment |

---

## 📝 Database Schema Changes

### New Columns in `comments` Table

```sql
-- Added in initial_schema - postgres.sql
CREATE TABLE comments (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  post_id UUID NOT NULL,
  user_id UUID NOT NULL,
  content TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- ✅ NEW
  deleted_at TIMESTAMP DEFAULT NULL,                -- ✅ NEW (soft delete)
  -- Foreign keys...
);

-- Auto-update trigger for updated_at
CREATE TRIGGER trigger_update_comments_updated_at 
BEFORE UPDATE ON comments 
FOR EACH ROW 
EXECUTE FUNCTION update_comments_updated_at();
```

### Migration for Existing Databases

If your database already exists, run:
```bash
psql -U postgres -d your_database -f scripts/sql/alter_comments_add_timestamps.sql
```

Or in Supabase SQL Editor:
```sql
ALTER TABLE comments ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE comments ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

-- Add auto-update trigger (see alter_comments_add_timestamps.sql for full code)
```

---

## 🎯 Key Features

### ✨ Soft Delete Pattern
- Comments are **not** hard-deleted from the database
- `DELETE` endpoint sets `deleted_at` timestamp
- Soft-deleted comments are filtered from all GET queries
- Maintains data integrity and audit trail

### ✨ Auto-Update Timestamps
- `updated_at` automatically updates on every UPDATE
- Handled by PostgreSQL trigger
- No manual timestamp management needed

### ✨ Authentication & Authorization
- JWT-based authentication
- Users can only edit/delete their own comments
- Ownership verification on all mutations

### ✨ Validation
- Content: 1-500 characters
- No empty or whitespace-only comments
- UUID format validation
- Post existence verification

### ✨ Pagination
- Default: 50 comments per page
- Maximum: 100 comments per page
- Chronological ordering (oldest first)

---

## 🧪 Testing

### Interactive Test Script

```bash
# Start API first
cd apps/api
uvicorn app.main:app --reload --port 8989

# In another terminal, run test script
python scripts/test_comments_api.py

# Or with pre-configured token/post_id
python scripts/test_comments_api.py "YOUR_JWT_TOKEN" "YOUR_POST_UUID"
```

### Test Menu
```
Configuration:
  [0] Set JWT Token 🔑
  [1] Set Post ID 📝

Individual Tests (with prompts):
  [2] Test Create Comment 💬
  [3] Test Get Comments 📋
  [4] Test Update Comment ✏️
  [5] Test Delete Comment 🗑️
  [6] Test Error Cases 🧪

Batch (auto-run, no prompts):
  [7] Run All Tests 🚀

Other:
  [8] Show Status ⚙️
  [9] Exit 👋
```

---

## 📚 API Examples

### 1. Create Comment
```bash
curl -X POST "http://localhost:8989/api/v1/comments/posts/{post_id}/comments" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Great post!"}'
```

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id": "abc-123-...",
    "post_id": "xyz-789-...",
    "content": "Great post!",
    "author": {
      "id": "user-id",
      "username": "johndoe",
      "profile_pic": "https://..."
    },
    "created_at": "2025-10-31T14:30:00Z",
    "updated_at": "2025-10-31T14:30:00Z"
  },
  "message": "Comment created successfully"
}
```

### 2. Get Comments (Public)
```bash
curl "http://localhost:8989/api/v1/comments/posts/{post_id}/comments?page=1&page_size=50"
```

**Response (200):**
```json
{
  "success": true,
  "data": [
    {
      "id": "comment-1",
      "post_id": "post-id",
      "content": "First comment!",
      "author": {
        "id": "user-1",
        "username": "alice",
        "profile_pic": null
      },
      "created_at": "2025-10-31T10:00:00Z",
      "updated_at": "2025-10-31T10:00:00Z"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 50,
  "has_next": false
}
```

### 3. Update Comment
```bash
curl -X PUT "http://localhost:8989/api/v1/comments/{comment_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated comment text"}'
```

**Response (200):**
```json
{
  "success": true,
  "data": {
    "id": "comment-id",
    "post_id": "post-id",
    "content": "Updated comment text",
    "author": {...},
    "created_at": "2025-10-31T10:00:00Z",
    "updated_at": "2025-10-31T14:35:00Z"
  },
  "message": "Comment updated successfully"
}
```

### 4. Delete Comment (Soft Delete)
```bash
curl -X DELETE "http://localhost:8989/api/v1/comments/{comment_id}" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response (200):**
```json
{
  "success": true,
  "message": "Comment deleted successfully"
}
```

---

## ⚠️ Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid UUID format |
| 401 | Unauthorized - Missing/invalid JWT token |
| 403 | Forbidden - Not comment owner |
| 404 | Not Found - Comment or post doesn't exist |
| 422 | Validation Error - Invalid content (empty, too long, etc.) |
| 500 | Internal Server Error |

---

## 🚀 Quick Start

### 1. Database Setup

**New database:**
```bash
psql -U postgres -d your_db -f scripts/sql/initial_schema\ -\ postgres.sql
```

**Existing database:**
```bash
psql -U postgres -d your_db -f scripts/sql/alter_comments_add_timestamps.sql
```

### 2. Start API
```bash
cd apps/api
uvicorn app.main:app --reload --port 8989
```

### 3. Verify
Visit: http://localhost:8989/docs

### 4. Test
```bash
python scripts/test_comments_api.py
```

---

## 📊 Definition of Done

- [x] Can add comment to existing post
- [x] Cannot comment on non-existent post (404)
- [x] Comments include author info (username, profile_pic)
- [x] Users can only edit/delete own comments (403 if not owner)
- [x] Comments ordered chronologically (oldest first)
- [x] Pagination implemented (default 50, max 100)
- [x] Comment validation (1-500 chars, no whitespace-only)
- [x] 4 CRUD endpoints implemented
- [x] Soft delete with deleted_at timestamp
- [x] Auto-updating updated_at timestamp
- [x] Interactive test script with menu
- [x] Complete documentation

---

## 🔄 Code Changes Summary

### `apps/api/app/main.py`
```python
# Simplified imports
from .routers import users, health, comments

# Register router
app.include_router(comments.router, prefix="/api/v1")
```

### `apps/api/app/routers/comments.py` (NEW)
- Complete CRUD implementation
- Soft delete support
- Ownership verification
- Pagination
- Author information joins
- Comprehensive validation

### Database Schema
- Added `updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- Added `deleted_at TIMESTAMP DEFAULT NULL`
- Added auto-update trigger for `updated_at`

---

## 💡 Next Steps

1. Implement XP-41 (Posts API) to include comment counts
2. Consider adding comment reactions/likes
3. Add comment threading/replies (nested comments)
4. Implement real-time updates via WebSocket
5. Add comment moderation/reporting

---

**Completed:** October 31, 2025  
**Status:** ✅ Production Ready  
**Version:** 1.0.0
