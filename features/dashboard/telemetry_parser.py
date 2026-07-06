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
            re.compile(r"at System\.") # Broad C# stack trace lines
        ]
        
        self.patterns = {
            "fps": re.compile(r"fps=([\d.]+)"),
            "heap": re.compile(r"heap=\s*(\d+)MB"),
            "players": re.compile(r"players=\s*(\d+)"), 
            "uptime": re.compile(r"Uptime=([\\whm]+)"),
            "global_chat": re.compile(r"CHAT Player/Global.*:\s*'(.*)'"),
            "faction_chat": re.compile(r"CHAT Player/Faction.*:\s*'(.*)'"),
            "system_metric": re.compile(r"(fps|heap|players)=(\S+)")
        }

    def parse(self, line):
        # 1. Noise Filter: Drop junk immediately
        if any(pattern.search(line) for pattern in self.noise_filters):
            return "NOISE", None
        
        # 2. Priority Parsing: Chat messages take precedence
        global_match = self.patterns["global_chat"].search(line)
        if global_match:
            return "GLOBAL_CHAT", global_match.group(1).strip()
            
        faction_match = self.patterns["faction_chat"].search(line)
        if faction_match:
            return "FACTION_CHAT", faction_match.group(1).strip()

        # 3. Aggregated Metric Parsing: Handle combined metric lines (if any)
        metrics = {}
        for key, pattern in self.patterns.items():
            if key in ["global_chat", "faction_chat", "system_metric"]:
                continue
            match = pattern.search(line)
            if match:
                metrics[key] = match.group(1)
        
        if metrics:
            return "METRIC", metrics
            
        # 4. Fallback for unparsed but non-noisy lines
        return "OTHER", line.strip()