import socket
import threading
import os
import sys
import time
from datetime import datetime

class ClicomServer:
    def __init__(self, host='0.0.0.0', port=None):
        # For Render deployment - reads PORT from environment
        if port is None:
            port = int(os.environ.get('PORT', 5555))
        
        self.host = host
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}  # {username: socket}
        self.start_time = time.time()  # Server start time
        
    def start(self):
        """Start the server"""
        try:
            self.server.bind((self.host, self.port))
            self.server.listen(5)
            print(f"[SERVER] Clicom started on {self.host}:{self.port}")
            print(f"[SERVER] Start time: {datetime.now()}")
            sys.stdout.flush()
            
            while True:
                try:
                    client_socket, addr = self.server.accept()
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                    thread.daemon = True
                    thread.start()
                except Exception as e:
                    print(f"[ERROR] Accept error: {e}")
                    sys.stdout.flush()
        except KeyboardInterrupt:
            print("\n[SERVER] Shutting down...")
            self.server.close()
        except Exception as e:
            print(f"[FATAL] {e}")
            sys.stdout.flush()
    
    def get_uptime(self):
        """Get server uptime"""
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        return f"{hours}h {minutes}m {seconds}s"
    
    def handle_client(self, client_socket, addr):
        """Handle individual client connection"""
        username = None
        
        try:
            # Receive username
            client_socket.send(b"Welcome to Clicom! Enter your username: ")
            username = client_socket.recv(1024).decode('utf-8').strip()
            
            if not username or len(username) < 1:
                client_socket.send(b"INVALID")
                client_socket.close()
                return
            
            # Check if username already exists
            if username in self.clients:
                client_socket.send(b"TAKEN")
                client_socket.close()
                return
            
            self.clients[username] = client_socket
            client_socket.send(b"OK")
            
            # Notify others - JOIN notification
            join_msg = f"\n[📍 {username} joined the chat! Now {len(self.clients)} online]\n"
            self.broadcast(join_msg, exclude=username)
            
            client_socket.send(f"\n[✓ Welcome {username}! Type /help for commands.]\n".encode('utf-8'))
            print(f"[JOIN] {username} connected from {addr}")
            sys.stdout.flush()
            
            while True:
                message = client_socket.recv(1024).decode('utf-8').strip()
                
                if not message:
                    continue
                
                if message.startswith('/'):
                    self.handle_command(username, message, client_socket)
                elif message == "🔤":
                    # Typing indicator
                    self.broadcast(f"\n[✍ {username} is typing...]\n", exclude=username)
                else:
                    # Regular message - server just broadcasts
                    self.broadcast(f"\n{username}: {message}\n")
        
        except Exception as e:
            print(f"[ERROR] Client error: {e}")
            sys.stdout.flush()
        
        finally:
            if username and username in self.clients:
                del self.clients[username]
                # LEAVE notification
                leave_msg = f"\n[📍 {username} left the chat! Now {len(self.clients)} online]\n"
                self.broadcast(leave_msg)
                print(f"[LEAVE] {username} disconnected")
                sys.stdout.flush()
    
    def handle_command(self, username, command, client_socket):
        """Handle special commands"""
        parts = command.lower().split()
        cmd = parts[0]
        
        if cmd == '/list':
            users_list = ", ".join([f"{user}" for user in self.clients.keys()])
            response = f"\n[👥 ONLINE USERS ({len(self.clients)})]\n{users_list}\n"
            client_socket.send(response.encode('utf-8'))
        
        elif cmd == '/uptime':
            uptime = self.get_uptime()
            response = f"\n[⏱️  SERVER UPTIME]\n{uptime}\nServer Location: Michigan, USA\n"
            client_socket.send(response.encode('utf-8'))
        
        elif cmd == '/help':
            help_text = """
[❓ AVAILABLE COMMANDS]
  /list       - Show all online users
  /stats      - Show your message statistics
  /users      - Show all users and their stats (online/offline)
  /uptime     - Show server uptime and location
  /clear      - Clear your statistics
  /quit       - Leave the chat
  /help       - Show this help message
"""
            client_socket.send(help_text.encode('utf-8'))
        
        elif cmd == '/quit':
            client_socket.send("\n[Goodbye!]\n".encode('utf-8'))
            client_socket.close()
        
        else:
            client_socket.send("\n[Unknown command. Type /help]\n".encode('utf-8'))
    
    def broadcast(self, message, exclude=None):
        """Send message to all connected clients"""
        for username, client_socket in list(self.clients.items()):
            if exclude is None or username != exclude:
                try:
                    client_socket.send(message.encode('utf-8'))
                except:
                    pass


if __name__ == "__main__":
    server = ClicomServer()
    server.start()
