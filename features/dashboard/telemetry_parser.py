import re

class TelemetryParser:
    """Stateless parser for Empyrion server log lines."""
    
    def __init__(self):
        # Define noise patterns that trigger server-side mod crashes or metadata junk
        self.noise_filters = [
            re.compile(r"System\.Reflection\.TargetInvocationException"),
            re.compile(r"NullReferenceException"),
            re.compile(r"EmpyrionChatDiscordBridge"),
            re.compile(r"EmpyrionModHost"),
            re.compile(r"at System\."), 
            re.compile(r"Thread 'TelnetClient"),
            re.compile(r"Telnet Connection closed"),
            re.compile(r"transport connection"),     # ADD THIS: Broadens the catch for socket aborts
            re.compile(r"aborted by the software"),   # ADD THIS: Specifically targets the host machine aborts
            re.compile(r"aborted"),
            re.compile(r"\.\)"),           # ADDED: Block Empyrion weird dot-parenthesis output
            re.compile(r"\{EPM\}")         # ADDED: Block Empyrion Playfield Manager tool spam
        ]
        
        self.patterns = {
            "uptime": re.compile(r"Uptime=(?P<time>[a-zA-Z0-9\s]+)"),
            
            # Updated to look for text inside parentheses for the faction group
            "global_chat": re.compile(r"CHAT ServerForward/Global.*? \((?P<player>.*?)\):\s*'(?P<message>.*?)'"),
            
            # Updated pattern: Matches "CHAT ServerForward/Faction from ... (Faction) ... (Player)"
            # This uses a non-greedy match to find the parenthetical faction tag
            "faction_chat": re.compile(r"CHAT ServerForward/Faction.*? \((?P<player>.*?)\):\s*'(?P<message>.*?)'"),
            
            "system_metric": re.compile(r"(?P<metric>fps|heap|players)=(?P<value>[^\s,\)]+)", re.IGNORECASE)
        }

    def parse(self, line):
        # 1. Noise Filter: Drop junk immediately
        if any(pattern.search(line) for pattern in self.noise_filters):
            return "NOISE", None

        # 2. Priority Parsing: Faction Chat (Must be checked BEFORE Global Chat to avoid overlapping match traps)
        faction_match = self.patterns["faction_chat"].search(line)
        if faction_match:
            try:
                data = faction_match.groupdict()
                return "FACTION_CHAT", {
                    "faction": "N/A",
                    "player": data["player"].strip(),
                    "message": data["message"].strip()
                }
            except KeyError as e:
                # If a group is missing, log the error instead of crashing the thread
                print(f"[ERROR] Faction Chat Parsing Error: Missing group {e}")
                return "NOISE", None
            
        global_match = self.patterns["global_chat"].search(line)
        if global_match:
            try:
                data = global_match.groupdict()
                return "GLOBAL_CHAT", {
                    "player": data["player"].strip(),
                    "message": data["message"].strip()
                }
            except KeyError as e:
                # If a group is missing, log the error instead of crashing the thread
                print(f"[ERROR] Global Chat Parsing Error: Missing group {e}")
                return "NOISE", None

        # 3. High-Performance Metric Harvesting
        metrics = {}
        
        # Fast, single-pass evaluation across unified metrics strings
        metric_matches = list(self.patterns["system_metric"].finditer(line))
        if metric_matches:
            for match in metric_matches:
                metrics[match.group("metric").lower()] = match.group("value").strip()
        
        # Check Uptime separately since it doesn't match the standard telemetry signature
        uptime_match = self.patterns["uptime"].search(line)
        if uptime_match:
            metrics["uptime"] = uptime_match.group("time").strip()

        if metrics:
            return "METRIC", metrics

        # 4. Fallback for unparsed but non-noisy lines
        return "OTHER", line.strip()
