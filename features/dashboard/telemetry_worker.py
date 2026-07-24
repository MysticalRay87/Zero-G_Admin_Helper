# telemetry_worker.py

import os
import time
import socket
import json
import paramiko
import threading

from PyQt6.QtCore import QThread, pyqtSignal
from features.dashboard.telemetry_parser import TelemetryParser, MsgType

class TelemetryWorker(QThread):
    # Signals for UI communication
    log_received = pyqtSignal(str)
    signal_metrics = pyqtSignal(dict)
    signal_player_join = pyqtSignal(dict)
    signal_global_chat = pyqtSignal(dict)
    signal_faction_chat = pyqtSignal(dict)
    status_msg = pyqtSignal(str)
    connection_status = pyqtSignal(bool) # Emit True when FTP is working   

    def __init__(self, telnet_config):
        super().__init__()
        # Load mirror config
        with open("data/mirror_config.json", 'r') as f:
            self.mirror_cfg = json.load(f).get("ftp_settings")
        
        self.ftp_cfg = self.mirror_cfg
        self.local_log = self.mirror_cfg["local_mirror"]
        
        # Primary Telnet settings
        self.host = telnet_config.get("input_ip")
        self.port = telnet_config.get("input_port")
        self.password = telnet_config.get("input_pass")
        
        self.parser = TelemetryParser()
        self.running = True
        print("[DEBUG] TelemetryWorker: Initialization complete.")
        self.lock = threading.Lock()

    def sync_logs(self):
        """Background Sync: Pulls log updates via SFTP."""
        try:
            transport = paramiko.Transport((self.ftp_cfg["host"], self.ftp_cfg["port"]))
            transport.connect(username=self.ftp_cfg["user"], password=self.ftp_cfg["pw"])
            sftp = paramiko.SFTPClient.from_transport(transport)
            
            # Get local size for resume
            local_size = os.path.getsize(self.local_log) if os.path.exists(self.local_log) else 0

            # Open the file on the SERVER
            with sftp.open(self.ftp_cfg["log_path"], 'rb') as remote_file:
                remote_file.seek(local_size) # Skip already downloaded bytes

                # Open the file on your LOCAL MACHINE
                with open(self.local_log, 'ab') as local_file:
                    while True:
                        # Read from SERVER, Write to LOCAL
                        data = remote_file.read(4096)
                        if not data:
                            break
                        local_file.write(data)

            # ... cleanup ...    
            sftp.close()
            transport.close()
        except Exception as e:
            print(f"[ERROR] SFTP Sync failed: {e}")

    def run(self):
        """
        Passive Log-Watcher: Tails local mirror.
        Instruction: Initializes the connection once, then enters the tailing loop.
        """
        # Initial connection phase
        print("[DEBUG] TelemetryWorker: Attempting initial log sync...")
        self.sync_logs()
        print("[SUCCESS] TelemetryWorker: Log synchronization established.")
        if os.path.exists(self.local_log):
            print(f"[DEBUG] Processing mirror file: {self.local_log}")

            # --- 1. Open the file ONCE outside all loops ---
            with open(self.local_log, 'r', encoding='utf-8', errors='ignore') as f:

                # --- 2. SMART STARTUP: Read the last 50 lines instead of skipping everything ---
                lines = f.readlines()
                recent_lines = lines[-50:] if len(lines) > 50 else lines
                
                for line in recent_lines:
                    msg_type, data = self.parser.parse(line)
                    if msg_type == "METRIC":
                        self.signal_metrics.emit(data)
                    elif msg_type == "PLAYER_JOIN":
                        self.signal_player_join.emit(data)
                    elif msg_type == "GLOBAL_CHAT":
                        self.signal_global_chat.emit(data)
                    elif msg_type == "FACTION_CHAT":
                        self.signal_faction_chat.emit(data)

                # 3. Move pointer to the end so we only read new lines from here on to avoid reading legacy data
                f.seek(0, os.SEEK_END)

                sync_counter = 0

                # 4. SINGLE permanent tailing loop (No outer loops to restart it)
                while self.running:
                   
                    # Periodically pull fresh bytes from remote SFTP every ~5 seconds
                    sync_counter += 1
                    if sync_counter >= 0.5:
                        self.sync_logs()
                        # print(f"[INFO] Server Live-Log re-sync in progress...")
                        sync_counter = 0

                    line = f.readline()
                    if not line:
                        # Before sleeping, check for new logs
                        time.sleep(1.0)
                        continue 

                    # Parse lines and route signals
                    msg_type, data = self.parser.parse(line)

                    # 1. Route specific signals
                    if msg_type == "PLAYER_JOIN":
                        self.signal_player_join.emit(data)
                    elif msg_type == "GLOBAL_CHAT":
                        self.signal_global_chat.emit(data)
                    elif msg_type == "FACTION_CHAT":
                        self.signal_faction_chat.emit(data)
                    elif msg_type == "METRIC":
                        self.signal_metrics.emit(data)

                    # 2. Finally, emit raw log for the console    
                    if msg_type != MsgType.NOISE:
                        self.log_received.emit(f"[LOG] {line.strip()}\n")

    def write_command(self, cmd_text):
        """Ephemeral Command Proxy: Executes admin commands with stepped Telnet authentication."""
        with self.lock: # Ensures only one socket transaction happens at a time
            try:
                clean_cmd = cmd_text.strip()
                print(f"[DEBUG] Command Proxy: Handshake connecting to {self.host}:{self.port}...")
                
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2.0)
                    s.connect((self.host, int(self.port)))
                    
                    # --- STEP 1: READ THE GREETING ---
                    try:
                        initial_greeting = s.recv(1024)
                        print(f"[DEBUG] Telnet Connected. Server Greeting: {initial_greeting.decode('utf-8', errors='ignore').strip()}")
                    except socket.timeout:
                        print("[WARNING] No initial greeting received, proceeding...")

                    # --- STEP 2: SEND PASSWORD ALONE AND WAIT ---
                    s.sendall(f"{self.password}\r\n".encode('utf-8'))
                    time.sleep(0.1) # Let the server validate the auth token

                    # --- STEP 3: SEND THE ACTUAL COMMAND AND WAIT ---
                    print(f"[DEBUG] Injecting command: {clean_cmd}")
                    s.sendall(f"{clean_cmd}\r\n".encode('utf-8'))
                    
                    # --- STEP 4: ACCUMULATE MULTI-LINE STREAM CHUNKS ---
                    response_data = b""
                    start_time = time.time()
                    
                    # Keep listening until data stops arriving or a strict 1.5s window passes
                    while (time.time() - start_time) < 1.5:
                        try:
                            chunk = s.recv(4096)
                            if chunk:
                                response_data += chunk
                                # Reset timer slightly if active data is still flowing
                                start_time = time.time() 
                            else:
                                break
                        except socket.timeout:
                            # Clean exit when the server finishes transmitting data blocks
                            print(f"[CONNECT LOG] End of socket stream chunk.")
                            break
                    
                    response_str = response_data.decode('utf-8', errors='ignore').strip()
                    print(f"[DEBUG] Command Proxy Response Received ({len(response_str)} chars)")
                  
                    # If the command was a player registry pull, cache it locally
                    if clean_cmd == "plys":
                        self.cache_player_registry(response_str)

                    if response_str and hasattr(self, 'status_msg') and self.status_msg:
                        self.status_msg.emit(response_str)

                    #=================================
                    # --- RAW RESPONSE DEBUG PRINT ---
                    #=================================
                    print("================ [RAW SERVER RESPONSE START] ================")
                    print(response_str)
                    print("================ [RAW SERVER RESPONSE END] ================")
                    
                    print(f"[DEBUG] Command Proxy Response Received ({len(response_str)} chars)")

                    response_str = response_data.decode('utf-8', errors='ignore').strip()
                    print(f"[DEBUG] Command Proxy Response Received ({len(response_str)} chars)")
                    
                    if response_str and hasattr(self, 'status_msg') and self.status_msg:
                        self.status_msg.emit(response_str)

                    return True
                
            except Exception as e:
                print(f"[ERROR] Command Proxy failed: {e}")
                return False

    def cache_player_registry(self, raw_text):
        """Parses raw plys response and caches structured player records to disk."""
        parsed_records = []
        lines = raw_text.splitlines()
        
        for line in lines:
            stripped = line.strip()
            if "id=" in stripped and "name=" in stripped:
                player_id = "-"
                player_name = "-"
                faction = "-"
                role = "Online"
                
                tokens = stripped.split()
                for token in tokens:
                    if token.startswith("id="):
                        player_id = token.split("=")[1]
                    elif token.startswith("name="):
                        player_name = token.split("=")[1]
                    elif token.startswith("fac="):
                        faction = token.split("=")[1].replace("[", "").replace("]", "")
                    elif token.startswith("role="):
                        role = token.split("=")[1]
                
                # Build row matching your 11-column layout
                row_data = [
                    player_name,           # Player Name
                    faction,               # Faction
                    role,                  # Faction Role
                    "---",                 # Playfield (Derived from instance telemetry)
                    "---",                 # Solar System
                    "---",                 # Coordinates (E/W, Height, N/S)
                    player_id,             # Private ID
                    "Off",                 # Cheat
                    "NO",                  # Cheater                    
                    "NO",                  # Banned
                    "No"                   # Auto-Ban Protection
                ]
                parsed_records.append(row_data)
        
        # Write out to cache file safely
        cache_path = "data/player_registry_cache.json"
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(parsed_records, f, indent=4)
            print(f"[SUCCESS] Cached {len(parsed_records)} player records to {cache_path}")
        except Exception as e:
            print(f"[ERROR] Failed to write player registry cache: {e}")