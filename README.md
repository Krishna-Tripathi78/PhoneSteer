# PhoneSteer

Control your desktop with your phone using QR code authentication - no app installation required!

## Overview

PhoneSteer is a simple project that lets you control your computer's mouse and keyboard using your phone's web browser. No need to install any apps on your phone - just scan a QR code and you're ready to go!

## Features

- Control mouse movement using your phone's touchscreen
- Click, right-click, and type using on-screen buttons
- Secure connection with unique access codes
- Works on any device with a web browser
- No app installation required

## How It Works

1. The desktop app generates a unique access code and QR code
2. Scan the QR code with your phone's camera
3. Your phone's browser opens the web controller
4. Move your finger on the touchpad area to control the mouse
5. Use the buttons to click or type

## Requirements

### Desktop
- Python 3.6+
- Libraries: websocket-client, pyautogui, qrcode, pillow

### Phone
- Any modern web browser
- Camera for scanning QR codes (optional)

## Installation

1. Clone this repository:
```
git clone https://github.com/Krishna-Tripathi78/PhoneSteer.git
cd PhoneSteer
```

2. Install desktop requirements:
```
cd src/desktop
pip install -r requirements.txt
```

3. Install server requirements:
```
cd ../server
pip install -r requirements.txt
```

## Usage

1. Start the server:
```
cd src/server
python server.py
```

2. Start the desktop app:
```
cd ../desktop
python app.py
```

3. In the desktop app:
   - Click "Connect"
   - A QR code will be generated

4. On your phone:
   - Scan the QR code with your camera app
   - OR visit the direct access URL and enter the access code manually
   - Use the touchpad to control your desktop

## Troubleshooting

- **Mouse not moving?** Try increasing the sensitivity slider
- **Can't connect?** Make sure your phone and computer are on the same network
- **QR code not working?** Try entering the access code manually at the direct access URL

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Created as a student project for learning WebSockets and Python GUI development
- Inspired by various remote control applications