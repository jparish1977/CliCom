import os
import asyncio
import websockets
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

start_time = time.time()  # Record when the server starts
clients = set()           # Set to hold connected websocket clients

async def chat_handler(websocket, path):
    try:
        # Receive the first message as the username
        username = await websocket.recv()
    except Exception as e:
        return

    clients.add(websocket)
    await safe_broadcast(f"{username} joined the chat.")

    try:
        async for message in websocket:
            # Broadcast the message to all connected clients except the sender
            await safe_broadcast(f"{username}: {message}", sender=websocket)
    except Exception as e:
        print(f"Exception in chat_handler: {e}")
    finally:
        if websocket in clients:
            clients.remove(websocket)
        await safe_broadcast(f"{username} left the chat.")


async def safe_broadcast(message, sender=None):
    """Async broadcast helper to avoid closed-loop issues."""
    dead_clients = []
    for client in list(clients):
        if client != sender:
            try:
                await client.send(message)
            except:
                dead_clients.append(client)
    for c in dead_clients:
        clients.discard(c)


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        uptime = time.time() - start_time
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
        html = f"""<html>
  <head><title>Chat Server Status</title></head>
  <body style='font-family: sans-serif; text-align: center; margin-top: 50px'>
    <h1>Chat Server Status</h1>
    <p><b>Uptime:</b> {uptime_str}</p>
    <p><b>Connected Clients:</b> {len(clients)}</p>
  </body>
</html>"""
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())


def start_http_server():
    port = int(os.getenv("STATUS_PORT", 8080))
    httpd = HTTPServer(("0.0.0.0", port), StatusHandler)
    print(f"[HTTP] Status page running on port {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    # Start the HTTP status server in a separate thread
    threading.Thread(target=start_http_server, daemon=True).start()

    # Start the WebSocket chat server on port 5000 (or use WS_PORT env var)
    ws_port = int(os.getenv("WS_PORT", 5000))
    start_server = websockets.serve(chat_handler, "0.0.0.0", ws_port)
    print(f"[WebSocket] Chat server running on port {ws_port}")

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down.")
