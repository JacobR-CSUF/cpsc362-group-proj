# cpsc362-group-proj
Group assignment that takes the Social Media subject for our project.
### Enhancing a global photo & video sharing platform with AI-powered experiences.

---

## Table of Contents
- [Project Description](#project-description)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Installation Instructions](#installation-instructions)
- [Security Setup](#security-setup)
- [Development Tools](#development-tools)

---

## Project Description

A social media platform backend API with user management, authentication, and AI-powered features. Built with FastAPI, Supabase, and PostgreSQL with Row-Level Security.

**Core Features:**
- User management (CRUD operations)
- JWT authentication
- Row-level security (RLS)
- Database seeding tools
- Comprehensive API documentation

---

## Quick Start

```bash
# 1. Clone and setup
git clone <repository>
cd cpsc362-group-proj
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start services
docker-compose up -d

# 4. Access API
# Docs: http://localhost:8001/docs
# API: http://localhost:8001
```

---

## API Documentation

### 📚 Complete Implementation Guide
**[IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)** - Comprehensive technical documentation

### 🚀 API Endpoints

**Base URL:** `http://localhost:8001`

**Health Check:**
```bash
curl http://localhost:8001/health
```

**User Endpoints:**
```bash
# Get public profile (no auth)
curl http://localhost:8001/api/v1/users/<user-id>

# Get own profile (auth required)
curl -H "Authorization: Bearer <token>" \
     http://localhost:8001/api/v1/users/me

# Update profile (auth required)
curl -X PUT \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"username": "new_name"}' \
     http://localhost:8001/api/v1/users/me

# Delete account (auth required)
curl -X DELETE \
     -H "Authorization: Bearer <token>" \
     http://localhost:8001/api/v1/users/me
```

**Interactive Documentation:**
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

---

## Installation Instructions

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git

### For Developers

1. **Setup virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Mac/Linux
    venv\Scripts\activate     # Windows
    ```
    
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    
3. **Configure environment:**
    ```bash
    cp .env.example .env
    # Edit .env with your Supabase credentials
    ```
    
4. **Start services:**
    ```bash
    docker-compose up -d
    ```
    
5. **Initialize database:**
    ```bash
    # Apply RLS policies
    # Open http://localhost:3100 (Supabase)
    # Copy scripts/sql/rls_rules.sql to SQL Editor
    # Run the SQL
    
    # Seed test data
    python scripts/seed_database.py
    ```


### Access Points

**API Server:**
- API: http://localhost:8001
- Docs: http://localhost:8001/docs

**Backend Services:**
- Supabase: http://localhost:3100
- MinIO: http://localhost:9001 (minioadmin/minioadmin123)

---

## Security Setup

### 🔐 Row Level Security (RLS)

Complete database-level security ensuring users can only access authorized data.

**Quick Setup:**
1. Open Supabase SQL Editor: http://localhost:3100
2. Copy `scripts/sql/rls_rules.sql`
3. Execute in SQL Editor

**Features:**
- ✅ Users can only edit their own data
- ✅ Post visibility controls (public/followers/private)
- ✅ Private messaging
- ✅ Protected friend suggestions
- ✅ Can't interact with invisible posts

**Testing:**
```bash
python scripts/test_rls.py
```

### 🔑 JWT Authentication

**Generate test tokens:**
```bash
python scripts/generate_test_token.py
```

**Use in requests:**
```bash
export TOKEN="<your-jwt-token>"
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/api/v1/users/me
```

---

## Development Tools

### Database Seeding
```bash
python scripts/seed_database.py

# Options:
# 1. Seed 5 hardcoded test users
# 2. Seed 20 realistic users (Faker)
# 3. Seed EVERYTHING (users, media, posts, follows, likes)
# 4. Clear all test data
```

### Token Generator
```bash
python scripts/generate_test_token.py

# Generate tokens for:
# - Manual user entry
# - Existing database users
# - Decode existing tokens
```

### RLS Testing
```bash
python scripts/test_rls.py
```

---

## Project Structure

```
apps/api/
├── app/
│   ├── main.py              # FastAPI application
│   ├── dependencies.py      # Auth middleware
│   ├── routers/
│   │   └── users.py        # User CRUD endpoints
│   └── services/
│       └── supabase_client.py  # Database client

scripts/
├── sql/
│   ├── initial_schema.sql   # Database schema
│   └── rls_rules.sql        # RLS policies ⭐
├── seed_database.py         # Test data generator
├── generate_test_token.py   # JWT token generator
└── test_rls.py             # RLS testing

docs/
├── IMPLEMENTATION_SUMMARY.md    # Complete guide ⭐
├── API_QUICK_REFERENCE.md       # API reference
└── SETUP.md                     # Setup guide
```

---

## Technology Stack

**Backend:**
- FastAPI 0.115.0
- Uvicorn 0.30.6
- Pydantic 2.9.2

**Database:**
- Supabase 2.6.0
- PostgreSQL with RLS

**Authentication:**
- PyJWT 2.8.0
- python-jose 3.3.0

**Development:**
- Faker 37.11.0
- python-dotenv 1.0.1

---

## API Features

### Implemented ✅
- User registration (via seeding)
- User authentication (JWT)
- Get user profile (public/private)
- Update user profile
- Delete user account
- Row-level security
- Health checks
- API documentation

### Planned 🚧
- Posts CRUD
- Comments system
- Likes functionality
- Follow/unfollow
- Private messaging
- Media upload
- Friend suggestions
- Real-time updates

---

## Testing

### Manual Testing
```bash
# 1. Generate token
python scripts/generate_test_token.py

# 2. Test endpoints
export TOKEN="<generated-token>"

# Get profile
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:8001/api/v1/users/me

# Update profile
curl -X PUT \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"username": "new_name"}' \
     http://localhost:8001/api/v1/users/me
```

### Interactive Testing
Open http://localhost:8001/docs for Swagger UI with built-in testing.

---

## Environment Configuration

Required environment variables in `.env`:

```env
# Supabase
SUPABASE_URL=http://localhost:8000
SUPABASE_SERVICE_ROLE_KEY=<your-service-key>
SUPABASE_ANON_KEY=<your-anon-key>

# JWT
JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long

# API
API_PORT=8001
DEBUG=True
```

---

## Troubleshooting

### Common Issues

**"Missing environment variables"**
- Create `.env` file from `.env.example`
- Verify all required variables are set

**"Token has expired"**
- Generate new token: `python scripts/generate_test_token.py`

**"User not found"**
- Run seed script: `python scripts/seed_database.py`

**"Port already in use"**
- Change `API_PORT` in `.env`
- Or kill process on port 8001

**"Database connection failed"**
- Start Supabase: `docker-compose up -d`
- Verify `SUPABASE_URL` is correct

---

## Documentation

- **[Complete Implementation Guide](docs/IMPLEMENTATION_SUMMARY.md)** - Everything you need
- **[API Quick Reference](docs/API_QUICK_REFERENCE.md)** - Quick API usage
- **[API Docs](http://localhost:8001/docs)** - Interactive Swagger UI

---

## Contributing

See [IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md) for:
- Code style guidelines
- Commit message format
- Testing requirements
- Development workflow

---

## License

[Project License Information]

---

**Version:** 1.0.0  
**Status:** ✅ Production Ready (User Management)  
**Last Updated:** October 2024
