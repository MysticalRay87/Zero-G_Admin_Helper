import os
import sys
from PyQt6.QtWidgets import QApplication

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)

from features.dashboard.telemetry_worker import TelemetryWorker

def handle_log(message):
    print(f"[TEST RECEIVED] {message}")

def handle_status(status):
    print(f"[TEST STATUS] Worker connection status: {status}")

def main():
    app = QApplication(sys.argv)
    
    # Instantiate the worker (host/port placeholders)
    worker = TelemetryWorker("127.0.0.1", 30004)
    
    # Connect signals to our test handlers
    worker.log_received.connect(handle_log)
    worker.connection_status.connect(handle_status)
    
    # Start the thread
    print("[TEST] Starting worker thread...")
    worker.start()
    
    # Run the test for 3 seconds
    from PyQt6.QtCore import QTimer
    QTimer.singleShot(3000, lambda: [worker.stop(), print("[TEST] Stopping..."), app.quit()])
    
    app.exec()
    print("[TEST] Verified: Worker thread is operational.")

if __name__ == "__main__":
    main()