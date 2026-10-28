"""Safe, rule-based analysis of synthetic file activity events."""
from dataclasses import dataclass


@dataclass
class DetectionResult:
    risk_score: int
    severity: str
    reasons: str


def analyze_event(event: dict) -> dict:
    score = 0
    reasons = []
    event_type = str(event.get("event_type", "")).lower()
    count = int(event.get("events_in_window", 0) or 0)
    extension_changed = bool(event.get("extension_changed", False))
    file_name = str(event.get("file_name", ""))

    if count >= 40:
        score += 55
        reasons.append(f"High event rate ({count} events in the observation window)")
    elif count >= 15:
        score += 25
        reasons.append(f"Elevated event rate ({count} events in the observation window)")

    if extension_changed:
        score += 30
        reasons.append("File extension change reported")

    suspicious_extensions = (".locked", ".encrypted", ".crypt")
    if file_name.lower().endswith(suspicious_extensions):
        score += 25
        reasons.append("Filename uses a suspicious demo extension")

    if event_type == "renamed":
        score += 10
        reasons.append("Rename event observed")

    score = min(score, 100)
    if score >= 60:
        severity = "High"
    elif score >= 30:
        severity = "Medium"
    else:
        severity = "Low"

    if not reasons:
        reasons.append("No configured suspicious patterns detected")

    return {
        "risk_score": score,
        "severity": severity,
        "reasons": "; ".join(reasons),
    }
