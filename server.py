import json
from aiohttp import web

# Store active WebRTC clients
clients = set()

async def index(request):
    return web.Response(text="Clicom signaling server is live.", content_type="text/plain")

async def offer(request):
    params = await request.json()
    offer = params["offer"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    clients.add(ws)
    print(f"[+] Client connected ({len(clients)} total)")

    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            data = msg.data
            for client in clients:
                if client != ws:
                    await client.send_str(data)
        elif msg.type == web.WSMsgType.ERROR:
            print(f"WebSocket error: {ws.exception()}")

    clients.remove(ws)
    print(f"[-] Client disconnected ({len(clients)} total)")
    return ws

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", offer)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
