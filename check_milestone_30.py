import os
import json

# Define our relative data path reference
DATA_PATH = "data/users.json"

print("==================================================")
print("INITIALIZATION MILESTONE: 30% USER LOGIN CHECK")
print("==================================================")

# Default Boolean flags tracking state boundaries
has_admin_profile = False

if os.path.exists(DATA_PATH):
	with open(DATA_PATH, 'r') as file_stream:
		try:
			user_database = json.load(file_stream)

			# Scenario A: The file exists but contains an empty list[]
			if len(user_database) == 0:
					print("SYSTEM NOTIFICATION: User database is empty.")
					print("SCREEN ROUTE: Launching 'Account Creation Wizard'")

			else:
				#Scenario B: Profiles exist; scan entries for administrative roles
				for user in user_database:
					current_role = user.get("account_type", "Standard User")

					if current_role == "Server Admin":
						has_admin_profile = True
						break # Found an admin, stop scanning

				# Screen steering based on flag state
				if has_admin_profile:
					print("ADMINISTRATIVE ACCOUNT VERIFIED.")
					print("PROGRESS GATE: 30% Clear: Advancing to 60% Network Check...")
				else:
					print("SECURITY HALT: No 'Server Admin' profile detected in database.")
					print("SCREEN ROUTE: Launching 'Account Creation Wizard'...")
		except json.JSONDecodeError:
			print("CRITICAL ERROR: Corrupted data structure detected!")
			print("SCREEN ROUTE: Halting boot sequence for data repair...")

else:
    # Scenario C: The user.json file is completely missing
    print("SYSTEM WARNING: User data storage file does not exist.")
    print("SCREEN ROUTE: Launching 'Account Creation Wizard' to initialize database...")

print("=====================================================================")
