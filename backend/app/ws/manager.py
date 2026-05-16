from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, crisis_id: str):
        await websocket.accept()
        if crisis_id not in self.active_connections:
            self.active_connections[crisis_id] = []
        self.active_connections[crisis_id].append(websocket)

    def disconnect(self, websocket: WebSocket, crisis_id: str):
        if crisis_id in self.active_connections:
            if websocket in self.active_connections[crisis_id]:
                self.active_connections[crisis_id].remove(websocket)

    async def broadcast(self, message: dict, crisis_id: str):
        if crisis_id in self.active_connections:
            for connection in self.active_connections[crisis_id]:
                await connection.send_json(message)

manager = ConnectionManager()
