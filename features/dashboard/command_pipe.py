import os
import json
import queue
import socket
import time
from PyQt6.QtCore import QThread, pyqtSignal

from features.dashboard.telemetry_worker import telemetry_lock

class CommandPipe(QThread):
    # Established signals to communicate status information back to main_cockpit UI
    command_sent = pyqtSignal(str)
    pipe_error = pyqtSignal(str)
    status_msg = pyqtSignal(str)

    def __init__(self, config_path="data/server_config.json"):
        super().__init__()
        self.config_path = config_path
        # Thread-safe FIFO queue for incoming UI/button requests
        self.cmd_queue = queue.Queue()
        self.is_running = False
        # Dynamically load destination coordinates and passkey
        self.host, self.port, self.password = self._load_credentials()

    def _load_credentials(self):
        """Loads networking parameters and authentication keys from local storage."""
        if not os.path.exists(self.config_path):
            print("[DEBUG] CommandPipe configuration not found. Using defaults.")
            return "127.0.0.1", 30004, ""
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
            ip = data.get("input_ip", "127.0.0.1")
            port = int(data.get("input_port", 30004))
            password = data.get("input_pass", "")
            return ip, port, password
        except Exception as e:
            print(f"[ERROR] CommandPipe credentials load failure: {e}")
            return "127.0.0.1", 30004, ""

    def send_command(self, cmd_text):
        """Public API method for UI buttons to queue an admin action text payload."""
        if cmd_text:
            print(f"[DEBUG] Enqueueing command instruction payload: {cmd_text}")
            self.cmd_queue.put(cmd_text)

    def run(self):
        self.is_running = True
        print("[DEBUG] Command Core Pipeline Active. Standing by for queued payloads...")
        
        while self.is_running:
            try:
                # Wait for a command, checking every 1 second so the thread can shut down safely
                cmd_text = self.cmd_queue.get(timeout=1.0)
                
                if cmd_text:
                    print(f"[DEBUG] Command Core pulling from queue and executing: {cmd_text}")
                    
                    # Fire the ephemeral socket burst
                    self._execute_ephemeral_burst(cmd_text)
                    
                    # Mark the task as completed in the queue
                    self.cmd_queue.task_done()
                    
            except queue.Empty:
                # No command arrived this second. Loop back and wait safely.
                continue
            except Exception as e:
                self.pipe_error.emit(f"Critical Pipeline Fault: {e}")

    def _execute_ephemeral_burst(self, cmd_text):
        """
        Executes command with enforced socket destruction to prevent 
        GTXGaming connection aborts.
        """

        with telemetry_lock:
            sock = None
            try:
                # 1. HARD INITIALIZATION: Fresh socket for every burst
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5.0)
                
                # 2. CONNECTION: Connect to the defined server coordinates
                print(f"[DEBUG] Initiating burst to {self.host}:{self.port}")
                sock.connect((self.host, int(self.port)))

                # 3. AUTHENTICATION: Synchronous Handshake
                # Wait specifically for the password prompt to avoid sending data into a void
                sock.settimeout(3.0)
                banner = sock.recv(1024) 
                
                if b"Password" in banner:
                    sock.sendall(f"{self.password}\r\n".encode('utf-8'))
                    # Small delay to ensure the server processes the authentication
                    time.sleep(0.5) 
                    
                    # Vacuum out any remaining login banner data to clear the buffer
                    sock.setblocking(False)
                    try:
                        sock.recv(4096)
                    except:
                        pass
                    sock.setblocking(True)
                
                # 4. PAYLOAD INJECTION: Send command with required \r\n terminator
                sock.sendall(f"{cmd_text}\r\n".encode('utf-8'))
                
                # 5. RESPONSE CAPTURE: Wait for the result
                sock.settimeout(2.0)
                response = sock.recv(4096).decode('utf-8', errors='ignore')
                
                if response:
                    self.status_msg.emit(response)
                else:
                    self.pipe_error.emit("Command executed; no data returned.")

            except Exception as e:
                # Log failure to console and UI signal bridge
                self.pipe_error.emit(f"Ephemeral burst failed: {e}")
            finally:
                # 6. CRITICAL: Forcing total closure
                # This ensures no zombie sessions remain, preventing server-side aborts
                if sock:
                    try:
                        sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass # Socket already closed
                    sock.close()

    def stop(self):
        """Gracefully halts the pipeline worker loop processing."""
        self.is_running = False
        self.wait()