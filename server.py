import os
import asyncio
import time
from aiohttp import web

start_time = time.time()  # Record when the server starts
clients = set()  # Set to hold connected websocket clients

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    clients.add(ws)
    async for msg in ws:
        if msg.type == web.WSMsgType.TEXT:
            text = msg.data.strip()
            # Broadcast the received message to all other connected clients
            for client in list(clients):
                if client != ws and not client.closed:
                    try:
                        await client.send_str(text)
                    except Exception as e:
                        print(f"Error sending to client: {e}")
        elif msg.type == web.WSMsgType.ERROR:
            print(f"WebSocket connection closed with exception: {ws.exception()}")
    clients.remove(ws)
    return ws

async def status_handler(request):
    uptime = time.time() - start_time
    hours, rem = divmod(uptime, 3600)
    minutes, seconds = divmod(rem, 60)
    uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    html = f"""
    <html>
      <head><title>Chat Server Status</title></head>
      <body style='font-family:sans-serif; text-align:center; margin-top:50px'>
        <h1>Chat Server Status</h1>
        <p><b>Uptime:</b> {uptime_str}</p>
        <p><b>Connected Clients:</b> {len(clients)}</p>
      </body>
    </html>
    """
    return web.Response(text=html, content_type="text/html")

app = web.Application()
app.router.add_get("/", status_handler)
app.router.add_get("/ws", websocket_handler)

if __name__ == "__main__":
    HTTP_PORT = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=HTTP_PORT)
