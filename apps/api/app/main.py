from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, health  # include both routers

app = FastAPI(
    title="CPSC Social Media API",
    version="1.0.0",
    description="Social media platform backend with AI-powered features"
)

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}

# Register routers
# Health router
app.include_router(health.router, prefix="/api")


app.include_router(auth.router)
