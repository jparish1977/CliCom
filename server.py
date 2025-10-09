import asyncio
import websockets
import time
import os

PORT = int(os.getenv("PORT", 8080))
clients = {}  # websocket -> username
clients_lock = asyncio.Lock()
start_time = time.time()
SERVER_LOCATION = "MI, USA 🇺🇸"

# --- HTTP handler for health checks ---
async def http_handler(path, request_headers):
    return 200, [("Content-Type", "text/plain")], b"WebSocket server running.\n"

# --- Broadcast helper ---
async def broadcast_message(message, exclude=None):
    async with clients_lock:
        to_remove = []
        for ws in list(clients.keys()):
            if ws != exclude:
                try:
                    await ws.send(message)
                except:
                    to_remove.append(ws)
        for ws in to_remove:
            clients.pop(ws, None)

# --- Broadcast online users ---
async def broadcast_online_users():
    async with clients_lock:
        if clients:
            online_list = ", ".join(clients.values())
            msg = f"[Server] Online users: {online_list}"
            for ws in list(clients.keys()):
                try:
                    await ws.send(msg)
                except:
                    clients.pop(ws, None)

# --- Each client connection ---
async def handler(websocket):
    try:
        username = await websocket.recv()
        async with clients_lock:
            clients[websocket] = username
        join_msg = f"{username} joined the chat."
        print(join_msg)
        await broadcast_message(join_msg)
        await broadcast_online_users()

        async for message in websocket:
            print(f"{username}: {message}")
            await broadcast_message(f"{username}: {message}", exclude=websocket)

    except websockets.ConnectionClosed:
        pass
    finally:
        async with clients_lock:
            if websocket in clients:
                left_name = clients.pop(websocket)
                leave_msg = f"{left_name} left the chat."
                print(leave_msg)
                await broadcast_message(leave_msg)
                await broadcast_online_users()

# --- Periodic server status ---
async def server_status():
    while True:
        await asyncio.sleep(600)
        uptime = int(time.time() - start_time)
        h, m = divmod(uptime // 60, 60)
        s = uptime % 60
        msg = f"[Server] Connected | {SERVER_LOCATION} | Uptime: {h}h {m}m {s}s | Ping: 0 ms"
        print(msg)
        await broadcast_message(msg)

# --- Main ---
async def main():
    server = await websockets.serve(
        handler,
        "0.0.0.0",
        PORT,
        process_request=http_handler  # avoids HEAD crash
    )
    print(f"✅ PulseChat WebSocket server running on port {PORT}")
    asyncio.create_task(server_status())
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
