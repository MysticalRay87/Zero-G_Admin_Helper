import os
import json
import socket 
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QGridLayout, QFrame, QLabel, QVBoxLayout, 
    QTextEdit, QHBoxLayout, QComboBox, QLineEdit, QPushButton, 
    QTableWidget, QHeaderView, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QPixmap

from features.dashboard.telemetry_worker import TelemetryWorker
from features.dashboard.resource_worker import ResourcePollingWorker
from features.dashboard.command_pipe import CommandPipe

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
        
        self.telemetry_layout.addWidget(self.lbl_server_cpu, 1, 0)
        self.telemetry_layout.addWidget(self.lbl_server_ram, 1, 1)

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
    """ Screen 3: Main Administration Cockpit Dashboard.
    Persistent multi-threaded dashboard featuring a fluid layout-retaining data feed engine.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("MainCockpitCanvas")
        self.setWindowTitle("Zero-G Admin Helper - Dashboard")
        self.setFixedSize(1280, 900)

        # 1. --- Central UI Canvas ---
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidgetCanvas")
        self.setCentralWidget(self.central_widget)
        self.background = QPixmap("assets/backgrounds/background.png")

        # 2. --- Master Layout & Scaffolding ---
        self.master_layout = QHBoxLayout()
        self.master_layout.setContentsMargins(90, 205, 90, 95) 
        self.master_layout.setSpacing(15)
        self.central_widget.setLayout(self.master_layout)

        # 3. Grid Layout Construction (Must happen first to initialize self.feed_stack)
        self.setup_zones()

        # 4. --- Initialize Workers ---
        # TelemetryWorker acts as the master authority for the socket connection
        self.telemetry_worker = TelemetryWorker()
        
        # CommandPipe is initialized as a lightweight proxy
        self.command_pipe = CommandPipe()
        
        # Injection: Link the CommandPipe proxy to the TelemetryWorker master socket
        self.command_pipe.set_telemetry_authority(self.telemetry_worker)

        # 5. --- Data Structures ---       
        self.player_map = {} # { "3129": "Manta" }

        # 6. --- Signal Bridge Connections ---
        # Telemetry signal mapping (Using QueuedConnection ensures UI updates happen on main thread)
        self.telemetry_worker.log_received.connect(self.update_console)
        self.telemetry_worker.connection_status.connect(self.update_server_status, QtCore.Qt.ConnectionType.QueuedConnection)
        self.telemetry_worker.signal_metrics.connect(self.update_telemetry_ui)
        self.telemetry_worker.signal_player_join.connect(self.handle_player_join)


        # Chat routing with forced Queueing to prevent thread-safety issues during screen switching
        try:
            self.telemetry_worker.signal_global_chat.disconnect(self.handle_global_chat)
        except (TypeError, RuntimeError):
            pass
        self.telemetry_worker.signal_global_chat.connect(self.handle_global_chat, QtCore.Qt.ConnectionType.QueuedConnection)
        try:
            self.telemetry_worker.signal_faction_chat.disconnect(self.handle_faction_chat)
        except (TypeError, RuntimeError):
            pass
        self.telemetry_worker.signal_faction_chat.connect(self.handle_faction_chat, QtCore.Qt.ConnectionType.QueuedConnection)

        # CommandPipe signal mapping
        self.command_pipe.status_msg.connect(self.handle_console_response)

        # 7. --- Start Background Threads ---
        self.telemetry_worker.start()
        self.command_pipe.start()

        # 8. --- UI Components ---
        self.telemetry_widget = TelemetryWidget(self)
        self.telemetry_widget.move(850, 120)
        self.telemetry_widget.show()

        # 9. --- Initialize and Start Resource Poller ---
        self.resource_worker = ResourcePollingWorker()
        self.resource_worker.signal_resources_received.connect(self.update_resource_ui)
        self.resource_worker.start()

        # 10. --- Panel Binder ---
        self.global_chat_display = self.global_chat_box
        self.faction_chat_display = self.faction_chat_box

        # 11. --- Console Buffer Management ---
        self.is_first_login = True
        self.response_buffer = []
        self.flush_timer = QTimer()
        self.flush_timer.setSingleShot(True)
        self.flush_timer.timeout.connect(self._flush_console)

        # 12. --- Initialize themes ---
        self.apply_theme()
        
        print("[SUCCESS] Main Cockpit Dashboard initialized.")

        # 13. --- Dynamic Configuration Loading ---
        self.load_network_config()

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
        self.cmd_input.setPlaceholderText("Enter Chat Message or Admin Command...")
        
        self.execute_btn = QPushButton("Execute")
        self.execute_btn.setObjectName("ExecuteButton")
        self.execute_btn.clicked.connect(self.dispatch_cmd)
        self.cmd_input.returnPressed.connect(self.dispatch_cmd)
        
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

    # --- System UI & Styling ---

    def paintEvent(self, event):
        """Force background canvas visualization mapping."""
        painter = QPainter(self)
        if not self.background.isNull():
            scaled_bg = self.background.scaled(self.size(), Qt.AspectRatioMode.IgnoreAspectRatio)
            painter.drawPixmap(0, 0, scaled_bg)
        painter.end()

    def apply_theme(self):
        """Loads external CSS to keep Python code purely structural."""
        try:
            # Assumes main_cockpit.py is in features/dashboard/
            # Path goes: up to features/, up to root/
            css_path = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'ZAH.css')
            with open(css_path, "r") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print(f"[ERROR] Could not load stylesheet: {e}")

    def toggle_console_visibility(self, selected_text):
        """Pivots active visible deck layers smoothly matching dropdown choices."""
        mapping = {
            "Global Live Feed Chat": 0,
            "Faction Live Feed Chat": 1,
            "Admin Command Console": 2,
            "Active Logs": 3
        }
        idx = mapping.get(selected_text, 0)
        self.feed_stack.setCurrentIndex(idx)

        # Makes Input Control Context-aware
        active_indices = [0, 1, 2]
        is_active = idx in active_indices
        self.cmd_input.setVisible(is_active)
        self.execute_btn.setVisible(is_active)
    
    # --- Telemetry & Data Processing ---

    def update_server_status(self, is_online):
        """Toggles real-time network presence alerts."""
        if is_online:
            self.telemetry_widget.lbl_server_status.setText("Server Status: ONLINE")
            self.telemetry_widget.lbl_server_status.setStyleSheet("color: #00FF00; font-weight: bold;")
            self.command_pipe.set_telemetry_authority(self.telemetry_worker)
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

    def handle_player_join(self, data: dict):
        self.player_map[data['id']] = data['name']
        print(f"[DEBUG] Registered player {data['name']} with ID {data['id']}")

    def update_resource_ui(self, resources):
        # Defensive check: ensure resources is a valid dictionary
        if not isinstance(resources, dict):
            return

        # Use safe defaults and explicit float casting
        try:
            cpu_val = float(resources.get("cpu", 0.0))
            ram_val = float(resources.get("ram", 0.0))
        except (ValueError, TypeError):
            cpu_val = 0.0
            ram_val = 0.0

        # Apply to UI
        self.telemetry_widget.lbl_server_cpu.setText(f"CPU: {cpu_val:.2f}%")
        self.telemetry_widget.lbl_server_ram.setText(f"RAM: {ram_val:.1f}%")

    def update_console(self, text, is_outbound=False, is_banner=False):
        """Manager: Appends one atomic block at a time."""
               
        if is_banner:
            # Banner styling (lines after)
            self.console.append(text)
            self.console.append("-" * 40)
        else:
            # Command output styling
            prefix = "[OUT] " if is_outbound else ""
            self.console.append(f"{prefix}{text}")

    def _flush_console(self):
        """This runs once after data stops arriving, processing the block as one unit."""
        if not self.response_buffer:
            return
            
        full_block = "\n".join(self.response_buffer)
        self.response_buffer = [] # Clear for next event
        
        # Apply your filtering and formatting logic here
        self.update_console(full_block)

    # --- Chat Handler ---

    def switch_chat_tab(self, tab_index):
            """Switches the visible chat box using the stacked widget index."""
            self.chat_stack.setCurrentIndex(tab_index)

    def handle_global_chat(self, data: dict):
        print(f"[DEBUG] Handler Triggered. Data: {data}")
        
        # 1. Resolve identity: Use ID if available, otherwise fallback to the raw data
        player_id = data.get('id')
        display_name = self.player_map.get(player_id, data.get('player', 'Unknown'))
        
        # 2. Fallback: If map lookup fails, use the raw data (only if not a hyphen)
        if not display_name or display_name == "-":
            raw_player = data.get('player', 'Unknown')
            display_name = raw_player if raw_player != "-" else "System/Bridge"

        # 3. Cleanup for the UI
        if display_name == "-1":
            display_name = "System/Bridge"

         # Strip the color tag if it exists
        msg = data.get('message', '').replace('[c]', '')

        # Verify feed_stack exists
        if not hasattr(self, 'feed_stack'):
            print("[CRITICAL] self.feed_stack DOES NOT EXIST!")
            return
        
        print(f"[DEBUG] Global message appended: {msg}")

        if hasattr(self, 'global_chat_box'):
            self.global_chat_box.append(f"[GLOBAL] {display_name}: {msg}")
        
        # Auto-scroll
        sb = self.global_chat_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    def handle_faction_chat(self, data: dict):
        print(f"[DEBUG] Handler Triggered. Data: {data}")

        # Resolve identity: Use ID if available, otherwise fallback to the raw data
        player_id = data.get('id')
        display_name = self.player_map.get(player_id, data.get('player', 'Unknown'))

        # 2. Fallback: If map lookup fails, use the raw data (only if not a hyphen)
        if not display_name or display_name == "-":
            raw_player = data.get('player', 'Unknown')
            display_name = raw_player if raw_player != "-" else "System/Bridge"
        
        # Cleanup for the UI
        if display_name == "-1":
            display_name = "System/Bridge"
        
        # Strip the color tag if it exists
        msg = data.get('message', '').replace('[c]', '')

        # Verify feed_stack exists
        if not hasattr(self, 'feed_stack'):
            print("[CRITICAL] self.feed_stack DOES NOT EXIST!")
            return
        
        print(f"[DEBUG] Faction message appended: {msg}")

        if hasattr(self, 'faction_chat_box'):
            self.faction_chat_box.append(f"[FACTION] {display_name}: {msg}")
        
        # Auto-scroll
        sb = self.faction_chat_box.verticalScrollBar()
        sb.setValue(sb.maximum())

    # --- Command Execution ---

    def dispatch_cmd(self):
        """
        Controller: Connects the GUI Input Box to the CommandPipe Buffer.
        Context-aware: Automatically prepends the correct chat syntax based on the active tab.
        """
        text = self.cmd_input.text().strip()
        if not text:
            self.update_console("[SYSTEM] Empty command ignored.")
            return
        
        # Determine target based on the active QStackedWidget index (self.feed_stack)
        current_idx = self.feed_stack.currentIndex()
        
        if current_idx == 0:
            command = f"say '{text}'\n"
            ui_display = f"[GLOBAL] You: {text}"
            target_box = self.global_chat_box
        elif current_idx == 1:
            command = f"faction say '{text}'\n"
            ui_display = f"[FACTION] You: {text}"
            target_box = self.faction_chat_box
        elif current_idx == 2:
            command = f"{text}\n"
            ui_display = f"[CMD] {text}"
            target_box = self.console
        else:
            # Index 3: Logs (Read-only, maybe ignore or treat as raw)
            self.update_console("[SYSTEM] Cannot send messages to log viewer.")
            return
           
        # Queue for safe, throttled execution (500ms delay enforced by pipe)
        if hasattr(self, 'command_pipe'):
            self.command_pipe.send_command(command)
            target_box.append(ui_display) # Update UI locally
            self.cmd_input.clear()
        else:
            self.console.append("[ERROR] CommandPipe not initialized.")

    def handle_console_response(self, response):
        """
        The Master Gatekeeper.
        Dynamically strips login banners and network noise from CommandPipe responses
        without destroying raw command text formatting.
        """
        # Strict low-level system junk to block
        noise_triggers = [
            "Thread 'TelnetClient", "ManagedId", "ThreadId",
            "Unable to read", "Unable to write", "aborted", ".)",
            "Connected from", "Welcome to Empyrion"
        ]
        
        # Dedicated login banner lines to block
        banner_elements = [
            "Empyrion dedicated server", "Version:", "Port:", 
            "Mode:", "Playfield:", "Name:", "Game seed:"
        ]
        
        lines = response.splitlines()
        filtered_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
                
            # Drop low-level system thread noise
            if any(noise in stripped for noise in noise_triggers):
                continue
                
            # Drop the initial connection banner components
            if any(element in stripped for element in banner_elements):
                continue
                
            # If it passes the gate, we keep it exactly as-is
            filtered_lines.append(stripped)
            
        sanitized_block = "\n".join(filtered_lines)
        
        if sanitized_block:
            self.response_buffer.append(sanitized_block)
            self.flush_timer.start(50)

    # --- Error Handling ---

    def handle_pipe_error(self, err_msg):
        self.console.append(f"[ERROR] {err_msg}")
        self.is_first_login = True # Reset gate to allow next login message   

    # --- Network Handling ---

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

    # --- Close & Shutdown ---

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