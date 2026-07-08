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
            re.compile(r"aborted"),
            re.compile(r"\.\)"),           # ADDED: Block Empyrion weird dot-parenthesis output
            re.compile(r"\{EPM\}")         # ADDED: Block Empyrion Playfield Manager tool spam
        ]
        
        self.patterns = {
            "uptime": re.compile(r"Uptime=(?P<time>[a-zA-Z0-9\s]+)"),
            "global_chat": re.compile(r"^.*?\[Chat\]\s+'(?P<player>[^']+)'\:\s(?P<message>.*)$"),
            "faction_chat": re.compile(r"^.*?\[Chat\]\s+\((?P<faction>[A-Za-z0-9]{3,4})\)\s+'(?P<player>[^']+)'\:\s(?P<message>.*)$"),
            "system_metric": re.compile(r"(?P<metric>fps|heap|players)=(?P<value>[^\s,\)]+)", re.IGNORECASE)
        }

    def parse(self, line):
        # 1. Noise Filter: Drop junk immediately
        if any(pattern.search(line) for pattern in self.noise_filters):
            return "NOISE", None

        # 2. Priority Parsing: Faction Chat (Must be checked BEFORE Global Chat to avoid overlapping match traps)
        global_match = self.patterns["global_chat"].search(line)
        if global_match:
            data = global_match.groupdict()
            return "GLOBAL_CHAT", {
                "player": data["player"].strip(),
                "message": data["message"].strip()
            }
        faction_match = self.patterns["faction_chat"].search(line)
        if faction_match:
            # Use .groupdict() to safely extract ALL captured entities at once
            data = faction_match.groupdict()
            return "FACTION_CHAT", {
                "faction": data["faction"].strip(),
                "player": data["player"].strip(),
                "message": data["message"].strip()
            }

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
