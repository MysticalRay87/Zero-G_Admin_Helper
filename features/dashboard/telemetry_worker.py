# telemetry_worker.py

import json
import os
import socket
import select
import time
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from features.dashboard.telemetry_parser import TelemetryParser
from enum import Enum

telemetry_lock = threading.Lock()

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
    signal_global_chat = pyqtSignal(dict)
    signal_faction_chat = pyqtSignal(dict)
    signal_metrics = pyqtSignal(dict)
    signal_player_join = pyqtSignal(dict)

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
                # Force a snapshot of online players upon first entry
                print("[DEBUG] STREAMING activated. Requesting player list snapshot...")
                self.write_command("plys")

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

        print("[DEBUG] TelemetryWorker: Stream captured.")

    def _perform_streaming(self):
        """
        Manages the high-speed passive stream reading and signal emission.
        Uses non-blocking multiplexing to allow safe interface shutdown.
        Returns True while streaming, False if the stream is broken.
        """
        try:
            # Create the buffered text stream wrapper
            stream = self.socket.makefile('r', encoding='utf-8', errors='ignore')
            
            # Crucial step: Set raw socket to non-blocking mode so readline() doesn't freeze the QThread
            self.socket.setblocking(False)
            timeout_seconds = 90.0
            
            print("[DEBUG] State: STREAMING - Non-blocking Pipeline open.")
            
            while self.is_running:
                # Use select to wait for data safely without eating 100% CPU core limits
                ready_to_read, _, _ = select.select([self.socket], [], [], 1.0) # 1-second ticks
                
                if not ready_to_read:
                    continue
                    
                line = stream.readline()
                if not line:
                    print("[DEBUG] Stream EOF detected.")
                    return False
                
                # Remove (hash) to reactivate Raw Stream Ingestion
                print(line.strip())
                
                # 1. Route through the token parser FIRST
                msg_type, data = self.parser.parse(line)

                # 2. If parser flags it as NOISE, drop it completely
                if msg_type == "NOISE":
                    continue 

                # 3. Emit the clean line to the Active Logs console
                self.log_received.emit(line.strip())

                # --- SIGNAL DISSEMINATION ---
                if msg_type == "PLAYER_JOIN":
                    print(f"[DEBUG] PlayerJoin: Emitting Player ID/Name Signal: {data}")
                    self.signal_player_join.emit(data)
                elif msg_type == "GLOBAL_CHAT":
                    print(f"[DEBUG] GlobalChat: Emitting GlobalChat Signal: {data}")
                    self.signal_global_chat.emit(data)
                elif msg_type == "FACTION_CHAT":
                    print(f"[DEBUG] FactionChat: Emitting FactionChat Signal: {data}")
                    self.signal_faction_chat.emit(data)
                elif msg_type == "METRIC":
                    print(f"[DEBUG] METRICS: Emitting METRICS Signal: {data}")
                    self.signal_metrics.emit(data)
                    
            return True

        except (socket.timeout, socket.error) as e:
            print(f"[DEBUG] Connection stream severed: {str(e)}")
            return False
        except Exception as e:
            print(f"[DEBUG] Unhandled exception inside stream controller: {str(e)}")
            return False
        finally:
            stream.close()

    def write_command(self, cmd_text):
        """
        Multiplexer Authority Method:
        Injects commands into the existing persistent telemetry socket.
        This allows the CommandPipe to function as a lightweight proxy
        without needing its own socket connection.
        """
        # Ensuring app is currently connected and streaming before attempting I/O
        if self.state != WorkerState.STREAMING or not self.socket:
            print("[ERROR] Multiplexer: Telemetry socket is not active.")
            return False
            
        try:
            # Use the global telemetry_lock to ensure atomic socket access.
            # This prevents sending commands while the read-loop is active.
            with telemetry_lock:
                print(f"[DEBUG] Multiplexer: Injecting command: {cmd_text.strip()}")
                
                # Encode command with Windows-style \r\n terminator (GTXGaming requirement)
                full_cmd = f"{cmd_text.strip()}\r\n".encode('utf-8')
                self.socket.sendall(full_cmd)
                return True
        except Exception as e:
            # Log failure if the socket connection was interrupted
            print(f"[ERROR] Multiplexer injection failed: {e}")
            return False
    
    def stop(self):
        """Gracefully halts the pipeline and forcibly kills the socket."""
        self.is_running = False
        if self.socket:
            try:
                # Tell the server we are done, allowing a clean session cleanup
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
            except Exception as e:
                print(f"[DEBUG] Socket cleanup error: {e}")
        self.quit()
        self.wait(1000) # Wait up to 1 second for the thread to join