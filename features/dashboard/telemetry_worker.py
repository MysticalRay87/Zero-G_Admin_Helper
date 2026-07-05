import json
import os
import socket
import time
from PyQt6.QtCore import QThread, pyqtSignal
from features.dashboard.telemetry_parser import TelemetryParser


class TelemetryWorker(QThread):
    # Establish signals to communicate data pulses back to the main cockpit UI
    log_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    signal_global_chat = pyqtSignal(str)
    signal_faction_chat = pyqtSignal(str)
    signal_metrics = pyqtSignal(dict)

    def __init__(self, config_path="data/server_config.json"):
        super().__init__()
        self.config_path = config_path
        self.is_running = False
        self.socket = None
        
        # Dynamically load destination coordinates and passkey
        self.host, self.port, self.password = self._load_credentials()
        
        # Initialize the parser
        self.parser = TelemetryParser() # Initialize the isolated parser
        self.running = True

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
        except (json.JSONDecodeError, Exception):
            return "127.0.0.1", 30004, ""

    def run(self):
        """
        Main worker thread loop: Manages socket lifecycle, auth, 
        and the passive telemetry stream ingestion.
        """
        self.is_running = True
        backoff_delay = 1.0

        while self.is_running:
            try:
                print(f"[DEBUG] Opening telemetry socket to {self.host}:{self.port}...")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.settimeout(15.0)
                self.socket.connect((self.host, int(self.port)))
                
                # --- HANDSHAKE SUPPRESSION GATE ---
                try:
                    self.socket.recv(1024)
                except socket.timeout:
                    pass

                # Signal connection status to the UI
                self.connection_status.emit(True)

                # Inject credentials to unlock the server data pipe
                if self.password:
                    print("[DEBUG] Injecting network validation handshake...")
                    auth_payload = f"{self.password}\r\n"
                    self.socket.sendall(auth_payload.encode('utf-8'))
                    
                print("[SUCCESS] Telemetry bridge secured. Locked in passive mirror stream.")
                backoff_delay = 1.0 

                # BUFFERED CONSUMER: Enable .readline() on the raw socket
                stream = self.socket.makefile('r', encoding='utf-8', errors='ignore')
                self.socket.settimeout(90.0)

                # Passive Stream Consumer Loop
                while self.is_running:
                    try:
                        line = stream.readline()
                        if not line: 
                            print("[DEBUG] Remote host severed the passive logging stream.")
                            break 

                        # Pre-Parse Sanitation: Ignore massive or invalid packets
                        if len(line) > 1024 or "currentFont" in line or "System." in line:
                            continue
                            
                        # Mirror the raw output for general console logging
                        self.log_received.emit(line)
                            
                        # TOKENIZATION: Route line through the TelemetryParser
                        msg_type, data = self.parser.parse(line)
                            
                        # SIGNAL ROUTING: Disseminate parsed data based on type
                        if msg_type == "GLOBAL_CHAT":
                            self.signal_global_chat.emit(data)
                        elif msg_type == "FACTION_CHAT":
                            self.signal_faction_chat.emit(data)
                        elif msg_type == "METRIC":
                            self.signal_metrics.emit(data)

                    except socket.timeout:
                        print("[WARNING] Telemetry stream silent for 90s. Reconnecting...")
                        break
                    except Exception as e:
                        print(f"[DEBUG] Stream error: {e}")
                        break
                stream.close() 

            except Exception as e:
                if self.is_running:
                    print(f"[ERROR] Telemetry network exception: {str(e)}")
                self.connection_status.emit(False)

            finally:
                if self.socket:
                    try: self.socket.close()
                    except: pass
                    self.socket = None

            # Exponential backoff mechanism for robust reconnection
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
        self.wait(1) # Wait for socket closure for 1 second, then force closure.