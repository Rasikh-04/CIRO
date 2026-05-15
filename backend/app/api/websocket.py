from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.manager import manager

router = APIRouter()


@router.websocket("/ws/command")
async def command_feed(ws: WebSocket):
    await manager.connect_command(ws)
    try:
        while True:
            await ws.receive_text()  # keep connection alive
    except WebSocketDisconnect:
        manager.disconnect_command(ws)


@router.websocket("/ws/crisis/{crisis_id}")
async def crisis_feed(ws: WebSocket, crisis_id: str):
    await manager.connect_crisis(crisis_id, ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_crisis(crisis_id, ws)
