import os
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from dotenv import load_dotenv

from detector import analyze_event
from storage import init_db, save_event, list_events, mark_reviewed, get_stats, clear_demo_events

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-this-secret")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "cloudshield-demo")
init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.route("/")
def index():
    stats = get_stats()
    events = list_events(limit=12)
    return render_template("index.html", stats=stats, events=events, logged_in=session.get("logged_in", False))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            flash("Signed in successfully.", "success")
            return redirect(url_for("index"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/simulate", methods=["POST"])
def simulate():
    scenario = request.form.get("scenario", "normal")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if scenario == "normal":
        sample_events = [
            {"file_name": "weekly_report.docx", "event_type": "modified", "events_in_window": 2, "extension_changed": False},
            {"file_name": "team_photo.jpg", "event_type": "created", "events_in_window": 1, "extension_changed": False},
            {"file_name": "budget.xlsx", "event_type": "modified", "events_in_window": 3, "extension_changed": False},
        ]
    elif scenario == "suspicious":
        sample_events = [
            {"file_name": "document.locked", "event_type": "renamed", "events_in_window": 48, "extension_changed": True},
            {"file_name": "photos.locked", "event_type": "modified", "events_in_window": 65, "extension_changed": True},
            {"file_name": "archive.locked", "event_type": "renamed", "events_in_window": 52, "extension_changed": True},
            {"file_name": "records.locked", "event_type": "modified", "events_in_window": 43, "extension_changed": True},
        ]
    else:
        flash("Unknown simulation scenario.", "error")
        return redirect(url_for("index"))

    for i, event in enumerate(sample_events):
        result = analyze_event(event)
        save_event({
            **event,
            **result,
            "created_at": now,
            "source": f"demo-{scenario}",
            "reviewed": 0,
        })
    flash(f"Added {len(sample_events)} safe simulated {scenario} events.", "success")
    return redirect(url_for("index"))


@app.route("/review/<int:event_id>", methods=["POST"])
@login_required
def review(event_id):
    mark_reviewed(event_id)
    flash("Alert marked as reviewed.", "success")
    return redirect(url_for("index"))


@app.route("/events")
def events_page():
    severity = request.args.get("severity", "")
    events = list_events(limit=200, severity=severity or None)
    return render_template("events.html", events=events, severity=severity, logged_in=session.get("logged_in", False))


@app.route("/export")
@login_required
def export_logs():
    """Optional AWS S3 export. The app still works without AWS configuration."""
    import csv
    import io
    from flask import Response
    from storage import list_events

    rows = list_events(limit=10000)
    output = io.StringIO()
    fields = ["id", "created_at", "file_name", "event_type", "events_in_window", "risk_score", "severity", "reasons", "source", "reviewed"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    csv_data = output.getvalue()

    bucket = os.getenv("S3_BUCKET")
    if bucket:
        try:
            import boto3
            s3 = boto3.client("s3", region_name=os.getenv("AWS_REGION") or None)
            key = f"cloudshield-logs/events-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.csv"
            s3.put_object(Bucket=bucket, Key=key, Body=csv_data.encode("utf-8"), ContentType="text/csv")
            flash(f"Logs exported to s3://{bucket}/{key}", "success")
            return redirect(url_for("index"))
        except Exception as exc:
            app.logger.exception("S3 export failed")
            flash(f"S3 export failed; CSV downloaded instead. Check AWS configuration. ({type(exc).__name__})", "error")
    else:
        flash("S3_BUCKET is not configured; downloading CSV locally.", "error")
    return Response(csv_data, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=cloudshield-events.csv"})


@app.route("/reset-demo", methods=["POST"])
@login_required
def reset_demo():
    clear_demo_events()
    flash("Demo-generated events cleared.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Local development only. For production, use a production WSGI server.
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)
