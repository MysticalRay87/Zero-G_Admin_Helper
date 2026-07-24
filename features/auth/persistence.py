# persistence.py

import json
import os
from datetime import datetime, timedelta
from features.security.security_module import SecurityModule

SESSION_FILE = "data/session.json"
USERS_FILE = "data/users.json"
file_path = "data/users.json"
sec = SecurityModule()

def get_data_path():
    """Returns the base data directory path."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def create_user_profile(username, password, role, steamID):
    """Creates an enriched user profile object."""
    now = datetime.now().strftime("%m/%d/%Y at %H:%M")
    return {
        "Username": username,
            "Password": password,
            "Account Type": role,
            "Keep me logged in status": False, # Default state
            "Steam ID": steamID,
            "Account Creation": now,
            "Account Status": "Active"
    }

def save_account_data(user_data):
    """Saves user account data securely to users.json."""
    os.makedirs("data", exist_ok=True)
    users = []
    
    # Load and decrypt existing users
    if os.path.exists(USERS_FILE):
        try:
            users = load_secure_data(USERS_FILE)
        except:
            users = []
    
    users.append(user_data)
    
    # Encrypt and save
    plaintext = json.dumps(users, indent=4)
    encrypted_blob = sec.encrypt_data(plaintext)
    with open(USERS_FILE, 'w') as f:
        f.write(encrypted_blob)

def load_secure_data(file_path):
    """Decrypts and loads JSON data."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r') as f:
        encrypted_blob = f.read()
    
    try:
        plaintext = sec.decrypt_data(encrypted_blob)
        return json.loads(plaintext)
    except Exception as e:
        print(f"[ERROR] Decryption failed: {e}")
        return []

def is_session_valid(expiry_days=365):
    """
    Checks if a valid session token exists and hasn't expired.
    Returns True if session is valid, False otherwise.
    """
    if not os.path.exists(SESSION_FILE):
        return False
        
    try:
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
            
        last_login = datetime.fromisoformat(data.get("timestamp", "2000-01-01T00:00:00"))
        if datetime.now() - last_login < timedelta(days=expiry_days):
            return True
    except (json.JSONDecodeError, ValueError, Exception) as e:
        print(f"[DEBUG] Session validation error: {e}")
        
    return False

def check_for_persistent_user():
    """Checks users.json for any user with persist_session == True."""
    if not os.path.exists(USERS_FILE):
        return False
    try:
        users = load_secure_data(file_path)
        for user in users:
            if user.get("Keep me logged in status") is True:
                return True
    except:
        return False
    return False

def save_session(username):
    """Saves a new session token to disk."""
    os.makedirs("data", exist_ok=True)
    data = {
        "username": username,
        "timestamp": datetime.now().isoformat()
    }
    with open(SESSION_FILE, 'w') as f:
        json.dump(data, f)
    print(f"[SUCCESS] Session saved for {username}")

def save_persistence_state(username, persist):
    try:
        users = load_secure_data(USERS_FILE)
        
        # Update the specific user's record
        for user in users:
            if user.get("Username") == username:
                user["Keep me logged in status"] = persist
                break
        
        # FIX: Encrypt the WHOLE 'users' list
        encrypted_blob = sec.encrypt_data(json.dumps(users, indent=4))
        with open(USERS_FILE, 'w') as f:
            f.write(encrypted_blob)
        print(f"[SUCCESS] Persistence updated for {username}: {persist}")
            
    except Exception as e:
        print(f"[ERROR] Failed to save persistence: {e}")

def update_last_login(username):
    """Updates the 'Last Accessed' field for a specific user securely."""
    try:
        users = load_secure_data(USERS_FILE)
        now = datetime.now().strftime("%m/%d/%Y - %H:%M")
        
        for user in users:
            if user.get("Username") == username:
                user["Last Accessed"] = now
                break
        
        # FIX: Ensure we write back an encrypted blob
        encrypted_blob = sec.encrypt_data(json.dumps(users, indent=4))
        with open(USERS_FILE, 'w') as f:
            f.write(encrypted_blob)
            
        print(f"[SUCCESS] Last Accessed updated for {username}")
    except Exception as e:
        print(f"[ERROR] Failed to update login timestamp: {e}")