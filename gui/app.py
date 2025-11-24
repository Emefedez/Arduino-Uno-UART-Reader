from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from serial_handler import SerialHandler
import threading
import time
import webbrowser
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global Serial Handler
serial_handler = SerialHandler()

# --- Serial Callbacks ---
def on_serial_message(origin, data):
    socketio.emit('new_message', {'origin': origin, 'data': data, 'timestamp': time.strftime("%H:%M:%S.%f")[:-3]})

def on_serial_status(status):
    socketio.emit('status_update', status)

def on_serial_log(msg):
    socketio.emit('log_message', {'data': msg})

serial_handler.on_message = on_serial_message
serial_handler.on_status = on_serial_status
serial_handler.on_log = on_serial_log

# --- Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/ports')
def get_ports():
    return {'ports': serial_handler.get_ports()}

@app.route('/api/connect', methods=['POST'])
def connect():
    data = request.json
    port = data.get('port')
    if serial_handler.connect(port):
        return {'status': 'connected'}
    return {'status': 'error'}, 400

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    serial_handler.disconnect()
    return {'status': 'disconnected'}

@app.route('/api/send', methods=['POST'])
def send():
    data = request.json
    cmd = data.get('cmd')
    serial_handler.send(cmd)
    return {'status': 'sent'}

@app.route('/api/config', methods=['POST'])
def config():
    data = request.json
    d_pins = data.get('d_pins', [])
    a_pins = data.get('a_pins', [])
    serial_handler.send_config(d_pins, a_pins)
    return {'status': 'configured'}

@app.route('/api/test_bridge', methods=['POST'])
def test_bridge():
    # Send PING and wait for response (handled asynchronously by frontend via socket)
    # But we can just send the command here.
    if serial_handler.serial_port and serial_handler.serial_port.is_open:
        serial_handler.send("PING")
        return {'status': 'sent'}
    return {'status': 'error', 'message': 'Not connected'}, 400

if __name__ == '__main__':
    # Kill any process on port 5000
    try:
        os.system("lsof -ti :5000 | xargs kill -9")
    except:
        pass
        
    # Open browser automatically
    threading.Timer(1.5, lambda: webbrowser.open("http://localhost:5000")).start()
    socketio.run(app, port=5000, debug=False)
