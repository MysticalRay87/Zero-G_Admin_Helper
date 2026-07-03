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
    signal_data_received = pyqtSignal(dict)

    def __init__(self, config_path="data/server_config.json"):
        super().__init__()
        self.config_path = config_path
        self.is_running = False
        self.socket = None
        
        # Dynamically load destination coordinates and passkey
        self.host, self.port, self.password = self._load_credentials()
        
        # Initialize the parser
        self.parser = TelemetryParser()

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

                # Emit only the success status
                self.connection_status.emit(True)

                # Inject credentials to unblock the game server data pipe
                if self.password:
                    print("[DEBUG] Injecting network validation handshake...")
                    auth_payload = f"{self.password}\r\n"
                    self.socket.sendall(auth_payload.encode('utf-8'))
                    
                print("[SUCCESS] Telemetry bridge secured. Locked in passive mirror stream.")
                self.connection_status.emit(True)
                backoff_delay = 1.0 

                # BUFFERED CONSUMER: Wrap socket to enable .readline()
                stream = self.socket.makefile('r', encoding='utf-8', errors='ignore')

                # Set a long timeout to allow the server's 60-second quiet periods
                # without corrupting the makefile stream buffer with micro-timeouts
                self.socket.settimeout(90.0)

                # Passive Stream Consumer Loop (Strict Read-Only + Heartbeat Pulse)
                while self.is_running:
                    try:
                        line = stream.readline()

                        # If line is empty, the server has closed the connection
                        if not line: 
                            print("[DEBUG] Remote host severed the passive logging stream.")
                            break 

                        # Pre-Parse Sanitation Gate
                        # Filter for valid length (standard logs are < 512 chars) 
                        # and verify it's a readable text line.
                        if len(line) > 1024:
                                # Discard massive binary dump
                                continue
                        
                        # Filter out raw font tags or empty telemetry artifacts
                        if "currentFont" not in line and "System." not in line:
                            # SANITY BUFFER GUARD: Prevent binary-dump overflows
                            self.log_received.emit(line)
                            
                            # PARSE: Extract metrics and emit as dict
                            data = self.parser.parse(line)
                            if data:
                                self.signal_data_received.emit(data)

                    except socket.timeout:
                        # --- DEDICATED TELNET HEARTBEAT PULSE ---
                        # Timeout here means the server has been completely silent for over 90 seconds.
                        # Break out to trigger a clean reconnection cycle.
                        print("[WARNING] Telemetry stream silent for too long. Reconnecting...")
                        break
                    except Exception as e:
                        print(f"[DEBUG] Stream error: {e}")
                        break
                stream.close() # Safely close the stream object

            except Exception as e:
                if self.is_running:
                    print(f"[ERROR] Telemetry network exception occurred: {str(e)}")
                self.connection_status.emit(False)
            finally:
                if self.socket:
                    try: self.socket.close()
                    except: pass
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