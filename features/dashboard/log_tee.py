# log_tee.py

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
            self.terminal.write(text)
            self.terminal.flush()
            
            # Process text chunk for the GUI console view
            if text:
                # Split multi-line blocks so each line hits the signal independently
                for line in text.splitlines():
                    cleaned_line = line.strip()
                    if cleaned_line:
                        if not any(tag in cleaned_line for tag in ["[TRACE]", "[DEBUG] Line parsed"]):
                            formatted_line = f"[LOG] {cleaned_line}\n"
                            self.new_log.emit(formatted_line)
        finally:
            self._is_writing = False

    def flush(self):
        self.terminal.flush()