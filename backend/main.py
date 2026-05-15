from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import signals, crisis, websocket
from app.db.init_db import init_db

app = FastAPI(title="CIRO Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
init_db()

# Register routers
app.include_router(signals.router, prefix="/api")
app.include_router(crisis.router, prefix="/api")
app.include_router(websocket.router)

@app.get("/")
def root():
    return {"status": "CIRO backend running"}