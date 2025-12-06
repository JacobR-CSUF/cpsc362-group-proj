"""
FastAPI Main Application
Entry point for the social media backend API
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

from .routers import auth, users, health, posts, likes, comments, media
from .services.supabase_client import SupabaseClient

load_dotenv()

app = FastAPI(
    title="CPSC Social Media API",
    description="Social media platform backend with AI-powered features",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
default_origins = [
    "https://project.geeb.pp.ua",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "https://project.geeb.pp.ua",
]
allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", ",".join(default_origins)).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    print("\n" + "="*60)
    print("  Starting Social Media Backend API")
    print("="*60 + "\n")
    
    print("Testing Supabase connection...")
    health = await SupabaseClient.health_check()
    
    if health["connected"]:
        print(f"✅ {health['message']}")
    else:
        print(f"⚠️  Supabase connection failed: {health['error']}")
        print("   The API will start, but database operations may fail.")
    
    print(f"\n📡 API running on: http://localhost:{os.getenv('API_PORT', 8989)}")
    print(f"📚 API docs: http://localhost:{os.getenv('API_PORT', 8989)}/docs")
    print("\n" + "="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("\n👋 Shutting down API...")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc) if os.getenv("DEBUG") == "True" else "An error occurred"
        }
    )


@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "CPSC Social Media API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Comprehensive health check endpoint
    Returns status of API and connected services
    """
    supabase_health = await SupabaseClient.health_check()
    
    return {
        "status": "healthy" if supabase_health["connected"] else "degraded",
        "services": {
            "api": {
                "status": "healthy",
                "version": "1.0.0"
            },
            "supabase": supabase_health
        }
    }


# Register routers
app.include_router(users.router, prefix="/api/v1")
app.include_router(comments.router, prefix="/api/v1")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(posts.router, prefix="/api/v1") 
app.include_router(likes.router)
app.include_router(media.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8989))
    debug = os.getenv("DEBUG", "True") == "True"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info"
    )
