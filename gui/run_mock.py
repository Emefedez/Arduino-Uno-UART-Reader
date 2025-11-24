import customtkinter as ctk
from ui_components import MainApp
from serial_handler import SerialHandler
import threading
import time
import random

class MockSerialHandler(SerialHandler):
    def get_ports(self):
        return ["MOCK_PORT"]
        
    def connect(self, port, baudrate=9600):
        self.is_running = True
        self.thread = threading.Thread(target=self._mock_loop, daemon=True)
        self.thread.start()
        if self.on_log: self.on_log(f"Connected to {port} (MOCK)")
        return True
        
    def _mock_loop(self):
        while self.is_running:
            time.sleep(0.1)
            # Simulate Status Report (approx every 1s)
            if random.random() < 0.1:
                # STATUS:D2:1,D3:0,A0:512
                d2 = 1 if random.random() > 0.5 else 0
                a0 = int(random.random() * 1024)
                msg = f"STATUS:D2:{d2},D3:0,A0:{a0}"
                self._parse_status(msg)
            
            # Simulate random message
            if random.random() < 0.05:
                if self.on_message: self.on_message("Device -> PC", "Hello from Mock Device")

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    
    app = MainApp()
    # Inject mock handler
    app.serial = MockSerialHandler()
    # Re-bind callbacks
    app.serial.on_message = app.on_message
    app.serial.on_status = app.on_status
    app.serial.on_log = app.log_message
    
    app.mainloop()
