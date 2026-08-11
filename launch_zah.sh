#!/bin/bash

PROJECT_DIR="/mnt/Zero-G_Files/Zero-G_Forge/Zero-G_Admin_Helper"

if [ -z "$ZAH_TERMINAL_SPAWNED" ]; then
    export ZAH_TERMINAL_SPAWNED=1
    
    # Launch gnome-terminal:
    # Width x Height + X_Offset + Y_Offset
    # X=1020 pushes it to the right
    # Y=200 pushes it down so it doesn't load too high up/above the app window
    gnome-terminal --class="zah_right_terminal" --title="ZAH_TERMINAL" --working-directory="$PROJECT_DIR" -- "$0" "$@" &
    
    sleep 0.3
    wmctrl -x -r "zah_right_terminal" -e 0,1900,1200,600,750 2>/dev/null
    
    exit 0
fi

cd "$PROJECT_DIR"
source .venv/bin/activate
python3 ZAH.py
