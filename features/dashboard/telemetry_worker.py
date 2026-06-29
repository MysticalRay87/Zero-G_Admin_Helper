import os,json, socket, time
from PyQt6.QtCore import QThread, pyqtSignal


class TelemetryWorker(QThread):
    log_received = pyqtSignal(str)
    server_status_changed = pyqtSignal(bool)
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
        # Establish passive log receiver loop
        # Note: All password writing and active handshake commands have been stripped 
        # to prevent socket contention with the incoming command pipeline.
        self.is_running = True
        backoff_delay = 1.0

        while self.is_running:
            try:
                print(f"[DEBUG] Opening telemetry socket to {self.host}:{self.port}...")
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(15.0)
                self.sock.connect((self.host, int(self.port)))
                
                print("[DEBUG] Connected. Listening strictly for passive broadcast stream...")
                self.connection_status.emit(True)
                backoff_delay = 1.0  # Reset backoff on successful connection

                while self.is_running:
                    raw_bytes = self.sock.recv(8192)
                    if not raw_bytes:
                        print("[DEBUG] Server closed the telemetry stream gracefully.")
                        break

                    # Process the inbound data pulse
                    decoded_line = raw_bytes.decode('utf-8', errors='ignore')
                    
                    # Filter binary noise or specific system fragments
                    if "currentFont" not in decoded_line:
                        self.log_received.emit(decoded_line)

            except socket.timeout:
                print("[ERROR] Telemetry stream timed out waiting for server broadcast.")
                self.server_status_changed.emit(False)
            except Exception as e:
                print(f"[ERROR] Telemetry network exception occurred: {str(e)}")
                self.server_status_changed.emit(False)
            finally:
                if self.socket:
                    self.socket.close()
                    self.socket = None

            # Enforce backoff tracking to prevent connection storms during cycles
            if self.is_running:
                print(f"[DEBUG] Cooling down. Reconnecting in {backoff_delay} seconds...")
                time.sleep(backoff_delay)
                backoff_delay = min(backoff_delay * 2, 60.0)

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