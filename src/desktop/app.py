import json
import threading
import tkinter as tk
from tkinter import ttk
import pyautogui
import websocket
import qrcode
import socket
import io
from PIL import Image, ImageTk

class CTRLitDesktop:
    def __init__(self, root):
        self.root = root
        self.root.title("CTRLit")
        self.root.geometry("500x600")
        self.root.configure(bg="#2c3e50")
        
        self.status_var = tk.StringVar(value="Disconnected")
        self.server_url = tk.StringVar(value="localhost")
        self.server_port = tk.IntVar(value=8080)
        self.conn = None
        self.is_connected = False
        self.access_code = ""
        self.qr_image = None
        self.web_url = ""
        
        self.setup_ui()
        
    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Server connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Server Connection", padding="10")
        conn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(conn_frame, text="Server URL:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(conn_frame, textvariable=self.server_url, width=20).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(conn_frame, text="Server Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(conn_frame, textvariable=self.server_port, width=20).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Connect", command=self.connect).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Disconnect", command=self.disconnect).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(main_frame, padding="5")
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var)
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # QR Code frame
        self.qr_frame = ttk.LabelFrame(main_frame, text="QR Code", padding="10")
        self.qr_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.code_label = ttk.Label(self.qr_frame, text="Access Code: Not Connected")
        self.code_label.pack(pady=5)
        
        self.url_label = ttk.Label(self.qr_frame, text="URL: Not Connected", wraplength=350)
        self.url_label.pack(pady=5)
        
        self.qr_label = ttk.Label(self.qr_frame)
        self.qr_label.pack(pady=10, expand=True)
        
        ttk.Button(self.qr_frame, text="Generate New Code", command=self.generate_new_code).pack(pady=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = tk.Text(log_frame, height=8, width=50)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
    def log(self, message):
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        
    def connect(self):
        if self.is_connected:
            return
            
        try:
            ws_url = f"ws://{self.server_url.get()}:{self.server_port.get()}"
            self.log(f"Connecting to {ws_url}")
            
            def on_message(ws, message):
                self.handle_message(message)
                
            def on_error(ws, error):
                self.log(f"Error: {error}")
                self.status_var.set("Connection Failed")
                
            def on_close(ws, close_status_code, close_msg):
                self.log("Connection closed")
                self.is_connected = False
                self.status_var.set("Disconnected")
                
            def on_open(ws):
                self.log("Connection established")
                self.is_connected = True
                self.status_var.set("Connected")
                
                # Register as desktop and request access code
                ws.send(json.dumps({
                    'type': 'register_desktop'
                }))
            
            self.conn = websocket.WebSocketApp(ws_url,
                                  on_open=on_open,
                                  on_message=on_message,
                                  on_error=on_error,
                                  on_close=on_close)
                                  
            def run_websocket():
                self.conn.run_forever()
                
            threading.Thread(target=run_websocket, daemon=True).start()
            
        except Exception as e:
            self.log(f"Connection error: {str(e)}")
            self.status_var.set("Connection Failed")
            
    def disconnect(self):
        if not self.is_connected:
            return
            
        try:
            self.conn.close()
            self.is_connected = False
            self.status_var.set("Disconnected")
            self.log("Disconnected from server")
            self.access_code = ""
            self.web_url = ""
            self.code_label.config(text="Access Code: Not Connected")
            self.url_label.config(text="URL: Not Connected")
            self.qr_label.config(image="")
        except Exception as e:
            self.log(f"Disconnect error: {str(e)}")
            
    def generate_new_code(self):
        if self.is_connected:
            # Request new access code
            self.conn.send(json.dumps({
                'type': 'register_desktop'
            }))
            self.log("Requesting new access code")
    
    def generate_qr_code(self, code):
        try:
            # Get IP address
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            
            # Try to get a better IP address that works across networks
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                better_ip = s.getsockname()[0]
                s.close()
                self.log(f"Using network IP: {better_ip}")
                local_ip = better_ip
            except:
                self.log(f"Using hostname IP: {local_ip}")
            
            # Create URL for web controller
            self.web_url = f"http://{local_ip}:8000/index.html?server={local_ip}&port={self.server_port.get()}&code={code}"
            self.log(f"Web URL: {self.web_url}")
            
            # Create QR code with web URL
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(self.web_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to PhotoImage
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            image = Image.open(io.BytesIO(img_byte_arr))
            image = image.resize((250, 250), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            
            # Update QR code display
            self.qr_image = photo  # Keep a reference
            self.qr_label.config(image=photo)
            self.code_label.config(text=f"Access Code: {code}")
            self.url_label.config(text=f"URL: {self.web_url}")
            
            self.log(f"QR code generated for access code: {code}")
        except Exception as e:
            self.log(f"Error generating QR code: {str(e)}")
            
    def handle_message(self, message_body):
        try:
            data = json.loads(message_body)
            msg_type = data.get('type')
            
            if msg_type == 'access_code':
                code = data.get('code')
                self.access_code = code
                self.generate_qr_code(code)
                self.log(f"Received access code: {code}")
            
            elif msg_type == 'sensor':
                self.log(f"Sensor: x={data.get('x'):.2f}, y={data.get('y'):.2f}, z={data.get('z'):.2f}")
                
            elif msg_type == 'keyboard':
                key = data.get('key')
                self.log(f"Keyboard: {key}")
                if key == 'SPACE':
                    pyautogui.press('space')
                elif key == 'ENTER':
                    pyautogui.press('enter')
                elif key == 'BACKSPACE':
                    pyautogui.press('backspace')
                elif key == 'ESC':
                    pyautogui.press('escape')
                else:
                    pyautogui.press(key.lower())
                    
            elif msg_type == 'mouse':
                action = data.get('action')
                self.log(f"Mouse: {action}")
                if action == 'left_click':
                    pyautogui.click()
                elif action == 'right_click':
                    pyautogui.rightClick()
                    
            elif msg_type == 'touchpad':
                dx = data.get('dx', 0)
                dy = data.get('dy', 0)
                self.log(f"Touchpad: dx={dx:.2f}, dy={dy:.2f}")
                
                try:
                    # Use pyautogui.move for relative movement
                    pyautogui.move(dx, dy)
                except Exception as e:
                    self.log(f"Mouse movement error: {str(e)}")
                
        except Exception as e:
            self.log(f"Error handling message: {str(e)}")

if __name__ == "__main__":
    pyautogui.FAILSAFE = False
    root = tk.Tk()
    app = CTRLitDesktop(root)
    root.mainloop()