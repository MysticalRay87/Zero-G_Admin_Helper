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
                # Non-blocking check with timeout allows loop evaluation for teardowns
                cmd_text = self.cmd_queue.get(timeout=1.0)
                
                # Hand over to specialized execution function to handle the connection burst
                self._execute_ephemeral_burst(cmd_text)
                
                # Document queue consumption success
                self.cmd_queue.task_done()
                
                # Enforce calibration constraints: mandatory 500ms jitter stabilization delay
                time.sleep(0.5)
                
            except queue.Empty:
                # Normal condition when waiting for operator input
                continue
            except Exception as e:
                self.pipe_error.emit(f"Core process exception: {str(e)}")

    def _execute_ephemeral_burst(self, cmd_text):
        """Establishes an ephemeral short-lived channel to deliver a command burst."""
        sock = None
        try:
            print(f"[DEBUG] Executing ephemeral channel burst for: '{cmd_text}'")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5.0)
            sock.connect((self.host, int(self.port)))

            # Read initial challenge/welcome banner if presented by remote host
            try:
                welcome = sock.recv(1024).decode('utf-8', errors='ignore')
                print(f"[DEBUG] Remote host greeting: {welcome.strip()}")
            except socket.timeout:
                pass

            # Step 1: Deliver custom authentication handshake string structure
            auth_payload = f"{self.password}\r\n"
            sock.sendall(auth_payload.encode('utf-8'))
            time.sleep(0.1) # Brief internal processing delay before writing command

            # Step 2: Inject admin command formatted with Windows line endings (\r\n)
            command_payload = f"{cmd_text}\r\n"
            sock.sendall(command_payload.encode('utf-8'))
            print(f"[SUCCESS] Command payload successfully written to network socket: {cmd_text}")
            
            # Broadcast validation milestone back to HUD view
            self.command_sent.emit(cmd_text)

        except Exception as e:
            err_msg = f"Failed to deliver command burst: {str(e)}"
            print(f"[ERROR] {err_msg}")
            self.pipe_error.emit(err_msg)
            
        finally:
            if sock:
                try:
                    # Instantly enforce low-level graceful shutdown connection teardown
                    sock.shutdown(socket.SHUT_RDWR)
                    sock.close()
                    print("[DEBUG] Ephemeral channel torn down smoothly.")
                except Exception:
                    pass

    def stop(self):
        """Gracefully halts the pipeline worker loop processing."""
        self.is_running = False
        self.wait()