import os
import os
import json
import socket # Added missing socket import for shutdown
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QFrame, QLabel, QVBoxLayout, 
    QTextEdit, QHBoxLayout, QComboBox, QLineEdit, QPushButton, 
    QTableWidget, QHeaderView, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtGui import QPainter, QPixmap

from features.dashboard.telemetry_worker import TelemetryWorker

'''
->self.mid_row_layout (QHBoxLayout): The invisible horizontal wrapper that keeps the Player Table and Button Matrix side-by-side.
->self.player_registry (QFrame): The visible box holding the player info. Sits on the left side of the mid-row.
->self.lbl_players_header (QLabel): (Blueprint #9) The text title saying "Players on server".
->self.player_table (QTableWidget): (Blueprint #10) The actual 5-column spreadsheet/grid displaying player data.
->self.control_panel (QFrame): The visible box holding the command matrix. Sits on the right side of the mid-row.
->self.matrix_buttons (List of QPushButtons): (Blueprint #11) This is a Python list holding all 18 buttons in your 3x6 grid. 
   -They don't have individual self names; instead, they are generated in a loop and stored here so you can program them later.
->self.display_fbp (QFrame): Display for Functional button panel

'''

class MainCockpit(QMainWindow):
    """
    Screen 3: Main Administration Cockpit Dashboard.
    The primary hub for server telemetry and command execution.
    """
    def __init__(self):
        super().__init__()

        # --- Dashboard Configuration ---
        self.setWindowTitle("Zero-G Admin Helper - Main Cockpit")
        self.setFixedSize(1280, 900)

        # --- Style Application ---
        try:
            with open("assets/ZAH.css", "r") as f:
                self.setStyleSheet(f.read())
            print(f"[SUCCESS] ZAH.css fully integrated.")
        except FileNotFoundError:
            print("[WARNING] ZAH.css not found. Skipping theme application.")
            # Fallback Glassmorphism Styling so the background is visible
            # Note: This is an emergency fallback. Primary styling is handled in ZAH.css.
            self.setStyleSheet("""
                QFrame { background-color: rgba(15, 25, 35, 180); border: 1px solid #00d4ff; border-radius: 5px; }
                QLabel { background-color: transparent; border: none; color: #00d4ff; font-weight: bold; }
                QTextEdit, QTableWidget { background-color: rgba(10, 15, 25, 200); color: #e0e0e0; border: 1px solid #005577; }
                QHeaderView::section { background-color: rgba(20, 30, 45, 220); color: #00d4ff; }
                QPushButton { background-color: rgba(0, 85, 119, 150); color: #ffffff; border: 1px solid #00d4ff; }
                QPushButton:hover { background-color: rgba(0, 150, 200, 200); }
            """)
        self.setFixedSize(1280, 900)

        # --- Style Application ---
        try:
            with open("assets/ZAH.css", "r") as f:
                self.setStyleSheet(f.read())
            print(f"[SUCCESS] ZAH.css fully integrated.")
        except FileNotFoundError:
            print("[WARNING] ZAH.css not found. Skipping theme application.")
            # Fallback Glassmorphism Styling so the background is visible
            # Note: This is an emergency fallback. Primary styling is handled in ZAH.css.
            self.setStyleSheet("""
                QFrame { background-color: rgba(15, 25, 35, 180); border: 1px solid #00d4ff; border-radius: 5px; }
                QLabel { background-color: transparent; border: none; color: #00d4ff; font-weight: bold; }
                QTextEdit, QTableWidget { background-color: rgba(10, 15, 25, 200); color: #e0e0e0; border: 1px solid #005577; }
                QHeaderView::section { background-color: rgba(20, 30, 45, 220); color: #00d4ff; }
                QPushButton { background-color: rgba(0, 85, 119, 150); color: #ffffff; border: 1px solid #00d4ff; }
                QPushButton:hover { background-color: rgba(0, 150, 200, 200); }
            """)
        
        # --- Central UI Canvas ---
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidgetCanvas")
        self.central_widget.setObjectName("CentralWidgetCanvas")
        self.setCentralWidget(self.central_widget)
        self.background = QPixmap("assets/backgrounds/background.png")
        self.background = QPixmap("assets/backgrounds/background.png")

        # --- Master Layout Definition ---
        self.master_layout = QHBoxLayout(self.central_widget)
        
        # INCREASED MARGINS: These push the widgets inward so they sit inside the drawn HUD lines.
        self.master_layout.setContentsMargins(65, 100, 65, 80) 
        self.master_layout.setSpacing(15)
        # --- Master Layout Definition ---
        self.master_layout = QHBoxLayout(self.central_widget)
        
        # INCREASED MARGINS: These push the widgets inward so they sit inside the drawn HUD lines.
        self.master_layout.setContentsMargins(65, 100, 65, 80) 
        self.master_layout.setSpacing(15)

        # 1. Grid Initialization        
        # 1. Grid Initialization        
        self.setup_zones()

        # 2. Start background telemetry threads
        # 2. Start background telemetry threads
        # --- Telemetry Engine Initialization ---
        self.telemetry_worker = TelemetryWorker()
        self.telemetry_worker.log_received.connect(self.update_console_output)
        
        self.telemetry_worker.connection_status.connect(self.update_server_status, QtCore.Qt.ConnectionType.QueuedConnection)
        self.telemetry_worker.start()
        
        # Initial log confirmation for registry sync
        print("[SUCCESS] Main Cockpit Dashboard initialized.")

        # 3. Load configurations and populate the UI Last
        self.load_network_config()

    def paintEvent(self, event):
        """Force the background image to render on the MainCockpit."""
        painter = QPainter(self)
        # Scale image to fit the window exactly
        scaled_bg = self.background.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
        painter.drawPixmap(0, 0, scaled_bg)
        painter.end()
    

        # 3. Load configurations and populate the UI Last
        self.load_network_config()

    def paintEvent(self, event):
        """Force the background image to render on the MainCockpit."""
        painter = QPainter(self)
        # Scale image to fit the window exactly
        scaled_bg = self.background.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
        painter.drawPixmap(0, 0, scaled_bg)
        painter.end()
    
    def setup_zones(self):
        """
        Constructs the UI zones using a primary Left Column (Communications) 
        and a Right Column (Telemetry, Players, Controls).
        """
        # =====================================================
        # LEFT COLUMN (approx 35%): Data Feed & Chat/Commands 
        # Handles all primary communication and log outputs.
        # =====================================================
        self.left_column = QVBoxLayout()
        """
        Constructs the UI zones using a primary Left Column (Communications) 
        and a Right Column (Telemetry, Players, Controls).
        """
        # =====================================================
        # LEFT COLUMN (approx 35%): Data Feed & Chat/Commands 
        # Handles all primary communication and log outputs.
        # =====================================================
        self.left_column = QVBoxLayout()

        # --- (6) Data Feed Panel Control ---
        # Dropdown menu to toggle the context of the main console panel.
        self.feed_selector = QComboBox()
        self.feed_selector.setObjectName("FeedSelector")
        self.feed_selector.addItems([
            "Global Live Feed Chat", 
            "Faction Live Feed Chat", 
            "Admin Command Console", 
            "Active Logs"
        ])
        self.left_column.addWidget(self.feed_selector)

        # --- (7) Display Panel for Data Feed ---
        # The large text area displaying live chat, logs, or admin feedback.
        # --- (6) Data Feed Panel Control ---
        # Dropdown menu to toggle the context of the main console panel.
        self.feed_selector = QComboBox()
        self.feed_selector.setObjectName("FeedSelector")
        self.feed_selector.addItems([
            "Global Live Feed Chat", 
            "Faction Live Feed Chat", 
            "Admin Command Console", 
            "Active Logs"
        ])
        self.left_column.addWidget(self.feed_selector)

        # --- (7) Display Panel for Data Feed ---
        # The large text area displaying live chat, logs, or admin feedback.
        self.console = QTextEdit()
        self.console.setObjectName("ConsoleDisplay")
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Data stream initializing...")
        self.left_column.addWidget(self.console, stretch=1)

        # --- (8) Chat/Command Input Area ---
        # Text entry line and execution button for sending inputs to the server.
        self.input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setObjectName("CommandInput")
        self.cmd_input.setPlaceholderText("Enter Chat or Admin Command...")
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("ExecuteButton")
        
        self.input_layout.addWidget(self.cmd_input, stretch=4)
        self.input_layout.addWidget(self.execute_btn, stretch=1)
        self.left_column.addLayout(self.input_layout)

        # Add Left Column to Master Layout
        self.master_layout.addLayout(self.left_column, stretch=35)


        # =====================================================
        # RIGHT COLUMN (approx 65%): Telemetry, Players, Controls
        # Handles dynamic data viewing, server health, and interactive control matrices.
        # =====================================================
        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(15)
        self.console.setPlaceholderText("Data stream initializing...")
        self.left_column.addWidget(self.console, stretch=1)

        # --- (8) Chat/Command Input Area ---
        # Text entry line and execution button for sending inputs to the server.
        self.input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setObjectName("CommandInput")
        self.cmd_input.setPlaceholderText("Enter Chat or Admin Command...")
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("ExecuteButton")
        
        self.input_layout.addWidget(self.cmd_input, stretch=4)
        self.input_layout.addWidget(self.execute_btn, stretch=1)
        self.left_column.addLayout(self.input_layout)

        # Add Left Column to Master Layout
        self.master_layout.addLayout(self.left_column, stretch=35)


        # =====================================================
        # RIGHT COLUMN (approx 65%): Telemetry, Players, Controls
        # Handles dynamic data viewing, server health, and interactive control matrices.
        # =====================================================
        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(15)

        # --- TOP SECTION: Telemetry Grid (Panels 2, 3, 4, 5) ---
        # Displays core server health metrics and connection details.
        self.telemetry_frame = QFrame()
        self.telemetry_frame.setObjectName("TelemetryPanel")
        self.telemetry_layout = QGridLayout(self.telemetry_frame)
        self.telemetry_layout.setContentsMargins(10, 10, 10, 10)
        
        self.lbl_target_ip = QLabel("Target IP: Loading...")
        self.lbl_server_status = QLabel("Server Status: DETECTING....")
        self.lbl_cpu_usage = QLabel("CPU: 0%")
        self.lbl_ram_usage = QLabel("RAM: 0%")

        self.telemetry_layout.addWidget(self.lbl_target_ip, 0, 0, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.telemetry_layout.addWidget(self.lbl_server_status, 0, 1, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.telemetry_layout.addWidget(self.lbl_cpu_usage, 1, 0)
        self.telemetry_layout.addWidget(self.lbl_ram_usage, 1, 1)
        
        self.right_column.addWidget(self.telemetry_frame, stretch=1)

        # --- MIDDLE SECTION: Players (9,10) AND Matrix (11) Side-by-Side ---
        # A horizontal split dividing the player registry and the functional button matrix.
        self.mid_row_layout = QHBoxLayout()

        # Left Side of Mid Row: Player Registry Grid
        self.player_registry = QFrame()
        self.player_registry.setObjectName("PlayerRegistry")
        self.players_layout = QVBoxLayout(self.player_registry)
        
        self.lbl_players_header = QLabel("Players on Server")
        self.lbl_players_header.setObjectName("HeaderLabel")
        
        self.player_table = QTableWidget(0, 5)
        self.player_table.setObjectName("PlayerRegistryTable")
        self.player_table.setHorizontalHeaderLabels(["Player", "Status", "Faction", "System", "Playfield"])
        self.player_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.player_table.verticalHeader().setVisible(False) # Hides the default row numbers
        
        self.players_layout.addWidget(self.lbl_players_header)
        self.players_layout.addWidget(self.player_table)
        self.mid_row_layout.addWidget(self.player_registry, stretch=1)

        # Right Side of Mid Row: Functional Button Panel Control Grid
        self.control_panel = QFrame()
        self.control_panel.setObjectName("ControlPanel")
        self.button_grid = QGridLayout(self.control_panel)
        self.button_grid.setContentsMargins(5, 5, 5, 5)
        
        self.matrix_buttons = []
        # Generate a 3x6 grid of generic buttons dynamically
        for row in range(3):
            for col in range(6):
                btn = QPushButton(f"[{row},{col}]")
                btn.setObjectName("MatrixButton")
                btn.setSizePolicy(btn.sizePolicy().Policy.Expanding, btn.sizePolicy().Policy.Expanding)
                self.button_grid.addWidget(btn, row, col)
                self.matrix_buttons.append(btn)
                
        self.mid_row_layout.addWidget(self.control_panel, stretch=1)
        
        # Add the mid-row block to the right column
        self.right_column.addLayout(self.mid_row_layout, stretch=3)


        # --- BOTTOM SECTION: Dynamic Displays (12 & 13) Side-by-Side ---
        # Dual stacked widgets allowing interchangeable UI pages without opening new windows.
        self.bottom_row_layout = QHBoxLayout()

        # Dynamic Display Area A
        self.display_fbp = QFrame()
        self.display_fbp.setObjectName("DynamicDisplayA")
        self.layout_fbp = QVBoxLayout(self.display_fbp)
        self.dynamic_display_fbp = QStackedWidget()
        
        fbp1 = QLabel("Functional Button Display")
        fbp1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dynamic_display_fbp.addWidget(fbp1)
        self.layout_fbp.addWidget(self.dynamic_display_fbp)
        
        self.bottom_row_layout.addWidget(self.display_fbp, stretch=1)

        # Add the bottom-row block to the right column
        self.right_column.addLayout(self.bottom_row_layout, stretch=3)

        # Finally, attach the entire Right Column to the Master Layout
        self.master_layout.addLayout(self.right_column, stretch=65)

        print("[SUCCESS] Main Cockpit grid initialized.")
        pass

    def update_console_output(self, log_line):
        """Slot to receive signal from worker and update UI."""
        self.console.append(log_line)

    def load_network_config(self):
        """Loads saved server connection profiles and populates telemetry labels."""
        try:
            config_path = os.path.abspath("data/server_config.json")
            print(f"[DEBUG] Cockpit attempting to read: {config_path}")

            with open(config_path, "r") as f:
                config_data = json.load(f)

            # Print the raw dictionary to terminal to expose any key mismatches
            print(f"[DEBUG] Cockpit loaded dictionary: {config_data}")
                
            # Extract target connection parameters
            saved_ip = config_data.get("input_ip", "127.0.0.1")
            saved_port = config_data.get("input_port", "30000")
            
            # Dynamically update the telemetry label string
            self.lbl_target_ip.setText(f"Target IP: {saved_ip}:{saved_port}")
            print(f"[SUCCESS] Loaded connection profile: {saved_ip}:{saved_port}")
            
        except FileNotFoundError:
            print("[WARNING] server_config.json profile not found. Defaulting to local loopback telemetry.")
            # FIX: Replace the invalid '{saved_ip}' reference with a hardcoded fallback string.
            self.lbl_target_ip.setText("Target IP: UNKNOWN (Config Missing)")
            
        except json.JSONDecodeError:
            print("[ERROR] server_config.json is corrupted. Verification failed.")
            self.lbl_target_ip.setText("Target IP: ERROR")

    def update_server_status(self, is_online):
        """Updates the status label based on telemetry stream health."""
        if is_online:
            self.lbl_server_status.setText("Server Status: ONLINE")
            self.lbl_server_status.setStyleSheet("color: #00FF00; font-weight: bold;")
        else:
            self.lbl_server_status.setText("Server Status: OFFLINE")
            self.lbl_server_status.setStyleSheet("color: #FF0000; font-weight: bold;")


    def closeEvent(self, event):
        """Standardized, safe shutdown sequence."""
        print("[STATUS] Shutdown signal received. Closing telemetry worker...")
        
        # 1. Flag the worker to terminate
        self.telemetry_worker.isRunning = False
        
        # 2. Force socket shutdown to break the blocking recv()
        if hasattr(self.telemetry_worker, 'socket') and self.telemetry_worker.socket:
            try:
                self.telemetry_worker.socket.shutdown(socket.SHUT_RDWR)
                self.telemetry_worker.socket.close()
            except Exception as e:
                print(f"[DEBUG] Socket already closed: {e}")

        # 3. Request quit and WAIT for actual termination
        self.telemetry_worker.quit()
        self.telemetry_worker.wait(1) # Wait for less than 1 second before force-closing.
        print("[WARNING] Telemetry worker was forced into termination.")
        
        event.accept()
        print("[SUCCESS] Cockpit closed successfully.")


# Kept for continuity, though its contents are currently integrated directly into the new Telemetry frame
class TelemetryPanel(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.layout = QVBoxLayout(self)
        
        # Panel Title
        self.title_label = QLabel(title)
        self.layout.addWidget(self.title_label)
        
        # Telemetry Data Placeholder
        self.data_label = QLabel("INITIALIZING...")
        self.layout.addWidget(self.data_label)