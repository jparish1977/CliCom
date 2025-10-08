import asyncio
import websockets
import time
import os

PORT = int(os.getenv("PORT", 8080))
clients = {}  # websocket -> username
clients_lock = asyncio.Lock()  # ensures thread-safe access
start_time = time.time()
SERVER_LOCATION = "MI, USA"

# --- Broadcast helper ---
async def broadcast(message, exclude=None):
    async with clients_lock:
        to_remove = []
        for ws in list(clients.keys()):
            if ws != exclude:
                try:
                    await ws.send(message)
                except:
                    to_remove.append(ws)
        # Remove disconnected clients
        for ws in to_remove:
            if ws in clients:
                left_name = clients.pop(ws)
                leave_msg = f"{left_name} left the chat."
                print(leave_msg)
                await broadcast(leave_msg, exclude=ws)
        # Update online users after broadcast
        await broadcast_online_users()

# --- Broadcast online users ---
async def broadcast_online_users():
    async with clients_lock:
        if clients:
            online_list = ", ".join(clients.values())
            msg = f"[Server] Online users: {online_list}"
            for ws in clients.keys():
                try:
                    await ws.send(msg)
                except:
                    pass

# --- Client handler ---
async def handler(websocket):
    try:
        username = await websocket.recv()
        async with clients_lock:
            clients[websocket] = username
        join_msg = f"{username} joined the chat."
        print(join_msg)
        await broadcast(join_msg)

        async for message in websocket:
            print(f"{username}: {message}")
            await broadcast(f"{username}: {message}", exclude=websocket)

    except websockets.ConnectionClosed:
        pass
    finally:
        async with clients_lock:
            if websocket in clients:
                left_name = clients.pop(websocket)
                leave_msg = f"{left_name} left the chat."
                print(leave_msg)
                await broadcast(leave_msg)

# --- Server status every 10 min ---
async def server_status():
    while True:
        await asyncio.sleep(600)  # 10 min
        uptime = int(time.time() - start_time)
        h, m = divmod(uptime // 60, 60)
        s = uptime % 60
        msg = f"[Server] Connected | {SERVER_LOCATION} | Uptime: {h}h {m}m {s}s | Ping: 0 ms"
        print(msg)
        await broadcast(msg)

# --- Main ---
async def main():
    server = await websockets.serve(handler, "0.0.0.0", PORT)
    print(f"✅ PulseChat WebSocket server running on port {PORT}")
    asyncio.create_task(server_status())
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
