# command_pipe.py

import queue
from PyQt6.QtCore import QThread, pyqtSignal

class CommandPipe(QThread):
    pipe_error = pyqtSignal(str)
    status_msg = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Queue remains for thread-safe command buffering
        self.cmd_queue = queue.Queue()
        self.is_running = False
        # Proxy reference to the master connection authority
        self.telemetry_authority = None

    def run(self):
        """
        [NEW LOGIC]
        Processes queued commands and delegates to telemetry_authority.
        """
        self.is_running = True
        
        while self.is_running:
            try:
                # Wait for command in queue; block for 1 second for shutdown safety
                cmd_text = self.cmd_queue.get(timeout=1.0)
                
                # Check for authority injection and command presence
                if cmd_text and self.telemetry_authority:
                    # Route command to the master thread via established connection
                    self.telemetry_authority.write_command(cmd_text)
                    self.cmd_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.pipe_error.emit(f"Command routing failure: {e}")

    def set_telemetry_authority(self, worker):
        """
        [NEW METHOD]
        Links the CommandPipe to the TelemetryWorker instance.
        """
        self.telemetry_authority = worker

    def send_command(self, cmd_text):
        """
        [RESTORED METHOD]
        Public API method for UI buttons to queue an admin action text payload.
        The command is placed into the thread-safe FIFO queue.
        """
        if cmd_text:
            print(f"[DEBUG] CommandPipe: Enqueueing command: {cmd_text.strip()}")
            self.cmd_queue.put(cmd_text)