import os
import json

# Define the local data file path relative to our execution root
DATA_PATH = "data/users.json"

print("============================================")
print("Zero-G Diagnostic Gate: User Profile Validation")
print("============================================")

# Step 1: Structure Path Check
if os.path.exists(DATA_PATH):
        print(f"Found data file at {DATA_PATH}")

        # Step 2: Establish a secure context manager read stream
        with open(DATA_PATH, "r") as file_stream:
                try:
                    # Parse the text data directly into a native Python list
                    user_list = json.load(file_stream)

                    print(f"Total Registered Profiles Identified: {len(user_list)}")

                    # Print a clean, column-aligned table header
                    print(f"{'USERNAME':<16} | {'ASSIGNED ACCOUNT TYPE':<20} | {'STATUS':<10}")
                    print("-" * 55)

                    # Step 3: Loop through the json array elements sequentially
                    for user in user_list:
                           # Safely extract dictionary keys using fallback default entries
                           username = user.get("username", "Unknown User")
                           account_type = user.get("account_type", "Unassigned Tier")
                           account_status = user.get("status", "Inactive")

                           # Render the variables within formatted f-string layout blocks
                           print(f"{username:<16} | {account_type:<20} | {account_status:<10}")

                except json.JSONDecodeError:
                       print("Critical System Error: JSON format contains structural corruption.")
else:
    print(f"Verification Failure: Target file is missong at '{DATA_PATH}'")

print("==========================================================================")