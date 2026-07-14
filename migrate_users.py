import json
from features.security.security_module import SecurityModule

# Your users provided in the prompt
plaintext_users = [
    {
        "Username": "Enter username Here",
        "Password": "Enter password here",
        "Account Type": "Primary/Secondary Admin",
        "Keep me logged in status": # True/False,
        "Steam ID": # Enter 17 Digit SteamID here,
        "Account Creation": "Creation Date dd/mm/yyyy at hh:mm",
        "Account Status": "Active/Inactive",
        "Last Accessed": "Date dd/mm/yyyy at hh:mm"
    }
]

sec = SecurityModule()
encrypted_blob = sec.encrypt_data(json.dumps(plaintext_users, indent=4))

with open("data/users.json", "w") as f:
    f.write(encrypted_blob)

print("[SUCCESS] users.json has been migrated to encrypted format.")