from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active_connections: dict[int, WebSocket] = {}

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int) -> None:
        self.active_connections.pop(user_id, None)

    async def send_status(self, user_id: int, status: str) -> None:
        websocket = self.active_connections.get(user_id)
        if websocket:
            await websocket.send_json({"status": status})


manager = ConnectionManager()
