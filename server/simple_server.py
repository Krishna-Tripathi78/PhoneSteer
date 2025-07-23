import asyncio
import websockets
import json
import uuid
import time

connected = set()
active_sessions = {}

async def message_handler(websocket):
    client_id = str(uuid.uuid4())
    connected.add(websocket)
    print(f"Client connected: {client_id}. Total clients: {len(connected)}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"Received: {data}")
                
               
                if data.get('type') == 'auth':
                    access_code = data.get('code')
                    if access_code in active_sessions:
                        active_sessions[access_code]['phone'] = websocket
                        await websocket.send(json.dumps({
                            'type': 'auth_response',
                            'status': 'success'
                        }))
                        print(f"Client {client_id} authenticated with code {access_code}")
                        print(f"Phone client registered for session {access_code}")
                    else:
                        await websocket.send(json.dumps({
                            'type': 'auth_response',
                            'status': 'failure',
                            'message': 'Invalid access code'
                        }))
                        print(f"Client {client_id} failed authentication with code {access_code}")
                        continue
                if data.get('type') == 'register_desktop':
                    access_code = str(uuid.uuid4())[:6].upper()
                    active_sessions[access_code] = {
                        'desktop': websocket,
                        'created_at': time.time(),
                        'phone': None
                    }
                    await websocket.send(json.dumps({
                        'type': 'access_code',
                        'code': access_code
                    }))
                    print(f"Desktop {client_id} registered with code {access_code}")
                if data.get('type') in ['sensor', 'keyboard', 'mouse', 'touchpad']:
                    found = False
                    for code, session in active_sessions.items():
                        if session.get('phone') == websocket and session.get('desktop'):
                            try:
                                await session['desktop'].send(message)
                                print(f"Forwarded {data.get('type')} message to desktop")
                                found = True
                                break
                            except Exception as e:
                                print(f"Error forwarding message: {e}")
                    
                    if not found:
                        print(f"Warning: Could not find desktop for client {client_id}")
                        print(f"Active sessions: {active_sessions}")
                        for code, session in active_sessions.items():
                            if session.get('phone') == websocket:
                                print(f"Found phone in session {code} but desktop is {session.get('desktop')}")
                            if session.get('desktop') and session.get('desktop') == websocket:
                                print(f"This client is registered as a desktop in session {code}")
                        await websocket.send(json.dumps({
                            'type': 'error',
                            'message': 'Not connected to a desktop'
                        }))
            except json.JSONDecodeError:
                print(f"Invalid JSON received: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} connection closed")
    finally:
        connected.remove(websocket)
        for code, session in list(active_sessions.items()):
            if session.get('desktop') == websocket or session.get('phone') == websocket:
                del active_sessions[code]
                print(f"Session {code} removed")
        print(f"Client {client_id} disconnected. Total clients: {len(connected)}")
async def cleanup_sessions():
    while True:
        current_time = time.time()
        for code, session in list(active_sessions.items()):

            if current_time - session['created_at'] > 600:
                del active_sessions[code]
                print(f"Session {code} expired")
        await asyncio.sleep(60)  

async def main():

    asyncio.create_task(cleanup_sessions())

    async with websockets.serve(message_handler, "0.0.0.0", 8080):
        print("WebSocket server started on ws://0.0.0.0:8080")
        await asyncio.Future()  

if __name__ == "__main__":
    asyncio.run(main())