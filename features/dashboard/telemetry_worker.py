import json
import os
from PyQt6.QtCore import QThread, pyqtSignal, QTimer
import socket
import time

class TelemetryWorker(QThread):
    log_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    server_status_changed = pyqtSignal(bool)
    
    def __init__(self, config_path="data/server_config.json"):
        super().__init__()
        self.socket = None
        self.config_path = config_path
        self.is_running = True
        
        self.host, self.port, self.password = self._load_settings()

    def _load_settings(self):
        """Loads IP and Port from the JSON configuration."""
        if not os.path.exists(self.config_path):
            print("[DEBUG] Config not found, defaulting to localhost.")
            # FIX: Return 3 items to match unpacking requirements
            return "127.0.0.1", 30004, ""
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                # Use .get() to provide safety defaults if keys are missing
                ip = data.get("input_ip", "127.0.0.1")
                port = int(data.get("input_port", 30004))
                password = data.get("input_pass", "")
                
                return ip, port, password
        except Exception as e:
            print(f"[ERROR] Loading settings: {e}")
            return "127.0.0.1", 30004, ""

    def run(self):
        # Initialize the watchdog to detect stream stalls
        self.watchdog_timer = QTimer()
        self.watchdog_timer.moveToThread(self)
        self.watchdog_timer.setInterval(30000)
        self.watchdog_timer.timeout.connect(self.handle_server_timeout)
        
        while self.is_running:
            try:
                # Log the initiation of the socket object
                print("[DEBUG] Initializing new socket object...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(20.0)
                
                # Log the connection attempt
                print(f"[DEBUG] Attempting connection to {self.host}:{self.port}...")
                self.socket.connect((self.host, int(self.port)))
                print("[DEBUG] Connection established.")
                
                # Log banner receipt
                banner = self.socket.recv(1024)
                print(f"[DEBUG] Received banner: {banner.decode(errors='ignore').strip()}")
                
                # Transmit authentication credentials
                print("[DEBUG] Transmitting authentication token...")
                self.socket.sendall(f"{self.password}\r\n".encode('utf-8'))
                
                # Transition to read-only state to prevent firewall-triggered write-aborts
                self.socket.shutdown(socket.SHUT_WR)
                print("[DEBUG] Socket locked to read-only mode.")
                
                self.connection_status.emit(True)
                self.watchdog_timer.start()

                while self.is_running:
                    # Ingest incoming telemetry data
                    data = self.socket.recv(8192)
                    if data:
                        self.watchdog_timer.start()
                        decoded = data.decode(errors='ignore')
                        if len(decoded) > 0 and "currentFont" not in decoded:
                            self.log_received.emit(decoded)
                    else:
                        print("[DEBUG] Socket EOF: Connection closed by remote host.")
                        break
            
            except Exception as e:
                # Capture and log the specific exception type and message
                print(f"[ERROR] Socket lifecycle exception: {type(e).__name__} - {e}")
                self.server_status_changed.emit(False)
                time.sleep(10)
            finally:
                if hasattr(self, 'socket'):
                    self.socket.close()
                    print("[DEBUG] Socket resource released.")

    def handle_server_timeout(self):
        print("[WARNING] Server telemetry stream timed out.")
        # Emit a custom signal to the MainCockpit to update the UI
        self.server_status_changed.emit(False)

    def send_command(self, command):
        """Sends a single admin command via an ephemeral socket."""
        try:
            # Create a separate, short-lived socket just for the command
            cmd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            cmd_socket.settimeout(5.0)
            cmd_socket.connect((self.host, int(self.port)))
            
            # Re-authenticate for the command session
            cmd_socket.sendall(f"{self.password}\r\n".encode('utf-8'))
            
            # Send the actual admin command
            cmd_socket.sendall(f"{command}\r\n".encode('utf-8'))
            
            # Close immediately to prevent host-side write-abort
            cmd_socket.close()
            print(f"[STATUS] Command sent successfully: {command}")
        except Exception as e:
            print(f"[ERROR] Command failed: {e}")

    def stop(self):
        self.is_running = False
        # Force close the socket if it exists to break a blocking recv() or connect()
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                print(f"[STATUS] Socket Closing Connection.")
                self.socket.close()
            except:
                pass
        self.wait()