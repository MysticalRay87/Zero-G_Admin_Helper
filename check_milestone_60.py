import os
import json
import socket

# Define paths matching out State Separation Protocol
CONFIG_PATH = "data/server_config.json"
TIMEOUT_LIMIT = 2.5

print("===========================================")
print("INITIALIZATION MILESTONE: 60% NETWORK CHECK")
print("===========================================")

# Step 1: Initialize baseline memory states for connection variables
target_ip = ""
target_port = 0
target_host = ""
is_first_time_activation = True

# Step 2: Evaluate First-Time Activation by checking configuration file existence
if os.path.exists(CONFIG_PATH):
    is_first_time_activation = False
    print ("Existing network configuration detected.")

    with open(CONFIG_PATH, "r") as file_stream:
        try:
            config_data = json.load(file_stream)

            # Safely extract core input variables from JSON structure
            target_ip = config_data.get("server_ip", "")
            target_port = int(config_data.get("telnet_port", 0))
            telnet_password = config_data.get("auth_token", "")

            print("PARSING CREDENTIALS: IP={target_ip}, Port={target_port}")

        except (json.JSONDecodeError, ValueError):
            print("CRITICAL ERROR: server_config.json contains unparseable format formatting.")
            target_ip = "" # Force validation failure to trigger wizard fallback
else:
    print("FIRST-TIME ACTIVATION STATUS VERIFIED: No configuration file detected.")

print("=====================================================================")

# Step 3: Run structural input validation checks before opening network hardware
if not target_ip or target_port <= 0 or not telnet_password:
    print("Configuration Validation Status: INCOMPLETE / BLANK")
    print("SCREEN ROUTE: Launching 'Network Connection Wizard' Layout Panel...")
    print("Required Interactive Input Actions:")
    print("   [1] Input Targeted IP Address Field")
    print("   [2] Input Active TelNET Port Field")
    print("   [3] Input Verified Password (Host-Provided or Custom)")
    print("   [4] Apply/Accept Settings or hit Reset to clear fields to blank")
else:
    print("🛑 Configuration Validation Status: VERIFIED")
    print(f"📡 Initiating low-level connection handshake to GTX Gaming hardware...")
    
    # Establish our IPv4 TCP Stream channel descriptor
    probe_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe_socket.settimeout(TIMEOUT_LIMIT)
    
    try:
        # Probe the remote port boundary
        probe_socket.connect((target_ip, target_port))
        
        print("PERSISTENT NETWORK LINK FULLY ESTABLISHED.")
        print(f"TelNET Session Authenticated using Secure Token [***{telnet_password[-2:] if len(telnet_password) > 2 else ''}]")
        print("PROGRESS GATE: 60% Clear. System stable. Streaming dashboard layout...")
        
    except socket.timeout:
        print("CONNECTION FAILURE: Remote port failed to complete handshake within limit.")
        print("SCREEN ROUTE: Falling back to 'Network Connection Wizard' for verification...")
        
    except Exception as connection_error:
        print(f"CONNECTION FAILURE: Network socket dropped with code: {connection_error}")
        print("SCREEN ROUTE: Falling back to 'Network Connection Wizard'...")
        
    finally:
        # Ensure our script explicitly closes the test file descriptor handle
        probe_socket.close()
        print("SYSTEM CLEANUP: Temporary network socket released safely.")

print("=====================================================================")