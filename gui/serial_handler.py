import serial
import threading
import time

class SerialHandler:
    def __init__(self):
        self.serial_port = None
        self.is_running = False
        self.thread = None
        
        # Callbacks
        self.on_message = None # func(origin, message)
        self.on_status = None  # func(status_dict)
        self.on_log = None     # func(text)
        
    def get_ports(self):
        from serial.tools import list_ports
        return [p.device for p in list_ports.comports()]
        
    def connect(self, port, baudrate=9600):
        try:
            self.serial_port = serial.Serial(port, baudrate, timeout=1)
            self.is_running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            if self.on_log: self.on_log(f"Connected to {port}")
            return True
        except Exception as e:
            if self.on_log: self.on_log(f"Error connecting: {e}")
            return False
            
    def disconnect(self):
        self.is_running = False
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
        if self.on_log: self.on_log("Disconnected")
            
    def send(self, data):
        if self.serial_port and self.serial_port.is_open:
            try:
                self.serial_port.write((data + '\n').encode('utf-8'))
                if self.on_message: self.on_message("PC", data)
            except Exception as e:
                if self.on_log: self.on_log(f"Send error: {e}")
                
    def send_config(self, digital_pins, analog_pins):
        # digital_pins: list of ints [2, 3]
        # analog_pins: list of ints [0]
        cmd = "CFG:"
        parts = []
        
        # Reset all first (optional, but good practice if we tracked state)
        # For now, we just send what we want to ENABLE. 
        # The firmware logic I wrote accumulates enables. 
        # Wait, my firmware logic sets monitorDigital[p] = (val == 1).
        # So I should probably send 0 for everything else? 
        # Or just rely on the user to uncheck things.
        # Let's send explicit 1s and 0s for everything to be safe.
        
        for i in range(14):
            val = 1 if i in digital_pins else 0
            parts.append(f"D{i}={val}")
            
        for i in range(6):
            val = 1 if i in analog_pins else 0
            parts.append(f"A{i}={val}")
            
        cmd += ",".join(parts)
        self.send(cmd)
        
    def _read_loop(self):
        while self.is_running and self.serial_port and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting:
                    line = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                    if not line: continue
                    
                    if line.startswith("STATUS:"):
                        self._parse_status(line)
                    elif line.startswith("<- "):
                        # Echo from Arduino (what it sent to device)
                        # Format in firmware: 
                        # Serial.print("<- "); Serial.print(TXData);
                        # This means the Arduino is reporting what it sent to the device.
                        # So Origin = Arduino (Bridge)
                        content = line[3:]
                        if self.on_message: self.on_message("Arduino -> Device", content)
                    else:
                        # Could be debug message or data from Device -> Arduino -> PC
                        if self.on_message: self.on_message("Device -> PC", line)
                        
            except Exception as e:
                if self.on_log: self.on_log(f"Read error: {e}")
                time.sleep(0.1)
                
    def _parse_status(self, line):
        # STATUS:D2:1,D3:0,A0:512
        try:
            content = line[7:]
            parts = content.split(',')
            status = {}
            for p in parts:
                if ':' in p:
                    k, v = p.split(':')
                    status[k] = int(v)
            if self.on_status: self.on_status(status)
        except:
            pass
