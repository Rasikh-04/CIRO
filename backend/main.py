from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import signals, crisis, websocket, debug
from app.db.init_db import init_db

app = FastAPI(title="CIRO Backend", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables on startup
init_db()

# ── v1 routes (agents + internal scripts) ────────────────────────────────────
app.include_router(signals.router, prefix="/api")
app.include_router(crisis.router,  prefix="/api")

# ── v2 routes (dashboard + mobile frontend) ───────────────────────────────────
app.include_router(crisis.router,  prefix="/api/v2", include_in_schema=False)
app.include_router(debug.router,   prefix="/api/v2/debug")

# ── WebSocket ─────────────────────────────────────────────────────────────────
app.include_router(websocket.router)


@app.get("/")
def root():
    return {"status": "CIRO backend running", "version": "2.0"}
