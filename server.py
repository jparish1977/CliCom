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
        if msg.type != web.WSMsgType.TEXT:
            continue
        try:
            data = json.loads(msg.data)
        except:
            continue

        msg_type = data.get("type")

        # --- User joins ---
        if msg_type == "join":
            name = data.get("name", "Guest")
            connected_users[ws] = name
            print(f"🟢 {name} joined")
            await broadcast_system(f"{name} joined the chat. ({len(connected_users)} online)")
            await broadcast_active_users()

        # --- User message ---
        elif msg_type == "message":
            name = data.get("name", "Guest")
            color = data.get("color", "6")
            text = data.get("text", "")
            await broadcast_message(name, color, text)

        # --- /who command ---
        elif msg_type == "who":
            users = list(connected_users.values())
            await ws.send_json({"type": "who", "users": users})

        # --- User leaves ---
        elif msg_type == "leave":
            name = connected_users.get(ws, "Unknown")
            if ws in connected_users: del connected_users[ws]
            await ws.close()
            print(f"🔴 {name} left")
            await broadcast_system(f"{name} left the chat. ({len(connected_users)} online)")
            await broadcast_active_users()

    # --- Unexpected disconnect ---
    if ws in connected_users:
        name = connected_users[ws]
        del connected_users[ws]
        await broadcast_system(f"{name} disconnected unexpectedly. ({len(connected_users)} online)")
        await broadcast_active_users()
        print(f"⚪ {name} disconnected")

    return ws

async def broadcast_message(name, color, text):
    msg_data = {"type":"message","name":name,"color":color,"text":text}
    for ws in list(connected_users.keys()):
        try:
            await ws.send_json(msg_data)
        except:
            if ws in connected_users: del connected_users[ws]

async def broadcast_system(text):
    msg_data = {"type":"system","text":text}
    for ws in list(connected_users.keys()):
        try:
            await ws.send_json(msg_data)
        except:
            if ws in connected_users: del connected_users[ws]

async def broadcast_active_users():
    users = list(connected_users.values())
    msg_data = {"type":"active_users","users":users}
    for ws in list(connected_users.keys()):
        try:
            await ws.send_json(msg_data)
        except:
            if ws in connected_users: del connected_users[ws]

async def index(request):
    return web.Response(text="Clicom Chat Server is running.", content_type="text/plain")

app = web.Application()
app.add_routes([
    web.get("/", index),
    web.get("/ws", websocket_handler)
])

if __name__ == "__main__":
    # Render uses $PORT environment variable
    import os
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)
