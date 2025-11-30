# AI Service - Configuration & Usage Guide

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Directory Structure](#directory-structure)
5. [Available Endpoints](#available-endpoints)
6. [Development Workflow](#development-workflow)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The AI Service provides three core AI capabilities for our social media platform:

| Feature | Technology | Location | Sprint Ticket |
|---------|-----------|----------|---------------|
| **Video Transcription** | OpenAI Whisper | Local (Docker) | XP-55 |
| **Text Moderation** | Google ShieldGemma 2B | Local (Docker) | XP-56 |
| **Image Moderation** | Google Gemini | Cloud API | XP-57 |
| **Video Summarization** | Google Gemini | Cloud API | XP-58 |

**Service Details:**
- **Port:** 8002
- **Framework:** FastAPI
- **Container:** `social_media_ai`
- **Docker Network:** `app-network`

---

## Quick Start

### 1. Initial Setup

```bash
# Create the .env file from template
cp apps/ai/.env.example apps/ai/.env

# Edit .env and add your Gemini API key
nano apps/ai/.env
```

### 2. Start the AI Service

```bash
# Start just the AI service
docker-compose up ai

# Or start all services
docker-compose up -d
```

### 3. Verify It's Running

```bash
# Check health endpoint
curl http://localhost:8002/health

# Expected response:
# {"status":"healthy","service":"ai"}

# Open Swagger UI
open http://localhost:8002/docs
```

---

## Configuration

### Configuration Hierarchy (Priority Order)

The configuration system loads values in this order:

1. **Environment variables** from `docker-compose.yml` (highest priority)
2. **`.env` file** in `apps/ai/`
3. **Default values** in `config.py` (lowest priority - fallback)

### Environment Variables

#### Required Variables

| Variable | Description | Where to Get It | Example |
|----------|-------------|-----------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | [Google AI Studio](https://aistudio.google.com/app/apikey) | `AIza...` |

#### Optional Variables (with defaults)

| Variable | Default | Options | Purpose |
|----------|---------|---------|---------|
| `WHISPER_MODEL_SIZE` | `base` | `tiny`, `base`, `small`, `medium`, `large` | Whisper accuracy vs speed |
| `SHIELDGEMMA_DEVICE` | `cpu` | `cpu`, `cuda` | Run on CPU or GPU |
| `IMAGE_MODERATION_THRESHOLD` | `strict` | `strict`, `moderate`, `lenient` | Image safety level |
| `MINIO_ENDPOINT` | `minio:9000` | Docker service name | MinIO connection |
| `MINIO_BUCKET` | `media` | Bucket name | Where media files are stored |

### How to Change Configuration

#### ✅ **Recommended: Edit `.env` file**

```bash
# apps/ai/.env
GEMINI_API_KEY=your_actual_api_key_here

# Model Settings
WHISPER_MODEL_SIZE=tiny              # Change model size here
SHIELDGEMMA_DEVICE=cpu
IMAGE_MODERATION_THRESHOLD=strict

# MinIO Settings (usually don't need to change)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
MINIO_BUCKET=media
```

**After editing `.env`, restart the service:**

```bash
docker-compose restart ai
```

#### ❌ **Not Recommended: Hardcoding in `config.py`**

Don't edit default values in `config.py` unless you're changing the system-wide defaults for all developers.

### Whisper Model Size Guide

Choose based on your needs:

| Model | Size | Speed | Accuracy | Recommended For |
|-------|------|-------|----------|-----------------|
| `tiny` | 39 MB | Very Fast | Lower | Development/Testing |
| `base` | 74 MB | Fast | Good | **Default - Production** |
| `small` | 244 MB | Medium | Better | High accuracy needs |
| `medium` | 769 MB | Slow | Great | Very high accuracy |
| `large` | 1.5 GB | Very Slow | Best | Not recommended (resource intensive) |

**To change model size:**
```bash
# Edit apps/ai/.env
WHISPER_MODEL_SIZE=tiny  # or small, medium, large

# Restart
docker-compose restart ai
```

---

## Directory Structure

```
apps/ai/
├── app/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app & routes
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                # Settings class (DO NOT EDIT VALUES)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── whisper_service.py       # XP-55: Video transcription
│   │   ├── shieldgemma_service.py   # XP-56: Text moderation
│   │   ├── gemini_service.py        # XP-57 & XP-58: Image mod + Video summary
│   │   ├── minio_client.py          # MinIO file access
│   │   └── ai_pipeline.py           # XP-59: Orchestration
│   └── routers/
│       └── __init__.py
├── Dockerfile                       # Container definition
├── requirements.txt                 # Python dependencies
├── .env                            # YOUR CONFIG (git-ignored)
└── .env.example                    # Template for .env
```

---

## Available Endpoints

Once implemented, the AI service will expose these endpoints:

### Health & Documentation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/docs` | GET | Swagger UI (interactive API docs) |
| `/` | GET | Service info |

### AI Features (To Be Implemented)

#### XP-55: Video Transcription

```http
POST /transcribe
POST /transcribe/minio?filename={filename}
```

**Purpose:** Convert video/audio to text using Whisper.

#### XP-56: Text Moderation

```http
POST /moderate/text
```

**Purpose:** Check if text is safe using ShieldGemma.

#### XP-57: Image Moderation

```http
POST /moderate/image
```

**Purpose:** Check if image is safe using Gemini.

#### XP-58: Video Summarization

```http
POST /summarize
POST /summarize/minio?filename={filename}
```

**Purpose:** Generate video summary using Gemini.

#### XP-59: Full Pipelines

```http
POST /process-video/minio?filename={filename}
POST /process-image
```

**Purpose:** Run complete AI pipeline (transcribe → moderate → summarize).

---

## Development Workflow

### Starting Development

1. **Pull latest code**
   ```bash
   git pull origin develop
   ```

2. **Start the AI service**
   ```bash
   docker-compose up ai
   ```

3. **Code hot-reloads automatically** (thanks to volume mount)

### Making Changes

1. **Edit Python files** in `apps/ai/app/`
2. **Save** - Uvicorn auto-reloads
3. **Check logs** for errors:
   ```bash
   docker logs -f social_media_ai
   ```

### Adding New Dependencies

1. **Add to `requirements.txt`**
   ```txt
   # requirements.txt
   new-package>=1.0.0
   ```

2. **Rebuild the container**
   ```bash
   docker-compose build --no-cache ai
   docker-compose up ai
   ```

### Working on Your Ticket

#### Example: XP-43 (Whisper Transcription)

1. **Create service file**
   ```bash
   touch apps/ai/app/services/whisper_service.py
   ```

2. **Implement the service** (see ticket description)

3. **Add endpoint to `main.py`**
   ```python
   from app.services.whisper_service import WhisperService
   
   @app.post("/transcribe")
   async def transcribe_video(file: UploadFile = File(...)):
       result = WhisperService.transcribe(file_bytes=await file.read())
       return result
   ```

4. **Test via Swagger UI**
   - Go to http://localhost:8002/docs
   - Find your endpoint
   - Click "Try it out"
   - Upload test file
   - Execute

---

## Testing

### Manual Testing (Swagger UI)

1. **Open Swagger UI**
   ```
   http://localhost:8002/docs
   ```

2. **Select endpoint** (e.g., `/transcribe`)

3. **Click "Try it out"**

4. **Upload test file** or provide parameters

5. **Execute** and view response

### Command Line Testing (curl)

```bash
# Test health
curl http://localhost:8002/health

# Test transcription (once implemented)
curl -X POST http://localhost:8002/transcribe \
  -F "file=@test_video.mp4"

# Test from MinIO (once implemented)
curl -X POST "http://localhost:8002/transcribe/minio?filename=uuid_video.mp4"
```

### Testing with Python

```python
import httpx

async def test_transcription():
    with open("test_video.mp4", "rb") as f:
        files = {"file": f}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8002/transcribe",
                files=files,
                timeout=120.0
            )
            print(response.json())
```

---

## Troubleshooting

### Service Won't Start

#### Problem: `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
```bash
# Rebuild without cache
docker-compose stop ai
docker-compose rm -f ai
docker-compose build --no-cache ai
docker-compose up ai
```

#### Problem: `ValidationError: Extra inputs are not permitted`

**Cause:** Environment variable defined in docker-compose but not in `config.py`.

**Solution:** Add the field to `apps/ai/app/core/config.py`:
```python
class Settings(BaseSettings):
    NEW_VARIABLE: str = "default_value"
```

### Configuration Issues

#### Problem: Changes to `.env` not taking effect

**Solution:**
```bash
# Restart the container
docker-compose restart ai

# Or force recreation
docker-compose up -d --force-recreate ai
```

#### Problem: Can't find `.env` file

**Solution:**
```bash
# Create from template
cp apps/ai/.env.example apps/ai/.env

# Edit it
nano apps/ai/.env
```

### Model Loading Issues

#### Problem: Whisper model download is slow

**Cause:** Models are large (74MB - 1.5GB).

**Solution:** Be patient on first run. Models are cached in `ai_model_cache` volume.

#### Problem: Out of memory when loading ShieldGemma

**Cause:** Model is 2GB+ in memory.

**Solution:** Use smaller Whisper model or increase Docker memory:
```bash
# Edit .env
WHISPER_MODEL_SIZE=tiny  # Instead of base/medium
```

### API Connection Issues

#### Problem: Can't reach MinIO

**Check Docker network:**
```bash
docker exec social_media_ai ping minio
# Should succeed
```

**Check MinIO is running:**
```bash
docker ps | grep minio
```

#### Problem: Gemini API key invalid

**Verify key:**
```bash
docker exec social_media_ai env | grep GEMINI_API_KEY
# Should show your key
```

**Get new key:** https://aistudio.google.com/app/apikey

### Performance Issues

#### Problem: Transcription is too slow

**Solutions:**
1. Use smaller Whisper model: `WHISPER_MODEL_SIZE=tiny`
2. Use shorter test videos during development
3. Process asynchronously in production

#### Problem: Container using too much memory

**Check resource usage:**
```bash
docker stats social_media_ai
```

**Solutions:**
1. Use smaller models
2. Increase Docker Desktop memory limits
3. Add memory limits to docker-compose:
   ```yaml
   ai:
     deploy:
       resources:
         limits:
           memory: 4G
   ```

---

## Useful Commands

### Container Management

```bash
# View logs
docker logs -f social_media_ai

# Enter container shell
docker exec -it social_media_ai /bin/bash

# Restart service
docker-compose restart ai

# Stop service
docker-compose stop ai

# Rebuild and restart
docker-compose up -d --build ai

# Remove container and volumes
docker-compose down -v
```

### Debugging

```bash
# Check if packages installed
docker exec social_media_ai pip list

# Check environment variables
docker exec social_media_ai env

# Test imports
docker exec social_media_ai python -c "from app.core.config import settings; print(settings.WHISPER_MODEL_SIZE)"

# Check MinIO connection
docker exec social_media_ai python -c "from app.services.minio_client import MinioClient; print(MinioClient.get_client().bucket_exists('media'))"
```

### Performance

```bash
# View resource usage
docker stats social_media_ai

# Check disk space
docker system df

# Clean up unused images
docker system prune -a
```

---

## Getting Help

### Resources

- **Swagger UI:** http://localhost:8002/docs
- **Whisper Docs:** https://github.com/openai/whisper
- **Gemini Docs:** https://ai.google.dev/gemini-api/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com/

### Contact

- **Group Leader:** @jacobr
- **Team Channel:** CPSC 362 Group (Discord)
- **Jira Board:** https://csuf-cpsc362-group.atlassian.net/jira/software/projects/XP/boards/1/backlog

### Common Questions

**Q: Do I need a GPU?**
A: No, all models work on CPU. GPU is optional for faster processing.

**Q: Do I need to pay for Gemini API?**
A: Free tier includes generous limits. Check: https://ai.google.dev/pricing

**Q: How do I know which ticket to work on?**
A: Check the sprint board and claim a ticket that's marked "TO DO".

**Q: Can I change the port?**
A: Yes, edit docker-compose.yml and change `"8002:8002"` to your preferred port.

---

## Sprint Ticket Reference

| Ticket | File to Edit | Purpose |
|--------|-------------|---------|
| **XP-55** | `whisper_service.py` | Implement video transcription |
| **XP-56** | `shieldgemma_service.py` | Implement text moderation |
| **XP-57** | `gemini_service.py` | Implement image moderation |
| **XP-58** | `gemini_service.py` | Implement video summarization |
| **XP-59** | `ai_pipeline.py`, `main.py` | Orchestrate all services |
| **XP-60** | ✅ Done | Docker setup complete |

---

## License

Internal project - CPSC 362 Group Project

---
```
Last Updated: 2025-11-29  
Maintained By: Jacob R.
```