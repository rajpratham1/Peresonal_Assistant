"""
Viru AI Assistant - Flask Web Server v3.0
All API endpoints for the full-featured web dashboard.
"""
from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import closing
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

import sys
sys.path.insert(0, str(Path(__file__).parent))

# Boot LLM server early
from backend.main import Assistant
Assistant._ensure_llm()

# ── Lazy assistant singleton ───────────────────────────────────────────────────
_assistant: Assistant | None = None
_lock = threading.Lock()

def get_assistant() -> Assistant:
    global _assistant
    if _assistant is None:
        with _lock:
            if _assistant is None:
                _assistant = Assistant()
    return _assistant

# ── Flask ──────────────────────────────────────────────────────────────────────
WEB_DIR = Path(__file__).parent / "web"
app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")

@app.after_request
def add_header(response):
    # Disable cache for static files to force browsers to load latest app.js/style.css
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# ── Helpers ────────────────────────────────────────────────────────────────────
def db_conn():
    from backend.config import DATABASE_PATH, DATABASE_DIR
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def rows_to_list(rows):
    return [dict(r) for r in rows]

def _get_lan_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        try:
            ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            ip = '127.0.0.1'
    finally:
        s.close()
    return ip

# ── Static ─────────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(str(WEB_DIR), "index.html")

# ── Status ─────────────────────────────────────────────────────────────────────
@app.route("/api/status")
def status():
    import socket
    llm_up = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\
                   .connect_ex(("127.0.0.1", 8080)) == 0
    return jsonify({"status": "ok", "llm_online": llm_up, "version": "3.0-elite"})

# ── Chat ───────────────────────────────────────────────────────────────────────
@app.route("/api/chat", methods=["POST"])
def chat():
    body    = request.get_json(force=True, silent=True) or {}
    message = str(body.get("message", "")).strip()
    if not message:
        return jsonify({"error": "message is required"}), 400

    assistant = get_assistant()
    response  = assistant.handle_text(message, voice_response=False)

    # Persist to chat_history table
    try:
        with closing(db_conn()) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS chat_history "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, created_at TEXT)"
            )
            now = datetime.now().isoformat(timespec="seconds")
            conn.execute("INSERT INTO chat_history (role,content,created_at) VALUES (?,?,?)",
                         ("user", message, now))
            conn.execute("INSERT INTO chat_history (role,content,created_at) VALUES (?,?,?)",
                         ("assistant", response.text, now))
            conn.commit()
    except Exception:
        pass

    return jsonify({
        "reply":  response.text,
        "intent": response.debug.intent,
        "route":  response.debug.route,
        "exit":   response.should_exit,
    })

# ── Dashboard ──────────────────────────────────────────────────────────────────
@app.route("/api/dashboard")
def dashboard():
    import psutil, platform, socket

    # System stats
    cpu   = psutil.cpu_percent(interval=0.3)
    ram   = psutil.virtual_memory()
    disk  = psutil.disk_usage("/")
    boot  = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")

    # Recent commands
    recent = []
    try:
        with closing(db_conn()) as conn:
            rows = conn.execute(
                "SELECT command, intent, created_at FROM commands ORDER BY id DESC LIMIT 10"
            ).fetchall()
            recent = rows_to_list(rows)
    except Exception:
        pass

    # Reminder count
    pending = 0
    try:
        with closing(db_conn()) as conn:
            pending = conn.execute(
                "SELECT COUNT(*) FROM reminders WHERE status='pending'"
            ).fetchone()[0]
    except Exception:
        pass

    # Notes count
    notes_count = 0
    try:
        with closing(db_conn()) as conn:
            notes_count = conn.execute("SELECT COUNT(*) FROM notes").fetchone()[0]
    except Exception:
        pass

    # LAN IP
    lan_ip = _get_lan_ip()

    return jsonify({
        "cpu_percent":   cpu,
        "ram_percent":   ram.percent,
        "ram_used_gb":   round(ram.used / 1e9, 1),
        "ram_total_gb":  round(ram.total / 1e9, 1),
        "disk_percent":  disk.percent,
        "disk_used_gb":  round(disk.used / 1e9, 1),
        "disk_total_gb": round(disk.total / 1e9, 1),
        "boot_time":     boot,
        "platform":      platform.node(),
        "lan_ip":        lan_ip,
        "port":          5000,
        "recent_commands": recent,
        "pending_reminders": pending,
        "notes_count":   notes_count,
    })

# ── Sysinfo (live polling) ─────────────────────────────────────────────────────
@app.route("/api/sysinfo")
def sysinfo():
    import psutil
    cpu  = psutil.cpu_percent(interval=0.2)
    ram  = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net  = psutil.net_io_counters()
    return jsonify({
        "cpu":   cpu,
        "ram":   ram.percent,
        "disk":  disk.percent,
        "net_sent_mb":  round(net.bytes_sent / 1e6, 1),
        "net_recv_mb":  round(net.bytes_recv / 1e6, 1),
    })

# ── Notes ──────────────────────────────────────────────────────────────────────
@app.route("/api/notes", methods=["GET"])
def get_notes():
    with closing(db_conn()) as conn:
        rows = conn.execute(
            "SELECT id, content, created_at FROM notes ORDER BY id DESC"
        ).fetchall()
    return jsonify(rows_to_list(rows))

@app.route("/api/notes", methods=["POST"])
def add_note():
    body    = request.get_json(force=True, silent=True) or {}
    content = str(body.get("content", "")).strip()
    if not content:
        return jsonify({"error": "content required"}), 400
    now = datetime.now().isoformat(timespec="seconds")
    with closing(db_conn()) as conn:
        cur = conn.execute("INSERT INTO notes (content, created_at) VALUES (?,?)", (content, now))
        conn.commit()
        row = conn.execute("SELECT id, content, created_at FROM notes WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
def delete_note(note_id):
    with closing(db_conn()) as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        conn.commit()
    return jsonify({"ok": True})

# ── Reminders ──────────────────────────────────────────────────────────────────
@app.route("/api/reminders", methods=["GET"])
def get_reminders():
    with closing(db_conn()) as conn:
        rows = conn.execute(
            "SELECT id, kind, target, message, trigger_at, status, created_at "
            "FROM reminders ORDER BY trigger_at ASC"
        ).fetchall()
    return jsonify(rows_to_list(rows))

@app.route("/api/reminders", methods=["POST"])
def add_reminder():
    body       = request.get_json(force=True, silent=True) or {}
    kind       = str(body.get("kind", "alarm")).strip()
    trigger_at = str(body.get("trigger_at", "")).strip()
    message    = str(body.get("message", "")).strip()
    target     = str(body.get("target", "")).strip() or None
    if not trigger_at:
        return jsonify({"error": "trigger_at required"}), 400
    now = datetime.now().isoformat(timespec="seconds")
    with closing(db_conn()) as conn:
        cur = conn.execute(
            "INSERT INTO reminders (kind,target,message,trigger_at,status,created_at) VALUES (?,?,?,?,'pending',?)",
            (kind, target, message, trigger_at, now)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM reminders WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201

@app.route("/api/reminders/<int:rid>", methods=["DELETE"])
def delete_reminder(rid):
    with closing(db_conn()) as conn:
        conn.execute("DELETE FROM reminders WHERE id=?", (rid,))
        conn.commit()
    return jsonify({"ok": True})

@app.route("/api/reminders/<int:rid>/done", methods=["POST"])
def done_reminder(rid):
    with closing(db_conn()) as conn:
        conn.execute("UPDATE reminders SET status='done' WHERE id=?", (rid,))
        conn.commit()
    return jsonify({"ok": True})

# ── Contacts ───────────────────────────────────────────────────────────────────
@app.route("/api/contacts", methods=["GET"])
def get_contacts():
    with closing(db_conn()) as conn:
        rows = conn.execute(
            "SELECT id, name, phone, email, whatsapp_name, created_at FROM contacts ORDER BY name ASC"
        ).fetchall()
    return jsonify(rows_to_list(rows))

@app.route("/api/contacts", methods=["POST"])
def add_contact():
    body  = request.get_json(force=True, silent=True) or {}
    name  = str(body.get("name", "")).strip().lower()
    phone = str(body.get("phone", "")).strip() or None
    email = str(body.get("email", "")).strip() or None
    wa    = str(body.get("whatsapp_name", "")).strip() or None
    if not name:
        return jsonify({"error": "name required"}), 400
    now = datetime.now().isoformat(timespec="seconds")
    with closing(db_conn()) as conn:
        conn.execute(
            "INSERT INTO contacts (name,phone,email,whatsapp_name,created_at) VALUES (?,?,?,?,?) "
            "ON CONFLICT(name) DO UPDATE SET phone=excluded.phone, email=excluded.email, whatsapp_name=excluded.whatsapp_name",
            (name, phone, email, wa, now)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM contacts WHERE name=?", (name,)).fetchone()
    return jsonify(dict(row)), 201

@app.route("/api/contacts/<int:cid>", methods=["DELETE"])
def delete_contact(cid):
    with closing(db_conn()) as conn:
        conn.execute("DELETE FROM contacts WHERE id=?", (cid,))
        conn.commit()
    return jsonify({"ok": True})

# ── Chat History ───────────────────────────────────────────────────────────────
@app.route("/api/history")
def get_history():
    try:
        with closing(db_conn()) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS chat_history "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT, content TEXT, created_at TEXT)"
            )
            rows = conn.execute(
                "SELECT id, role, content, created_at FROM chat_history ORDER BY id DESC LIMIT 200"
            ).fetchall()
        return jsonify(rows_to_list(rows))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/history", methods=["DELETE"])
def clear_history():
    with closing(db_conn()) as conn:
        conn.execute("DELETE FROM chat_history")
        conn.commit()
    return jsonify({"ok": True})

# ── Screenshots ────────────────────────────────────────────────────────────────
@app.route("/api/screenshots")
def list_screenshots():
    screenshots_dir = Path(__file__).parent / "screenshots"
    if not screenshots_dir.exists():
        return jsonify([])
    files = sorted(screenshots_dir.glob("*.png"), key=lambda f: f.stat().st_mtime, reverse=True)
    return jsonify([{"name": f.name, "url": f"/screenshots/{f.name}",
                     "size_kb": round(f.stat().st_size / 1024, 1)} for f in files[:50]])

@app.route("/screenshots/<path:filename>")
def serve_screenshot(filename):
    screenshots_dir = Path(__file__).parent / "screenshots"
    return send_from_directory(str(screenshots_dir), filename)

# ── Files ──────────────────────────────────────────────────────────────────────
@app.route("/api/files")
def browse_files():
    folder = request.args.get("path", str(Path.home() / "Desktop"))
    try:
        p = Path(folder)
        if not p.exists() or not p.is_dir():
            return jsonify({"error": "not a directory"}), 400
        items = []
        for f in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            items.append({
                "name": f.name,
                "path": str(f),
                "is_dir": f.is_dir(),
                "size_kb": round(f.stat().st_size / 1024, 1) if f.is_file() else None,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })
        return jsonify({"path": str(p), "parent": str(p.parent), "items": items})
    except PermissionError:
        return jsonify({"error": "permission denied"}), 403

@app.route("/api/files/open", methods=["POST"])
def open_file():
    body = request.get_json(force=True, silent=True) or {}
    path = str(body.get("path", "")).strip()
    if not path:
        return jsonify({"error": "path required"}), 400
    assistant = get_assistant()
    response  = assistant.handle_text(f"open folder {path}" if Path(path).is_dir() else path,
                                      voice_response=False)
    return jsonify({"reply": response.text})

# ── QR Code ────────────────────────────────────────────────────────────────────
@app.route("/api/qrcode")
def qr_code():
    """Return a QR code SVG for the LAN URL."""
    lan_ip = _get_lan_ip()
    url = f"http://{lan_ip}:5000"
    # Use qrcode if available, else return the URL only
    try:
        import qrcode, io, base64
        qr  = qrcode.make(url)
        buf = io.BytesIO()
        qr.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return jsonify({"url": url, "img": f"data:image/png;base64,{b64}"})
    except ImportError:
        return jsonify({"url": url, "img": None})

# ── Weather ────────────────────────────────────────────────────────────────────
@app.route("/api/weather")
def weather():
    try:
        import urllib.request, json
        req = urllib.request.Request(
            "https://wttr.in/?format=j1",
            headers={"User-Agent": "curl/7.68.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            data = json.loads(r.read())
        curr = data["current_condition"][0]
        area = data["nearest_area"][0]
        city = area["areaName"][0]["value"]
        return jsonify({
            "city":        city,
            "temp_c":      curr["temp_C"],
            "feels_like":  curr["FeelsLikeC"],
            "desc":        curr["weatherDesc"][0]["value"],
            "humidity":    curr["humidity"],
            "wind_kmph":   curr["windspeedKmph"],
            "icon":        _weather_icon(curr["weatherDesc"][0]["value"]),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 503

def _weather_icon(desc: str) -> str:
    d = desc.lower()
    if "sun" in d or "clear" in d:   return "☀️"
    if "cloud" in d:                  return "☁️"
    if "rain" in d or "drizzle" in d: return "🌧️"
    if "thunder" in d or "storm" in d:return "⛈️"
    if "snow" in d:                   return "❄️"
    if "fog" in d or "mist" in d:    return "🌫️"
    if "wind" in d:                   return "💨"
    return "🌡️"

# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import webbrowser
    port = int(os.getenv("VIRU_PORT", 5000))
    print(f"\n  Viru Web Client  ->  http://localhost:{port}")
    print(f"  Share on LAN    ->  check dashboard for your LAN IP")
    print("  Press Ctrl+C to stop.\n")
    threading.Timer(1.2, lambda: webbrowser.open(f"http://localhost:{port}")).start()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
