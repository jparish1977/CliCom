import asyncio
import websockets
import time
import os

# Use Render's PORT or fallback to 8080 locally
PORT = int(os.getenv("PORT", 8080))
clients = {}  # websocket -> username
start_time = time.time()
SERVER_LOCATION = "MI, USA "

# --- Broadcast helper ---
async def broadcast(message, exclude=None):
    for ws in list(clients.keys()):
        if ws != exclude:
            try:
                await ws.send(message)
            except:
                clients.pop(ws, None)

# --- Client handler ---
async def handler(websocket):
    try:
        username = await websocket.recv()
        clients[websocket] = username
        join_msg = f"{username} joined the chat."
        print(join_msg)
        await broadcast(join_msg)

        async for message in websocket:
            print(f"{username}: {message}")
            await broadcast(f"{username}: {message}", exclude=websocket)

    except:
        pass
    finally:
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
