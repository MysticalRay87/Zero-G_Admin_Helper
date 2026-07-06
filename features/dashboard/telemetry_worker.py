import json
import os
import socket
import time
from PyQt6.QtCore import QThread, pyqtSignal
from features.dashboard.telemetry_parser import TelemetryParser
from enum import Enum

class WorkerState(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    AUTHENTICATING = 2
    STREAMING = 3
    RECOVERY = 4

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
        State-driven background thread for passive telemetry ingestion.
        """
        self.is_running = True
        self.state = WorkerState.DISCONNECTED
        backoff_delay = 1.0

        while self.is_running:
            # -------------------------------------------------------------
            # STATE: DISCONNECTED - Initializing
            # -------------------------------------------------------------
            if self.state == WorkerState.DISCONNECTED:
                print("[DEBUG] State: DISCONNECTED -> CONNECTING")
                self.state = WorkerState.CONNECTING

            # -------------------------------------------------------------
            # STATE: CONNECTING - Socket setup
            # -------------------------------------------------------------
            elif self.state == WorkerState.CONNECTING:
                try:
                    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.socket.settimeout(10.0)
                    print(f"[DEBUG] Attempting connection to {self.host}:{self.port}...")
                    self.socket.connect((self.host, int(self.port)))
                    self.connection_status.emit(True)
                    print("[DEBUG] State: CONNECTING -> AUTHENTICATING")
                    self.state = WorkerState.AUTHENTICATING
                    backoff_delay = 1.0 # Reset backoff on successful connect
                except Exception as e:
                    print(f"[DEBUG] Connection failed: {e}")
                    self.state = WorkerState.RECOVERY

            # -------------------------------------------------------------
            # STATE: AUTHENTICATING - Synchronized Handshake
            # -------------------------------------------------------------
            elif self.state == WorkerState.AUTHENTICATING:
                try:
                    self.socket.settimeout(5.0)
                    # Wait for password challenge prompt
                    response = self.socket.recv(1024)
                    print(f"[DEBUG] Received Handshake Challenge: {response.strip()}")
                    
                    if b"Enter password:" in response:
                        print("[DEBUG] Password prompt detected. Injecting credentials...")
                        self.socket.sendall(f"{self.password}\r\n".encode('utf-8'))
                        self.state = WorkerState.STREAMING
                        print("[DEBUG] State: AUTHENTICATING -> STREAMING")
                    else:
                        print("[DEBUG] Unexpected handshake response. Aborting.")
                        self.state = WorkerState.RECOVERY
                except Exception as e:
                    print(f"[DEBUG] Authentication failure: {e}")
                    self.state = WorkerState.RECOVERY

            # -------------------------------------------------------------
            # STATE: STREAMING - Passive Read Loop
            # -------------------------------------------------------------
            elif self.state == WorkerState.STREAMING:
                self._perform_streaming()
                # If _perform_streaming exits, we lost the stream
                print("[DEBUG] State: STREAMING -> RECOVERY")
                self.state = WorkerState.RECOVERY

            # -------------------------------------------------------------
            # STATE: RECOVERY - Exponential Backoff
            # -------------------------------------------------------------
            elif self.state == WorkerState.RECOVERY:
                self.connection_status.emit(False)
                if self.socket:
                    self.socket.close()
                    self.socket = None
                
                print(f"[DEBUG] State: RECOVERY. Sleeping {backoff_delay}s before retry.")
                time.sleep(backoff_delay)
                
                # Increase wait time to prevent GTXGaming flood-ban
                backoff_delay = min(backoff_delay * 2, 60.0)
                self.state = WorkerState.DISCONNECTED

    def _perform_streaming(self):
        """
        Manages the high-speed passive stream reading and signal emission.
        Returns True while streaming, False if the stream is broken.
        """
        try:
            # Create a buffered stream for line-by-line reading
            stream = self.socket.makefile('r', encoding='utf-8', errors='ignore')
            self.socket.settimeout(90.0) # Heartbeat timeout

            print("[DEBUG] State: STREAMING - Pipeline open.")

            while self.is_running:
                line = stream.readline()
                if not line:
                    print("[DEBUG] Stream EOF detected.")
                    return False
                # Route through the token parser
                msg_type, data = self.parser.parse(line)
                if msg_type == "NOISE":
                    continue # Ignore, don't emit to UI

                # Display NOISE filter logging for the console.
                self.log_received.emit(line)

                # Signal Dissemination
                if msg_type == "GLOBAL_CHAT":
                    self.signal_global_chat.emit(data)
                elif msg_type == "FACTION_CHAT":
                    self.signal_faction_chat.emit(data)
                elif msg_type == "METRIC":
                    self.signal_metrics.emit(data)

            return True

        except socket.timeout:
            print("[DEBUG] Stream timeout (90s).")
            return False
        except Exception as e:
            print(f"[DEBUG] Stream exception: {e}")
            return False
        finally:
            stream.close()    
    
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