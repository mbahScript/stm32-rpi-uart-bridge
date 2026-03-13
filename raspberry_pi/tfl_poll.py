from typing import Tuple, Optional, List, Dict, Any

def summarize_tube_status(lines: List[Dict[str, Any]], top_n: int = 4) -> str:
    """
    Produces a compact status string for STM32.
    Example:
      "TUBE: Bakerloo=Good; Central=Minor Delays; ..."
    """
    parts = []
    for line in lines[:top_n]:
        name = line.get("name", "Unknown")
        statuses = line.get("lineStatuses", [])
        # Take the first status for compactness
        desc = statuses[0].get("statusSeverityDescription", "Unknown") if statuses else "Unknown"
        parts.append(f"{name}={desc}")
    return "TUBE: " + "; ".join(parts)

def summarize_arrivals(arrivals: List[Dict[str, Any]], top_n: int = 3) -> str:
    """
    Compact arrivals summary:
      "ARR: 25B 2m; 25B 6m; 73 7m"
    """
    # arrivals usually include expectedArrival or timeToStation (seconds)
    # Sort by soonest
    def key(a):
        return a.get("timeToStation", 10**9)

    arrivals_sorted = sorted(arrivals, key=key)[:top_n]

    parts = []
    for a in arrivals_sorted:
        line = a.get("lineName", "?")
        mins = int(a.get("timeToStation", 0) / 60)
        parts.append(f"{line} {mins}m")
    return "ARR: " + "; ".join(parts)