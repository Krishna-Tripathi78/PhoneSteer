import asyncio
import websockets
import json
import uuid
import time
import http.server
import socketserver
import threading
import os

# Store connected clients
connected = set()
# Store active sessions with their access codes
active_sessions = {}

async def message_handler(websocket):
    # Register client
    client_id = str(uuid.uuid4())[:8]
    connected.add(websocket)
    print(f"Client connected: {client_id}. Total clients: {len(connected)}")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                print(f"Received: {data}")
                
                # Handle authentication
                if data.get('type') == 'auth':
                    access_code = data.get('code')
                    if access_code in active_sessions:
                        # Register this client as the phone for this session
                        active_sessions[access_code]['phone'] = websocket
                        
                        # Send authentication success
                        await websocket.send(json.dumps({
                            'type': 'auth_response',
                            'status': 'success'
                        }))
                        print(f"Client {client_id} authenticated with code {access_code}")
                    else:
                        # Send authentication failure
                        await websocket.send(json.dumps({
                            'type': 'auth_response',
                            'status': 'failure',
                            'message': 'Invalid access code'
                        }))
                        print(f"Client {client_id} failed authentication with code {access_code}")
                        continue
                
                # Handle desktop registration
                if data.get('type') == 'register_desktop':
                    # Generate new access code
                    access_code = str(uuid.uuid4())[:6].upper()
                    active_sessions[access_code] = {
                        'desktop': websocket,
                        'created_at': time.time(),
                        'phone': None
                    }
                    # Send access code to desktop
                    await websocket.send(json.dumps({
                        'type': 'access_code',
                        'code': access_code
                    }))
                    print(f"Desktop {client_id} registered with code {access_code}")
                
                # Forward control messages to desktop if authenticated
                if data.get('type') in ['sensor', 'keyboard', 'mouse', 'touchpad']:
                    # Find the session this client belongs to
                    for code, session in active_sessions.items():
                        if session.get('phone') == websocket and session.get('desktop'):
                            # Forward message to desktop
                            await session['desktop'].send(message)
                            break
            except json.JSONDecodeError:
                print(f"Invalid JSON received: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client {client_id} connection closed")
    finally:
        # Unregister client
        connected.remove(websocket)
        # Remove from active sessions
        for code, session in list(active_sessions.items()):
            if session.get('desktop') == websocket or session.get('phone') == websocket:
                del active_sessions[code]
                print(f"Session {code} removed")
        print(f"Client {client_id} disconnected. Total clients: {len(connected)}")

# Clean up expired sessions
async def cleanup_sessions():
    while True:
        current_time = time.time()
        for code, session in list(active_sessions.items()):
            # Remove sessions older than 10 minutes
            if current_time - session['created_at'] > 600:
                del active_sessions[code]
                print(f"Session {code} expired")
        await asyncio.sleep(60)  # Check every minute

class HttpHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def start_http_server():
    PORT = 8000
    with socketserver.TCPServer(("", PORT), HttpHandler) as httpd:
        print(f"HTTP Server running at http://localhost:{PORT}")
        httpd.serve_forever()

async def main():
    # Start the cleanup task
    asyncio.create_task(cleanup_sessions())
    
    # Start the HTTP server in a separate thread
    http_thread = threading.Thread(target=start_http_server, daemon=True)
    http_thread.start()
    
    # Start the WebSocket server
    async with websockets.serve(message_handler, "0.0.0.0", 8080):
        print("WebSocket server started on ws://0.0.0.0:8080")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(main())