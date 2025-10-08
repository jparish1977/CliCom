import asyncio
import websockets
import time
import os
from aiohttp import web

# --- Configuration ---
PORT = int(os.getenv("PORT", 8080))        # WebSocket server port
HEALTH_PORT = PORT + 1                     # HTTP health check port
SERVER_LOCATION = "MI, USA 🇺🇸"
PING_INTERVAL = 30                          # seconds between ping checks

clients = {}  # websocket -> username
start_time = time.time()

# --- Broadcast helper ---
async def broadcast(message, exclude=None):
    """Send a message to all connected clients, excluding 'exclude' if specified."""
    disconnected = []
    for ws in list(clients.keys()):
        if ws != exclude:
            try:
                await ws.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(ws)
            except Exception as e:
                print(f"[Broadcast] Error sending to {clients.get(ws)}: {e}")

    # Remove disconnected clients
    for ws in disconnected:
        left_name = clients.pop(ws, None)
        if left_name:
            leave_msg = f"{left_name} left the chat."
            print(leave_msg)
            await broadcast(leave_msg)

# --- Client handler ---
async def handler(websocket, path):
    try:
        username = await websocket.recv()
        clients[websocket] = username
        join_msg = f"{username} joined the chat."
        print(join_msg)
        await broadcast(join_msg)

        async for message in websocket:
            print(f"{username}: {message}")
            await broadcast(f"{username}: {message}", exclude=websocket)

    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        print(f"[Handler] Error for {clients.get(websocket)}: {e}")
    finally:
        if websocket in clients:
            left_name = clients.pop(websocket)
            leave_msg = f"{left_name} left the chat."
            print(leave_msg)
            await broadcast(leave_msg)

# --- Server status task ---
async def server_status():
    while True:
        await asyncio.sleep(600)  # every 10 minutes
        uptime = int(time.time() - start_time)
        h, m = divmod(uptime // 60, 60)
        s = uptime % 60
        msg = f"[Server] Connected | {SERVER_LOCATION} | Uptime: {h}h {m}m {s}s | Ping: 0 ms"
        print(msg)
        await broadcast(msg)

# --- Ping task to detect dead clients ---
async def ping_clients():
    while True:
        await asyncio.sleep(PING_INTERVAL)
        disconnected = []
        for ws in list(clients.keys()):
            try:
                pong_waiter = await ws.ping()
                await asyncio.wait_for(pong_waiter, timeout=10)
            except:
                disconnected.append(ws)
        for ws in disconnected:
            left_name = clients.pop(ws, None)
            if left_name:
                leave_msg = f"{left_name} left the chat (ping timeout)."
                print(leave_msg)
                await broadcast(leave_msg)

# --- Health check endpoint for Render ---
async def health(request):
    return web.Response(text="OK")

# --- Main server ---
async def main():
    # Start WebSocket server on /ws
    ws_server = await websockets.serve(handler, "0.0.0.0", PORT, ping_interval=None)
    print(f"✅ PulseChat WebSocket server running on port {PORT}")

    # Start background tasks
    asyncio.create_task(server_status())
    asyncio.create_task(ping_clients())

    # Start HTTP server for health checks
    app = web.Application()
    app.router.add_get("/health", health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", HEALTH_PORT)
    await site.start()
    print(f"✅ Health check endpoint running on port {HEALTH_PORT}")

    await ws_server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
