import re

class TelemetryParser:
    """Stateless parser for Empyrion server log lines."""
    
    def __init__(self):
        # Compiled regex patterns updated to match actual log output
        # Added \s* to handle potential whitespace after the '='
        self.patterns = {
            "fps": re.compile(r"fps=([\d.]+)"),
            "heap": re.compile(r"heap=\s*(\d+)MB"),
            "players": re.compile(r"players=\s*(\d+)"), 
            "uptime": re.compile(r"Uptime=([\whm]+)")
        }

    def parse(self, line):
        """Processes a raw line and returns a dict of found metrics."""
        metrics = {}
        for key, pattern in self.patterns.items():
            match = pattern.search(line)
            if match:
                metrics[key] = match.group(1)
        return metrics