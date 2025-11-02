import asyncio
import json
from aiohttp import web

connected_users = {}  # ws -> username

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    connected_users[ws] = "Unknown"
    print("🔌 Client connected")

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            data = json.loads(msg.data)
            msg_type = data.get("type")

            # --- New user joined ---
            if msg_type == "join":
                name = data["name"]
                connected_users[ws] = name
                print(f"🟢 {name} joined")
                await broadcast_system(f"{name} joined the chat. ({len(connected_users)} online)")

            # --- User sent message ---
            elif msg_type == "message":
                name = data["name"]
                color = data.get("color", "")
                text = data["text"]
                await broadcast_message(name, color, text)

            # --- /who command ---
            elif msg_type == "who":
                users = [n for n in connected_users.values()]
                await ws.send_json({"type": "who", "users": users})

            # --- User leaving ---
            elif msg_type == "leave":
                name = connected_users.get(ws, "Unknown")
                await ws.close()
                print(f"🔴 {name} left")
                del connected_users[ws]
                await broadcast_system(f"{name} left the chat. ({len(connected_users)} online)")

    # Connection cleanup
    if ws in connected_users:
        name = connected_users[ws]
        del connected_users[ws]
        await broadcast_system(f"{name} disconnected unexpectedly. ({len(connected_users)} online)")
        print(f"⚪ {name} disconnected")

    return ws


async def broadcast_message(name, color, text):
    """Send message to all clients."""
    msg_data = {"type": "message", "name": name, "color": color, "text": text}
    for ws in list(connected_users.keys()):
        await safe_send(ws, msg_data)


async def broadcast_system(text):
    """Send system notification."""
    msg_data = {"type": "system", "text": text}
    for ws in list(connected_users.keys()):
        await safe_send(ws, msg_data)


async def safe_send(ws, data):
    try:
        await ws.send_json(data)
    except Exception:
        if ws in connected_users:
            del connected_users[ws]


async def index(request):
    return web.Response(text="Clicom Chat Server is running.", content_type="text/plain")


app = web.Application()
app.add_routes([
    web.get("/", index),
    web.get("/ws", websocket_handler)
])

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=10000)
