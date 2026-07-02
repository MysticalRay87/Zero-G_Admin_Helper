import os
import json
import socket 
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QFrame, QLabel, QVBoxLayout, 
    QTextEdit, QHBoxLayout, QComboBox, QLineEdit, QPushButton, 
    QTableWidget, QHeaderView, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPixmap

from features.dashboard.telemetry_worker import TelemetryWorker

class TelemetryWidget(QFrame):
    """
    Standalone high-density sub-panel managing server health metrics.
    Abstracted component for precision placement inside header controls.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TelemetryPanel")
        self.setFixedSize(330, 70)  # Strict dimensional boundary control
        self.setStyleSheet("""
            QFrame#TelemetryPanel {
                background-color: rgba(10, 15, 25, 140);
                border: 1px solid #005577;
                border-radius: 4px;
            }
            QLabel {
                font-size: 11px;  /* Highly compressed font footprint */
                color: #e0e0e0;
                background: transparent;
                border: none;
            }
        """)

        # Micro sub-grid coordinates mapped inside the shrunk layout structure
        self.telemetry_layout = QGridLayout(self)
        self.telemetry_layout.setContentsMargins(6, 4, 6, 4)
        self.telemetry_layout.setSpacing(4)

        # --- Upper Telemetry Matrix Elements ---
        self.lbl_target_ip = QLabel("Target IP: Loading...", self)
        self.lbl_server_status = QLabel("Server Status: DETECTING....", self)
        self.telemetry_layout.addWidget(self.lbl_target_ip, 0, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.telemetry_layout.addWidget(self.lbl_server_status, 0, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # --- Lower Telemetry Matrix Elements ---
        self.lbl_server_cpu = QLabel("CPU: --%", self)
        self.lbl_server_ram = QLabel("RAM: --%", self)
        self.telemetry_layout.addWidget(self.lbl_server_cpu, 1, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.telemetry_layout.addWidget(self.lbl_server_ram, 1, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        # --- Dynamic Log Metrics Ingestion Elements ---
        self.lbl_fps = QLabel("FPS: --", self)
        self.lbl_heap = QLabel("Heap: --", self)
        self.lbl_players = QLabel("Players: --", self)
        self.lbl_uptime = QLabel("Uptime: --", self)
        
        self.telemetry_layout.addWidget(self.lbl_fps, 2, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.telemetry_layout.addWidget(self.lbl_heap, 2, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.telemetry_layout.addWidget(self.lbl_players, 3, 0, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        self.telemetry_layout.addWidget(self.lbl_uptime, 3, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)


class MainCockpit(QMainWindow):
    """
    Screen 3: Main Administration Cockpit Dashboard.
    Persistent multi-threaded dashboard featuring a fluid layout-retaining data feed engine.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("MainCockpitCanvas")

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
        self.setCentralWidget(self.central_widget)
        self.background = QPixmap("assets/backgrounds/background.png")

        # --- Master Layout Definition ---
        self.master_layout = QHBoxLayout()
        self.master_layout.setContentsMargins(90, 205, 90, 95) 
        self.master_layout.setSpacing(15)
        self.central_widget.setLayout(self.master_layout)

        # --- Core Standalone Telemetry Component Allocation ---
        self.telemetry_widget = TelemetryWidget(self)
        self.telemetry_widget.move(850, 120)
        self.telemetry_widget.show()

        # 1. Grid Layout Construction
        self.setup_zones()

        # 2. Asynchronous Thread Operations
        self.telemetry_worker = TelemetryWorker()
        self.telemetry_worker.log_received.connect(self.update_console_output)
        self.telemetry_worker.connection_status.connect(self.update_server_status, QtCore.Qt.ConnectionType.QueuedConnection)
        
        # Connect the new structured telemetry signal
        self.telemetry_worker.signal_data_received.connect(self.update_telemetry_ui)
        
        self.telemetry_worker.start()
        
        print("[SUCCESS] Main Cockpit Dashboard initialized.")

        # 3. Dynamic Configuration Loading
        self.load_network_config()

    def paintEvent(self, event):
        """Force background canvas visualization mapping."""
        painter = QPainter(self)
        if not self.background.isNull():
            scaled_bg = self.background.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
            painter.drawPixmap(0, 0, scaled_bg)
        painter.end()
    
    def setup_zones(self):
        """
        Constructs Left Column (Communications Core via Card Stack) 
        and Right Column (Metrics & Matrices).
        """
        # =====================================================
        # TOP SYSTEM ROW: Unified Header Strip
        # =====================================================
        self.top_header_layout = QHBoxLayout()
        self.top_header_layout.setContentsMargins(10, 0, 10, 10)

        # Push the upcoming metrics box completely to the right side next to the words
        self.top_header_layout.addStretch()

        # =====================================================
        # LEFT COLUMN (35%): Stacked Communications Engine
        # =====================================================
        self.left_column = QVBoxLayout()

        # --- (6) Data Feed Panel Control Dropdown ---
        self.feed_selector = QComboBox()
        self.feed_selector.setObjectName("FeedSelector")
        self.feed_selector.addItems([
            "Global Live Feed Chat", 
            "Faction Live Feed Chat", 
            "Admin Command Console", 
            "Active Logs"
        ])
        self.feed_selector.currentTextChanged.connect(self.toggle_console_visibility)
        self.left_column.addWidget(self.feed_selector)

        # --- (7) Multi-Layer Display Card Deck Stack ---
        self.feed_stack = QStackedWidget()
        self.feed_stack.setObjectName("FeedStack")

        # Card 0: Global Chat display container box
        self.global_chat_box = QTextEdit()
        self.global_chat_box.setReadOnly(True)
        self.global_chat_box.setPlaceholderText("Global communication feeds stand by...")
        
        # Card 1: Faction Chat display container box
        self.faction_chat_box = QTextEdit()
        self.faction_chat_box.setReadOnly(True)
        self.faction_chat_box.setPlaceholderText("Faction communication feeds stand by...")

        # Card 2: Dedicated Admin Command Terminal display frame
        self.console = QTextEdit()
        self.console.setObjectName("ConsoleDisplay")
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Data stream initializing...")

        # Card 3: System Logs display container box
        self.system_logs_box = QTextEdit()
        self.system_logs_box.setReadOnly(True)
        self.system_logs_box.setPlaceholderText("System diagnostic records stand by...")

        # Mount layouts down onto card index rails
        self.feed_stack.addWidget(self.global_chat_box) # Index 0
        self.feed_stack.addWidget(self.faction_chat_box) # Index 1
        self.feed_stack.addWidget(self.console)          # Index 2
        self.feed_stack.addWidget(self.system_logs_box) # Index 3

        # Add Stack to column without collapsing space layout rules
        self.left_column.addWidget(self.feed_stack, stretch=1)

        # --- (8) Input Submission Field Panel ---
        self.input_layout = QHBoxLayout()
        self.cmd_input = QLineEdit()
        self.cmd_input.setObjectName("CommandInput")
        self.cmd_input.setPlaceholderText("Enter Chat or Admin Command...")
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("ExecuteButton")
        
        self.input_layout.addWidget(self.cmd_input, stretch=4)
        self.input_layout.addWidget(self.execute_btn, stretch=1)
        self.left_column.addLayout(self.input_layout)

        # =====================================================
        # RIGHT COLUMN (65%): Metrics & Matrices
        # =====================================================
        self.right_column = QVBoxLayout()
        self.right_column.setSpacing(15)

        # --- Player Matrix & Macros Mid Section ---
        self.mid_row_layout = QHBoxLayout()

        self.player_registry = QFrame()
        self.player_registry.setObjectName("PlayerRegistry")
        self.players_layout = QVBoxLayout(self.player_registry)
        
        self.lbl_players_header = QLabel("Players on Server")
        self.lbl_players_header.setObjectName("HeaderLabel")
        
        self.player_table = QTableWidget(0, 5)
        self.player_table.setObjectName("PlayerRegistryTable")
        self.player_table.setHorizontalHeaderLabels(["Player", "Status", "Faction", "System", "Playfield"])
        self.player_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.player_table.verticalHeader().setVisible(False)
        
        self.players_layout.addWidget(self.lbl_players_header)
        self.players_layout.addWidget(self.player_table)
        self.mid_row_layout.addWidget(self.player_registry, stretch=1)

        self.control_panel = QFrame()
        self.control_panel.setObjectName("ControlPanel")
        self.button_grid = QGridLayout(self.control_panel)
        self.button_grid.setContentsMargins(5, 5, 5, 5)
        
        self.matrix_buttons = []
        for row in range(3):
            for col in range(6):
                btn = QPushButton(f"[{row},{col}]")
                btn.setObjectName("MatrixButton")
                btn.setSizePolicy(btn.sizePolicy().Policy.Expanding, btn.sizePolicy().Policy.Expanding)
                self.button_grid.addWidget(btn, row, col)
                self.matrix_buttons.append(btn)
                
        self.mid_row_layout.addWidget(self.control_panel, stretch=1)
        self.right_column.addLayout(self.mid_row_layout, stretch=3)

        # --- Dynamic Stacked Sub-Panels Section Lower Row ---
        self.bottom_row_layout = QHBoxLayout()

        self.display_fbp = QFrame()
        self.display_fbp.setObjectName("DynamicDisplayA")
        self.layout_fbp = QVBoxLayout(self.display_fbp)
        self.dynamic_display_fbp = QStackedWidget()
        
        fbp1 = QLabel("Functional Button Display")
        fbp1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.dynamic_display_fbp.addWidget(fbp1)
        self.layout_fbp.addWidget(self.dynamic_display_fbp)
        
        self.bottom_row_layout.addWidget(self.display_fbp, stretch=1)
        self.right_column.addLayout(self.bottom_row_layout, stretch=3)

        # =====================================================
        # CANVAS CONSOLIDATION ASSEMBLY
        # =====================================================
        # Build the dynamic grid layout split content row
        self.content_columns_layout = QHBoxLayout()
        self.content_columns_layout.addLayout(self.left_column, stretch=35)
        self.content_columns_layout.addLayout(self.right_column, stretch=65)

        # Repackage the master layout vertically: Header Row on top, Content Columns underneath
        self.master_vertical_layout = QVBoxLayout()
        self.master_vertical_layout.addLayout(self.top_header_layout)
        self.master_vertical_layout.addLayout(self.content_columns_layout)

        # Re-apply the combined layout parameters cleanly onto your central workspace
        self.master_layout.addLayout(self.master_vertical_layout)
        print("[SUCCESS] Main Cockpit grid initialized.")

    def toggle_console_visibility(self, selected_text):
        """Pivots active visible deck layers smoothly matching dropdown choices."""
        if selected_text == "Global Live Feed Chat":
            self.feed_stack.setCurrentIndex(0)
        elif selected_text == "Faction Live Feed Chat":
            self.feed_stack.setCurrentIndex(1)
        elif selected_text == "Admin Command Console":
            self.feed_stack.setCurrentIndex(2)
        elif selected_text == "Active Logs":
            self.feed_stack.setCurrentIndex(3)

    def update_console_output(self, data_text):
        """Directs logs safely onto your terminal frame."""
        if data_text:
            self.console.append(data_text.strip())

    def load_network_config(self):
        """Loads and applies the network configuration to the UI components."""
        config_path = "data/server_config.json"
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                ip = config.get("input_ip", "Unknown")
                
                # Update the label inside the new detached telemetry widget
                self.telemetry_widget.lbl_target_ip.setText(f"Target IP: {ip}")
        else:
            self.telemetry_widget.lbl_target_ip.setText("Target IP: Not Configured")

    def update_server_status(self, is_online):
        """Toggles real-time network presence alerts."""
        if is_online:
            self.telemetry_widget.lbl_server_status.setText("Server Status: ONLINE")
            self.telemetry_widget.lbl_server_status.setStyleSheet("color: #00FF00; font-weight: bold;")
        else:
            self.telemetry_widget.lbl_server_status.setText("Server Status: OFFLINE")
            self.telemetry_widget.lbl_server_status.setStyleSheet("color: #FF0000; font-weight: bold;")

    def update_telemetry_ui(self, data):
        """Processes the structured dictionary received from TelemetryWorker."""
        # DEBUG: Print the raw incoming data to terminal
        print(f"[DEBUG] Cockpit received: {data}")
        if 'fps' in data:
            self.telemetry_widget.lbl_fps.setText(f"FPS: {data['fps']}")
            self.telemetry_widget.lbl_fps.repaint() # Force UI refresh
        if 'players' in data:
            self.telemetry_widget.lbl_players.setText(f"Players: {data['players']}")
            self.telemetry_widget.lbl_players.repaint()
        if 'heap' in data:
            self.telemetry_widget.lbl_heap.setText(f"Heap: {data['heap']}MB")
            self.telemetry_widget.lbl_heap.repaint()
        if 'uptime' in data:
            self.telemetry_widget.lbl_uptime.setText(f"Uptime: {data['uptime']}")
            self.telemetry_widget.lbl_uptime.repaint()

    def closeEvent(self, event):
        """Gracefully signs off connection streams on escape requests."""
        print("[STATUS] Shutdown signal received. Closing telemetry worker and clearing cache files...")
        self.telemetry_worker.is_running = False
        
        if hasattr(self.telemetry_worker, 'socket') and self.telemetry_worker.socket:
            try:
                self.telemetry_worker.socket.shutdown(socket.SHUT_RDWR)
                self.telemetry_worker.socket.close()
            except Exception as e:
                print(f"[DEBUG] Socket already closed: {e}")

        self.telemetry_worker.quit()
        self.telemetry_worker.wait(1)
        print("[SUCCESS] Cockpit closed successfully.")

        from features.clear_pycache import clear_pycache

        # Execute the cleanup script
        try:
            clear_pycache('/mnt/Zero-G_Files/Zero-G_Admin_Helper')
        except Exception as e:
            print(f"[ERROR] Cleanup failed: {e}")
        
        # Accept the event to proceed with closing
        event.accept()