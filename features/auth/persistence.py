import json
import os
from datetime import datetime, timedelta

SESSION_FILE = "data/session.json"
USERS_FILE = "data/users.json"

def get_data_path():
    """Returns the base data directory path."""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

def create_user_profile(username, password, role):
    """Creates an enriched user profile object."""
    now = datetime.now().strftime("%m/%d/%Y at %H:%M")
    return {
        "Username": username,
        "Password": password,
        "Account Type": role,
        "Account Creation": now,
        "Last Accessed": now,
        "Status": "Active",
        "Keep me logged in status": False # Default state
    }

def save_account_data(user_data):
    """Saves user account data to users.json."""
    os.makedirs("data", exist_ok=True)
    users = []
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            try:
                users = json.load(f)
            except:
                users = []
    
    users.append(user_data)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

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
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
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
    file_path = USERS_FILE
    try:
        if not os.path.exists(file_path):
            print(f"[ERROR] Cannot save persistence: {file_path} not found.")
            return
        
        with open(file_path, 'r') as f:
            users = json.load(f)
        
        # Update the specific user's record
        for user in users:
            if user.get("Username") == username:
                user["Keep me logged in status"] = persist
                break
        
        # Commit the updated list to the registry
        with open(file_path, 'w') as f:
            json.dump(users, f, indent=4)
        print(f"[SUCCESS] Persistance updated for {username}: {persist}")
            
    except Exception as e:
        print(f"[ERROR] Failed to save persistence: {e}")

def update_last_login(username):
    """Updates the 'Last Accessed' field for a specific user."""
    file_path = USERS_FILE
    try:
        with open(file_path, 'r') as f:
            users = json.load(f)
        
        now = datetime.now().strftime("%m/%d/%Y - %H:%M")
        for user in users:
            if user.get("Username") == username:
                user["Last Accessed"] = now
                break
        
        with open(file_path, 'w') as f:
            json.dump(users, f, indent=4)
        print(f"[SUCCESS] Last Accessed updated for {username}")
    except Exception as e:
        print(f"[ERROR] Failed to update login timestamp: {e}")