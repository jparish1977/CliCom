import asyncio
import json
import argparse
from aiohttp import web, WSMsgType

USERS = {}  # username -> (ws, color)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None
    color = None

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)
                t = data.get('type')

                if t == 'register':
                    username = data.get('name')
                    color = data.get('color', '92')
                    if not username:
                        await ws.send_json({'type': 'error', 'message': 'no name'})
                        continue
                    if username in USERS:
                        await ws.send_json({'type': 'error', 'message': 'name_taken'})
                        continue
                    USERS[username] = (ws, color)
                    print(f"[+] {username} registered with color {color}")
                    await broadcast_userlist(delta=True, join=username)

                elif t == 'list':
                    await ws.send_json({'type': 'userlist', 'users': list_users(), 'count': len(USERS)})

                elif t in ('offer', 'answer', 'candidate', 'leave'):
                    target = data.get('target')
                    if target in USERS:
                        target_ws, _ = USERS[target]
                        await target_ws.send_json(data)
                    else:
                        await ws.send_json({'type': 'error', 'message': 'target_offline'})
                else:
                    await ws.send_json({'type': 'error', 'message': 'unknown_type'})

            elif msg.type == WSMsgType.ERROR:
                print(f"ws connection closed with exception {ws.exception()}")
    finally:
        if username and username in USERS:
            del USERS[username]
            print(f"[-] {username} disconnected")
            await broadcast_userlist(delta=True, leave=username)

    return ws

async def broadcast_userlist(delta=False, join=None, leave=None):
    users = list_users()
    payload = {'type': 'userlist', 'users': users, 'count': len(users)}
    if delta:
        if join:
            payload['delta'] = {'change': +1, 'user': join}
        elif leave:
            payload['delta'] = {'change': -1, 'user': leave}
    for (u, (ws, _)) in list(USERS.items()):
        try:
            await ws.send_json(payload)
        except:
            pass

def list_users():
    return [{'name': u, 'color': c} for u, (ws, c) in USERS.items()]

app = web.Application()
app.router.add_get('/ws', websocket_handler)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    web.run_app(app, host=args.host, port=args.port)
