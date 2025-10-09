import asyncio
import websockets
import os
import time

PORT = int(os.getenv("PORT", 8080))
clients = {}  # websocket -> username
start_time = time.time()
SERVER_LOCATION = "MI, USA 🇺🇸"

# --- Handle HEAD/GET requests (Render health checks) ---
async def http_handler(path, request_headers):
    return 200, [("Content-Type", "text/plain")], b"WebSocket server is running.\n"

# --- Broadcast to all clients ---
async def broadcast(message, exclude=None):
    disconnected = []
    for ws in list(clients.keys()):
        if ws != exclude:
            try:
                await ws.send(message)
            except:
                disconnected.append(ws)
    for ws in disconnected:
        if ws in clients:
            left_name = clients.pop(ws)
            await broadcast(f"{left_name} left the chat.")
    await broadcast_online_users()

# --- Show online users ---
async def broadcast_online_users():
    if clients:
        online_list = ", ".join(clients.values())
        msg = f"[Server] Online: {online_list}"
        for ws in list(clients.keys()):
            try:
                await ws.send(msg)
            except:
                pass

# --- Handle each client ---
async def handler(websocket):
    try:
        username = await websocket.recv()
        clients[websocket] = username
        await broadcast(f"{username} joined the chat.")
        await broadcast_online_users()

        async for message in websocket:
            if message.strip().lower() == "/help":
                help_text = (
                    "[Server] Commands:\n"
                    "  /help - Show this message\n"
                    "  Just type anything else to chat\n"
                )
                await websocket.send(help_text)
            else:
                await broadcast(f"{username}: {message}", exclude=websocket)

    except websockets.ConnectionClosed:
        pass
    finally:
        if websocket in clients:
            left_name = clients.pop(websocket)
            await broadcast(f"{left_name} left the chat.")
            await broadcast_online_users()

# --- Server status broadcast ---
async def server_status():
    while True:
        await asyncio.sleep(600)
        uptime = int(time.time() - start_time)
        h, m = divmod(uptime // 60, 60)
        s = uptime % 60
        ping = 0
        msg = f"[Server] {SERVER_LOCATION} | Uptime: {h}h {m}m {s}s | Ping: {ping} ms"
        await broadcast(msg)

# --- Main entry ---
async def main():
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        PORT,
        process_request=http_handler
    )
    print(f"✅ Chat server running on ws://0.0.0.0:{PORT}")
    asyncio.create_task(server_status())
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
