import json
import os
from PyQt6.QtCore import QThread, pyqtSignal
import socket
import time

class TelemetryWorker(QThread):
    # Establish signals to communicate data pulses back to the main cockpit UI
    log_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)

    def __init__(self, config_path="data/server_config.json"):
        super().__init__()
        self.config_path = config_path
        self.is_running = False
        self.socket = None
        
        # Dynamically load destination coordinates and passkey
        self.host, self.port, self.password = self._load_credentials()

    def _load_credentials(self):
        """Loads networking parameters and authentication keys from local storage safely."""
        if not os.path.exists(self.config_path):
            print("[DEBUG] Config not found, defaulting to localhost.")
            return "127.0.0.1", 30004, ""
            
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                ip = data.get("input_ip", "127.0.0.1")
                port = int(data.get("input_port", 30004))
                password = data.get("input_pass", "")
                return ip, port, password
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[ERROR] Config corruption detected while parsing settings: {e}")
            return "127.0.0.1", 30004, ""

    def run(self):
        self.is_running = True
        backoff_delay = 1.0

        while self.is_running:
            try:
                print(f"[DEBUG] Opening telemetry socket to {self.host}:{self.port}...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(15.0)
                self.socket.connect((self.host, int(self.port)))
                
                # --- HANDSHAKE SUPPRESSION GATE ---
                # Silently clear out the initial challenge greeting ("Please enter password:")
                try:
                    self.socket.recv(1024)
                except socket.timeout:
                    pass

                # Inject credentials to unblock the game server data pipe
                if self.password:
                    print("[DEBUG] Injecting network validation handshake...")
                    auth_payload = f"{self.password}\r\n"
                    self.socket.sendall(auth_payload.encode('utf-8'))
                    
                print("[SUCCESS] Telemetry bridge secured. Locked in passive mirror stream.")
                self.connection_status.emit(True)
                backoff_delay = 1.0 

                # Enforce a tight 5-second frame to periodically unblock recv() for keep-alives
                self.socket.settimeout(5.0)

                # Passive Stream Consumer Loop (Strict Read-Only + Heartbeat Pulse)
                while self.is_running:
                    try:
                        raw_bytes = self.socket.recv(8192)
                        if not raw_bytes:
                            print("[DEBUG] Remote host severed the passive logging stream.")
                            break

                        decoded_line = raw_bytes.decode('utf-8', errors='ignore')
                        
                        # Filter out raw font tags or empty telemetry artifacts if any are sent
                        if "currentFont" not in decoded_line:
                            self.log_received.emit(decoded_line)

                    except socket.timeout:
                        # --- DEDICATED TELNET HEARTBEAT PULSE ---
                        if self.is_running and self.socket:
                            try:
                                self.socket.sendall(b"\r\n")
                            except Exception:
                                print("[DEBUG] Heartbeat pulse failed. Connection is stale.")
                                break

            except socket.timeout:
                print("[ERROR] Telemetry stream timed out waiting for server broadcast.")
                self.connection_status.emit(False)
            except Exception as e:
                if self.is_running:
                    print(f"[ERROR] Telemetry network exception occurred: {str(e)}")
                self.connection_status.emit(False)
            finally:
                if self.socket:
                    try:
                        self.socket.close()
                    except Exception:
                        pass
                    self.socket = None

            # Interruptible backoff delay for rapid app shutdown compliance
            if self.is_running:
                print(f"[DEBUG] Cooling down. Reconnecting in {backoff_delay} seconds...")
                wake_time = time.time() + backoff_delay
                while self.is_running and time.time() < wake_time:
                    time.sleep(0.1)
                    
                backoff_delay = min(backoff_delay * 2, 60.0)

    def stop(self):
        """Gracefully shuts down the background telemetry stream thread."""
        self.is_running = False
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except Exception:
                pass
        self.quit()
        self.wait(1)