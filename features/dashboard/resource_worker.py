import os
import psutil
import time
from PyQt6.QtCore import QThread, pyqtSignal

class ResourcePollingWorker(QThread):
    signal_resources_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.is_running = True

    def run(self):
        process = psutil.Process(os.getpid())
        while self.is_running:
            # Using interval=None for non-blocking
            cpu_usage = process.cpu_percent(interval=None)
            ram_usage = process.memory_percent()
            resources = {
                "cpu": cpu_usage,
                "ram": ram_usage
            }
            self.signal_resources_received.emit(resources)
            time.sleep(4)

    def stop(self):
        self.is_running = False
        self.wait()