import asyncio
from aiohttp import web

clients = set()

async def index(request):
    return web.Response(text="Clicom chat server running!", content_type="text/plain")

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    clients.add(ws)
    print(f"[+] New client connected ({len(clients)} online)")

    # Announce new user to everyone
    for client in clients:
        if client != ws:
            await client.send_str(f"[Server] A user joined. ({len(clients)} online)")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # Broadcast to all other clients
                for client in clients:
                    if client != ws:
                        await client.send_str(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    finally:
        clients.remove(ws)
        print(f"[-] Client disconnected ({len(clients)} online)")
        for client in clients:
            await client.send_str(f"[Server] A user left. ({len(clients)} online)")

    return ws

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
