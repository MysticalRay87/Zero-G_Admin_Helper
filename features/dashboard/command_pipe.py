import os, json, queue, socket, time
from PyQt6.QtCore import QThread, pyqtSignal

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
                cmd_text = self.cmd_queue.get(timeout=1.0)
                self._execute_ephemeral_burst(cmd_text)
                self.cmd_queue.task_done()
                
                # Enforce calibration constraints: mandatory 500ms jitter stabilization delay
                time.sleep(0.5)
                
            except queue.Empty:
                continue
            except Exception as e:
                self.pipe_error.emit(f"Core process exception: {str(e)}")

    def _execute_ephemeral_burst(self, cmd_text):
        """Executes command and sanitizes output at the pipe level."""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, int(self.port)))
            
            # Authenticate and send command in one block
            sock.sendall(f"{self.password}\r\n{cmd_text}\r\n".encode('utf-8'))
            
            # Read until server goes silent
            response_chunks = []
            sock.settimeout(0.5)
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk: break
                    response_chunks.append(chunk.decode('utf-8', errors='ignore'))
                except socket.timeout:
                    break
            
            raw_response = "".join(response_chunks)

            # --- AGGRESSIVE SANITIZATION GATE ---
            # Define exact string patterns that MUST be dropped
            noise_patterns = [
                "Logged in successfully", "Empyrion dedicated server", 
                "Version:", "Port:", "Mode:", "Playfield:", "Name:", 
                "Game seed:", "=", "Thread 'TelnetClient", 
                "ManagedId", "ThreadId", "INFO: Uptime=", 
                "{EPM} Timelog:", "Telnet Connection closed", 
                "Unable to read", "Unable to write", "aborted", ".)"
            ]

            # Filter: Keep line ONLY if it has content AND does not contain noise
            sanitized_lines = [
                line.strip() for line in raw_response.splitlines()
                if line.strip() and not any(noise in line for noise in noise_patterns)
            ]
            
            sanitized_response = "\n".join(sanitized_lines)

            # Final Emit
            if sanitized_response:
                self.status_msg.emit(sanitized_response)
            
            self.command_sent.emit(cmd_text)

        except (socket.timeout, socket.error) as e:
            self.pipe_error.emit(f"Pipe connection failed: {e}")
        finally:
            if sock: 
                sock.close()

    def stop(self):
        """Gracefully halts the pipeline worker loop processing."""
        self.is_running = False
        self.wait()