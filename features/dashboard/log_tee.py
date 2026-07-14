import sys
from PyQt6.QtCore import QObject, pyqtSignal

class LogTee(QObject):
    new_log = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        # Use a private flag to prevent re-entrancy
        self._is_writing = False
        self.terminal = sys.__stdout__

    def write(self, text):
        if self._is_writing:
            return
        
        self._is_writing = True
        try:
            # Write to terminal once
            self.terminal.write(text)
            self.terminal.flush()
            
            # Emit to GUI
            if text.strip():
                self.new_log.emit(text.strip())
        finally:
            self._is_writing = False

    def flush(self):
        self.terminal.flush()