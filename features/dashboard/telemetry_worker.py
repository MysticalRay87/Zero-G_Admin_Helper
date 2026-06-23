import json
import os
from PyQt6.QtCore import QThread, pyqtSignal
import socket
import time

class TelemetryWorker(QThread):
    log_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    
    def __init__(self, config_path="data/server_config.json"):
        super().__init__()
        self.socket = None
        self.config_path = config_path
        self.is_running = True
        
        # Load settings dynamically
        self.host, self.port = self._load_settings()

    def _load_settings(self):
        """Loads IP and Port from the JSON configuration."""
        if not os.path.exists(self.config_path):
            print("[DEBUG] Config not found, defaulting to localhost.")
            return "127.0.0.1", 30004
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                # Use .get() to provide safety defaults if keys are missing
                ip = data.get("input_ip", "127.0.0.1")
                port = int(data.get("input_port", 30004))
                return ip, port
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Config corruption: {e}")
            return "127.0.0.1", 30004

    def run(self):
        try:
            print(f"[THREAD] Telemetry worker started on {self.host}:{self.port}")
            # Simulate and broadcast the initial connection status
            self.log_received.emit(f"Telemetry initial sync at {time.strftime('%H:%M:%S')}")
            self.connection_status.emit(True)
            
            # Interval Polling
            while self.isRunning:
                time.sleep(15) # Network polling interval in seconds

                # Check running flag again before emitting after the long sleep
                if self.isRunning:
                    self.log_received.emit(f"Telemetry sync-check at {time.strftime('%H:%M:%S')}")
                    self.connection_status.emit(True)
        except (socket.error, Exception) as e:
            print(f"[ERROR] Telemetry worker error: {e}")
            self.connection_status.emit(False)
        finally:
            if self.socket:
                self.socket.close()

    def stop(self):
        self.isRunning = False
        # Force close the socket if it exists to break a blocking recv() or connect()
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                print(f"[STATUS] Socket Closing Connection.")
                self.socket.close()
            except:
                pass
        self.wait()