from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health # users, auth  # API list to develop 

app = FastAPI(title="CPSC Social Media", version="1.0")

# set CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health") # check the server status
async def health_check():
    return {"status": "ok"}

# Register router of each API (will be revised)
app.include_router(health.router, prefix="/api")
# app.include_router(users.router)
# app.include_router(auth.router)
