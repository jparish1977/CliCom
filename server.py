import asyncio
from aiohttp import web

clients = {}  # {websocket: username}

async def handle_ws(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Wait for the client to introduce itself
    join_msg = await ws.receive()
    if join_msg.type == web.WSMsgType.TEXT and join_msg.data.startswith("JOIN:"):
        username = join_msg.data.split(":", 1)[1]
    else:
        await ws.close()
        return ws

    clients[ws] = username
    print(f"[+] {username} joined ({len(clients)} online)")

    # Notify everyone
    await broadcast(f"[SERVER] {username} joined the chat! ({len(clients)} online)")
    await send_user_list()

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                if msg.data.startswith("MSG:"):
                    text = msg.data.split(":", 1)[1]
                    await broadcast(f"{username}: {text}", exclude=ws)
            elif msg.type == web.WSMsgType.ERROR:
                print(f"Error: {ws.exception()}")
    finally:
        if ws in clients:
            del clients[ws]
            print(f"[-] {username} left ({len(clients)} online)")
            await broadcast(f"[SERVER] {username} left the chat. ({len(clients)} online)")
            await send_user_list()

    return ws

async def broadcast(message, exclude=None):
    for client in list(clients.keys()):
        if client.closed:
            clients.pop(client, None)
        elif client != exclude:
            await client.send_str(message)

async def send_user_list():
    users = ", ".join(clients.values()) or "No one"
    await broadcast(f"[USERS] Online: {users}")

async def index(request):
    return web.Response(text="Clicom Chat Server is running!", content_type="text/plain")

app = web.Application()
app.router.add_get("/", index)
app.router.add_get("/ws", handle_ws)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8080)
