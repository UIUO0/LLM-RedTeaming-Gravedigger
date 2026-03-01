"""
detector.py — The Jailbreak Guard
=======================================
Analyzes user inputs for common prompt injection and jailbreak patterns.
This is the "Security" layer for the Red Teaming Showcase.
"""

import re
from typing import Dict, List

# Common jailbreak keywords and patterns
JAILBREAK_PATTERNS: List[str] = [
    r"ignore (previous|all) instructions",
    r"forget your (persona|rules|system prompt)",
    r"act as",
    r"you are now",
    r"new rule",
    r"bypass",
    r"sudo",
    r"dan mode",
    r"jailbreak",
    r"unfiltered",
    r"no restrictions",
    r"tell me your system prompt",
    r"what are your rules",
]

def analyze_input(user_input: str) -> Dict[str, object]:
    """
    Analyzes the input for jailbreak attempts.
    Returns a dict with detection results and a 'stability' score.
    """
    detected_patterns = []
    input_lower = user_input.lower()
    
    for pattern in JAILBREAK_PATTERNS:
        if re.search(pattern, input_lower):
            detected_patterns.append(pattern)
            
    # Calculate stability (100 is stable, 0 is fully compromised)
    # This is a simplified logic for the showcase
    penalty = len(detected_patterns) * 25
    stability_score = max(0, 100 - penalty)
    
    return {
        "is_detected": len(detected_patterns) > 0,
        "patterns": detected_patterns,
        "stability_score": stability_score,
        "risk_level": "High" if stability_score < 50 else ("Medium" if stability_score < 90 else "Low")
    }
