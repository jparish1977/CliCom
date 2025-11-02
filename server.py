# server.py
# Signaling server for Clicom (aiohttp WebSocket)
# Deploy this to Render (or any host). Exposes /ws for WebSocket signaling.

import json
import argparse
from aiohttp import web, WSMsgType

# Map username -> (websocket, color)
USERS = {}

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None
    color = None

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception:
                    await ws.send_json({'type': 'error', 'message': 'invalid_json'})
                    continue

                t = data.get('type')

                # Registration: name + color
                if t == 'register':
                    username = data.get('name')
                    color = data.get('color', '92')
                    if not username:
                        await ws.send_json({'type': 'error', 'message': 'no_name'})
                        continue
                    if username in USERS:
                        # name already taken
                        await ws.send_json({'type': 'error', 'message': 'name_taken'})
                        continue
                    USERS[username] = (ws, color)
                    print(f"[+] {username} connected (color={color})")
                    # Broadcast updated userlist + delta
                    await broadcast_userlist(delta=True, join=username)

                # Request current list
                elif t == 'list':
                    await ws.send_json({'type': 'userlist', 'users': list_users(), 'count': len(USERS)})

                # Relay offer/answer/candidate/leave to the target user
                elif t in ('offer', 'answer', 'candidate', 'leave'):
                    target = data.get('target')
                    if not target:
                        await ws.send_json({'type': 'error', 'message': 'no_target'})
                        continue
                    if target in USERS:
                        target_ws, _ = USERS[target]
                        await target_ws.send_json(data)
                    else:
                        await ws.send_json({'type': 'error', 'message': 'target_offline'})

                else:
                    await ws.send_json({'type': 'error', 'message': 'unknown_type'})
            elif msg.type == WSMsgType.ERROR:
                print('ws connection closed with exception %s' % ws.exception())
    finally:
        # cleanup on disconnect
        if username and username in USERS:
            del USERS[username]
            print(f"[-] {username} disconnected")
            await broadcast_userlist(delta=True, leave=username)

    return ws

def list_users():
    """Return list of user dicts with name+color."""
    return [{'name': name, 'color': color} for name, (_, color) in USERS.items()]

async def broadcast_userlist(delta=False, join=None, leave=None):
    users = list_users()
    payload = {'type': 'userlist', 'users': users, 'count': len(users)}
    if delta:
        if join:
            payload['delta'] = {'change': +1, 'user': join}
        elif leave:
            payload['delta'] = {'change': -1, 'user': leave}
    # send to everyone
    for name, (ws, _) in list(USERS.items()):
        try:
            await ws.send_json(payload)
        except Exception:
            pass

app = web.Application()
app.router.add_get('/ws', websocket_handler)
app.router.add_get('/', lambda r: web.Response(text="Clicom signaling server is live.", content_type='text/plain'))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    print(f"Starting signaling server on {args.host}:{args.port}")
    web.run_app(app, host=args.host, port=args.port)
