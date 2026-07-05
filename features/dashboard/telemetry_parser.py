import re

class TelemetryParser:
    """Stateless parser for Empyrion server log lines."""
    
    def __init__(self):
        # Compiled regex patterns for metrics and chat
        self.patterns = {
            "fps": re.compile(r"fps=([\d.]+)"),
            "heap": re.compile(r"heap=\s*(\d+)MB"),
            "players": re.compile(r"players=\s*(\d+)"), 
            "uptime": re.compile(r"Uptime=([\whm]+)"),
            "global_chat": re.compile(r"Global:\s*(.*)"),
            "faction_chat": re.compile(r"Faction:\s*(.*)"),
            "system_metric": re.compile(r"(fps|heap|players)=(\S+)")
        }

    def parse(self, line):
        """
        Parses a raw log line.
        Returns a tuple: (type, data)
        """
        # 1. Check for Chat (Highest Priority)
        global_match = self.patterns["global_chat"].search(line)
        if global_match:
            return "GLOBAL_CHAT", global_match.group(1).strip()
            
        faction_match = self.patterns["faction_chat"].search(line)
        if faction_match:
            return "FACTION_CHAT", faction_match.group(1).strip()

        # 2. Check for Metrics
        metrics = {}
        for key, pattern in self.patterns.items():
            if key in ["global_chat", "faction_chat", "system_metric"]:
                continue
            match = pattern.search(line)
            if match:
                metrics[key] = match.group(1)
        
        if metrics:
            return "METRIC", metrics
            
        return "OTHER", None