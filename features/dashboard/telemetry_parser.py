import re

class MsgType:
    PLAYER_JOIN = "PLAYER_JOIN"
    GLOBAL_CHAT = "GLOBAL_CHAT_CHAT"
    FACTION_CHAT = "FACTION_CHAT_CHAT"
    METRIC = "METRIC"
    STATUS_REGISTRY = "STATUS_REGISTRY"
    NOISE = "NOISE"


class TelemetryParser:
    """Stateless parser for Empyrion server log lines."""
    
    def __init__(self):
            # Noise patterns to be ignored entirely
            self.noise_filters = [
                re.compile(r"System\.Reflection\.TargetInvocationException"),
                re.compile(r"NullReferenceException"),
                re.compile(r"EmpyrionChatDiscordBridge"),
                re.compile(r"EmpyrionModHost"),
                re.compile(r"at System\."), 
                re.compile(r"Thread 'TelnetClient"),
                re.compile(r"Telnet Connection closed"),
                re.compile(r"transport connection"),
                re.compile(r"aborted by the software"),
                re.compile(r"aborted"),
                re.compile(r"\.\)"),
                re.compile(r"\{EPM\}")
            ]
            
            # Patterns for metrics and uptime (non-chat)
            self.patterns = {
                "status_registry": re.compile(r"id=(?P<id>\d+) name=(?P<name>.*?) fac=\[(?P<fac>.*?)\] role=(?P<role>.*?) online="),
                "uptime": re.compile(r"Uptime=(?P<time>[a-zA-Z0-9/s]+)"),
                "system_metric": re.compile(r"(?P<metric>fps|heap|players)=\s*(?P<value>[^\s,\)]+)", re.IGNORECASE),
                "player_join": re.compile(r"Got player id: CId=\d+, EId=(?P<id>\d+), .*?/'(?P<name>.*?)'"),
                "list_entry": re.compile(r"id=(?P<id>\d+), Name='(?P<name>.*?) (?=fac=)")
            }
            
            # Dedicated routing map for all chat types
            # This includes both old ServerForward formats and new Player-Direct formats
            self.chat_routing = {
                "GLOBAL": re.compile(r"CHAT (ServerForward/Global|Player/Global) from (?P<id>-?\d+)/.*? \((?P<player>.*?)\):\s*'(?P<message>.*?)'"),
                "FACTION": re.compile(r"CHAT (ServerForward/Faction|Player/Faction) from (?P<id>-?\d+)/.*? \((?P<player>.*?)\):\s*'(?P<message>.*?)'")
            }

    def parse(self, line):
        # 1. Noise Filter: Drop junk immediately
        if any(pattern.search(line) for pattern in self.noise_filters):
            return "NOISE", None
        
        # 2. Registry Sync: Check for the heartbeat registry line
        status_matches = list(self.patterns["status_registry"].finditer(line))
        if status_matches:
            # Extract data from all found matches in the line
            registry_data = [m.groupdict() for m in status_matches]
            return MsgType.STATUS_REGISTRY, registry_data

        # 3. Player Join Logic:
        # Check for list output
        list_match = self.patterns["list_entry"].search(line)
        if list_match:
            return "PLAYER_JOIN", list_match.groupdict()
        
        login_match = self.patterns["player_join"].search(line)
        if login_match:
            return "PLAYER_JOIN", login_match.groupdict()
        
        # 4. Priority Chat Parsing: Multi-pattern routing
        ''' This replaces manual if/else blocks with a loop that checks the 
        chat_routing dictionary defined in __init__.'''
        for chat_type, pattern in self.chat_routing.items():
            match = pattern.search(line)
            if match:
                data = match.groupdict()
                # Dynamically construct the signal type (e.g., GLOBAL_CHAT)
                print(f"[DEBUG] Regex extracted: {data}")
                # We use .get() here as a safety measure to prevent KeyError
                return f"{chat_type}_CHAT", {
                    "id": data.get("id"),
                    "faction": data.get("faction", "N/A"),
                    "player": data.get("player", "Unknown").strip(),
                    "message": data.get("message", "").strip()
                }
            
        # 5. High-Performance Metric Harvesting: single-pass evaluation across unified metrics strings
        metrics = {}
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