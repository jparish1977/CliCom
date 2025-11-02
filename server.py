import asyncio
from aiohttp import web

clients = set()

async def handle_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    clients.add(ws)
    print(f"[+] Client connected ({len(clients)} online)")

    # Notify others that someone joined
    for client in clients:
        if client is not ws:
            await client.send_str(f"[Server] Someone joined ({len(clients)} online)")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # Broadcast to everyone else
                for client in clients:
                    if client is not ws:
                        await client.send_str(msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
    finally:
        clients.remove(ws)
        print(f"[-] Client disconnected ({len(clients)} online)")
        for client in clients:
            await client.send_str(f"[Server] Someone left ({len(clients)} online)")

    return ws

async def index(request):
    return web.Response(text="Clicom server is live", content_type="text/plain")

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", handle_ws)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
