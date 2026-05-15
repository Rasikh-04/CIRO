from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        self._command_connections: list[WebSocket] = []
        self._crisis_connections: dict[str, list[WebSocket]] = {}

    async def connect_command(self, ws: WebSocket):
        await ws.accept()
        self._command_connections.append(ws)

    def disconnect_command(self, ws: WebSocket):
        self._command_connections = [c for c in self._command_connections if c is not ws]

    async def connect_crisis(self, crisis_id: str, ws: WebSocket):
        await ws.accept()
        self._crisis_connections.setdefault(crisis_id, []).append(ws)

    def disconnect_crisis(self, crisis_id: str, ws: WebSocket):
        conns = self._crisis_connections.get(crisis_id, [])
        self._crisis_connections[crisis_id] = [c for c in conns if c is not ws]

    async def broadcast(self, data: dict):
        dead = []
        for ws in self._command_connections:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_command(ws)

    async def broadcast_crisis(self, crisis_id: str, data: dict):
        conns = self._crisis_connections.get(crisis_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_crisis(crisis_id, ws)


manager = ConnectionManager()
