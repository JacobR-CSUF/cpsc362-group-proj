"""
FastAPI Main Application
Entry point for the social media backend API
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# CORRECTED IMPORTS - Use relative imports since we're inside app/
from .routers import users, health, comments
from .services.supabase_client import SupabaseClient

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Social Media Backend API",
    description="Backend API for social media platform with user management, posts, and interactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    print("\n" + "="*60)
    print("  Starting Social Media Backend API")
    print("="*60 + "\n")
    
    # Test Supabase connection
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


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("\n👋 Shutting down API...")


# Global exception handler
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


# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint"""
    return {
        "message": "Social Media Backend API",
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


# Additional route registration examples (for future implementation)
# from .routers import posts, comments, likes, follows
# app.include_router(posts.router, prefix="/api/v1")
# app.include_router(comments.router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("API_PORT", 8989))
    debug = os.getenv("DEBUG", "True") == "True"
    
    uvicorn.run(
        "app.main:app",  # Changed from "apps.api.app.main:app"
        host="0.0.0.0",
        port=port,
        reload=debug,
        log_level="info"
    )