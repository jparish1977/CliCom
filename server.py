import asyncio
import websockets
import os
import time

PORT = int(os.getenv("PORT", 8080))
clients = {}
clients_lock = asyncio.Lock()
start_time = time.time()
SERVER_LOCATION = "MI, USA 🇺🇸"

# Handles HTTP HEAD/GET to avoid handshake errors
async def http_handler(path, request_headers):
    return 200, [("Content-Type", "text/plain")], b"WebSocket server OK\n"

# Broadcast message to everyone
async def broadcast(message, exclude=None):
    async with clients_lock:
        to_remove = []
        for ws in list(clients.keys()):
            if ws != exclude:
                try:
                    await ws.send(message)
                except:
                    to_remove.append(ws)
        for ws in to_remove:
            if ws in clients:
                left_name = clients.pop(ws)
                await broadcast(f"{left_name} left the chat.")
        await broadcast_online_users()

# Send updated online users list
async def broadcast_online_users():
    async with clients_lock:
        if clients:
            online_list = ", ".join(clients.values())
            msg = f"[Server] Online: {online_list}"
            for ws in clients.keys():
                try:
                    await ws.send(msg)
                except:
                    pass

# Handle each client connection
async def handler(websocket):
    try:
        username = await websocket.recv()
        async with clients_lock:
            clients[websocket] = username
        await broadcast(f"{username} joined the chat.")

        async for message in websocket:
            await broadcast(f"{username}: {message}", exclude=websocket)

    except websockets.ConnectionClosed:
        pass
    finally:
        async with clients_lock:
            if websocket in clients:
                left_name = clients.pop(websocket)
                await broadcast(f"{left_name} left the chat.")

# Periodic server status
async def server_status():
    while True:
        await asyncio.sleep(600)
        uptime = int(time.time() - start_time)
        h, m = divmod(uptime // 60, 60)
        s = uptime % 60
        msg = f"[Server] {SERVER_LOCATION} | Uptime: {h}h {m}m {s}s"
        await broadcast(msg)

# Main server
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
