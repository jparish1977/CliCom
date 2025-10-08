import socket
import threading
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- Config ---
CHAT_HOST = "0.0.0.0"
CHAT_PORT = 5000
HTTP_PORT = int(os.getenv("PORT", 8080))

# If you want to customize location text, change this:
SERVER_LOCATION = "MI, USA 🇺🇸"

clients = {}  # {conn: username}
start_time = time.time()

# --- Broadcast helper ---
def broadcast(message, sender=None):
    """Send a message to all connected clients except sender."""
    for client in list(clients.keys()):
        try:
            if client != sender:
                client.sendall(message.encode())
        except:
            clients.pop(client, None)

# --- Automatic server status every 10 min ---
def server_status_loop():
    while True:
        time.sleep(600)  # 600 seconds = 10 min
        uptime = time.time() - start_time
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        # Simulated ping: since server pings itself, ~0ms
        ping_ms = 0
        msg = f"[Server] Connected | {SERVER_LOCATION} | Uptime: {uptime_str} | Ping: {ping_ms} ms\n"
        print(msg.strip())
        broadcast(msg)

# --- Handle client ---
def handle_client(conn, addr):
    try:
        username = conn.recv(1024).decode().strip()
        if not username:
            username = f"User-{addr[1]}"
        clients[conn] = username

        print(f"[CONNECTED] {username} ({addr})")
        broadcast(f"{username} joined the chat.\n")

        while True:
            data = conn.recv(1024)
            if not data:
                break
            msg = data.decode().strip()
            print(f"{username}: {msg}")
            broadcast(f"{username}: {msg}\n", sender=conn)
    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        username = clients.pop(conn, "Unknown")
        print(f"[DISCONNECTED] {username} ({addr})")
        broadcast(f"{username} left the chat.\n")
        conn.close()

# --- Chat server thread ---
def start_chat_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((CHAT_HOST, CHAT_PORT))
    server.listen()
    print(f"[CHAT] Running on {CHAT_HOST}:{CHAT_PORT}")
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

# --- Web status page ---
class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        uptime = time.time() - start_time
        hours, rem = divmod(uptime, 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

        html = f"""
        <html>
        <head><title>Chat Server Status</title></head>
        <body style='font-family:sans-serif;text-align:center;margin-top:50px'>
        <h1>Chat Server (Render)</h1>
        <p><b>Location:</b> {SERVER_LOCATION}</p>
        <p><b>Uptime:</b> {uptime_str}</p>
        <p><b>Connected Clients:</b> {len(clients)}</p>
        <ul style='list-style:none'>
            {''.join(f"<li>{name}</li>" for name in clients.values())}
        </ul>
        <p><b>Chat Port:</b> {CHAT_PORT}</p>
        </body>
        </html>
        """
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

def start_http_server():
    httpd = HTTPServer(("0.0.0.0", HTTP_PORT), StatusHandler)
    print(f"[HTTP] Status page running on port {HTTP_PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    # Start server status loop
    threading.Thread(target=server_status_loop, daemon=True).start()

    # Start chat + HTTP server
    threading.Thread(target=start_chat_server, daemon=True).start()
    start_http_server()
