from detector import analyze_event


def test_normal_activity_is_low():
    result = analyze_event({
        "file_name": "notes.docx",
        "event_type": "modified",
        "events_in_window": 2,
        "extension_changed": False,
    })
    assert result["severity"] == "Low"
    assert result["risk_score"] < 30


def test_high_rate_and_extension_change_is_high():
    result = analyze_event({
        "file_name": "notes.locked",
        "event_type": "renamed",
        "events_in_window": 48,
        "extension_changed": True,
    })
    assert result["severity"] == "High"
    assert result["risk_score"] >= 60
    assert "High event rate" in result["reasons"]


def test_medium_activity():
    result = analyze_event({
        "file_name": "notes.docx",
        "event_type": "modified",
        "events_in_window": 18,
        "extension_changed": True,
    })
    assert result["severity"] == "Medium"
