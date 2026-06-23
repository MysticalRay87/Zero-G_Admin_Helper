import json
from PyQt6.QtWidgets import QMainWindow, QWidget, QGridLayout, QFrame, QLabel, QVBoxLayout, QTextEdit
from PyQt6.QtCore import Qt

from features.dashboard.telemetry_worker import TelemetryWorker

class MainCockpit(QMainWindow):
    """
    Screen 3: Main Administration Cockpit Dashboard.
    The primary hub for server telemetry and command execution.
    """
    def __init__(self):
        super().__init__()

        # --- Dashboard Configuration ---
        self.setWindowTitle("Zero-G Admin Helper - Main Cockpit")
        self.setFixedSize(1000, 750)
        
        # --- Central UI Canvas ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # --- Grid Layout Definition ---
        self.grid = QGridLayout(self.central_widget)
        self.grid.setContentsMargins( 10, 10, 10, 10)
        self.grid.setSpacing(10)

        # Grid Initialization        
        self.setup_zones()

        # Console output widget
        self.console = QTextEdit()
        self.console.setObjectName("ConsoleDisplay")
        self.console.setReadOnly(True)
        self.console_layout.addWidget(self.console)

        # --- Telemetry Engine Initialization ---
        self.telemetry_worker = TelemetryWorker()
        self.telemetry_worker.log_received.connect(self.update_console_output)
        self.telemetry_worker.start()
        
        # Initial log confirmation for registry sync
        print("[SUCCESS] Main Cockpit Dashboard initialized.")

    def setup_zones(self):
        
        # -----------------------------------------------------
        # Zone A (Header/Status): Row 0, Col 0 (Spans 3). Holds your User, Status, CPU, and RAM metrics.
        # -----------------------------------------------------
        self.telemetry_panel = TelemetryPanel("SYSTEM LOAD")
        self.telemetry_panel.setObjectName("TelemetryPanel")
        self.grid.addWidget(self.telemetry_panel, 0, 0, 1, 1)

        # -----------------------------------------------------
        # Zone B (Telemetry/IP): Row 1, Col 0. IP + Telemetry/Data Feeds.
        # -----------------------------------------------------
        self.console_frame = QFrame()
        self.console_frame.setObjectName("ConsoleFrame")
        
        # Assign to self so it is available to the entire class instance
        self.console_layout = QVBoxLayout(self.console_frame)
        
        self.console = QTextEdit()
        self.console.setObjectName("ConsoleDisplay")
        self.console.setReadOnly(True)
        self.console_layout.addWidget(self.console)
        
        # Add to grid
        self.grid.addWidget(self.console_frame, 2, 0, 1, 3)

        # -----------------------------------------------------
        # Zone C (Player Registry): Row 1, Col 1. The player list table.
        # -----------------------------------------------------

        # -----------------------------------------------------
        # Zone D (Functional Panel): Row 1, Col 2. Control buttons.
        # -----------------------------------------------------

        # -----------------------------------------------------
        # Zone E (Command Console): Row 2, Col 0 (Spans 3). Your terminal input.
        # -----------------------------------------------------

        print("[SUCCESS] Main Cockpit grid initialized.")
        pass

    def update_console_output(self, log_line):
        """Slot to receive signal from worker and update UI."""
        self.console.append(log_line)

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
        print("[WARNING] Telemetry worker forced termination.")
        
        event.accept()
        print("[SUCCESS] Cockpit closed successfully.")


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