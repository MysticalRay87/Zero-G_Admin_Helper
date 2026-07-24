# clear_pycache.py

import os
import shutil

def clear_pycache(directory):
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            # print(f"Removing: {pycache_path}")
            shutil.rmtree(pycache_path)
            dirs.remove('__pycache__')

root_directory = '/mnt/Zero-G_Files/Zero-G_Admin_Helper'

# Clear pycache
clear_pycache(root_directory)

print("[SUCCESS] All pycache directories have been removed.")