from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        self.command_connections: List[WebSocket] = []
        self.crisis_connections: Dict[str, List[WebSocket]] = {}

    async def connect_command(self, ws: WebSocket):
        await ws.accept()
        self.command_connections.append(ws)

    def disconnect_command(self, ws: WebSocket):
        if ws in self.command_connections:
            self.command_connections.remove(ws)

    async def connect_crisis(self, crisis_id: str, ws: WebSocket):
        await ws.accept()
        if crisis_id not in self.crisis_connections:
            self.crisis_connections[crisis_id] = []
        self.crisis_connections[crisis_id].append(ws)

    def disconnect_crisis(self, crisis_id: str, ws: WebSocket):
        conns = self.crisis_connections.get(crisis_id, [])
        if ws in conns:
            conns.remove(ws)

    async def broadcast(self, message: dict, crisis_id: str):
        dead_command = []
        for ws in self.command_connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead_command.append(ws)
        for ws in dead_command:
            self.command_connections.remove(ws)

        dead_crisis = []
        for ws in self.crisis_connections.get(crisis_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                dead_crisis.append(ws)
        for ws in dead_crisis:
            self.crisis_connections[crisis_id].remove(ws)

manager = ConnectionManager()
