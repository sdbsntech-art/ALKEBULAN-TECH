#!/usr/bin/env python3
# ==========================================================
#  ALKEBULAN TECH -- Security Alert Server
#  Detecte toute tentative d'acces au code source
#  Alerte par : son systeme + email HTML vers Gmail
#  Base de donnees : SQLite (log de tous les incidents)
#
#  Installation :
#    pip install flask flask-cors
#    pip install playsound  (optionnel, pour .wav)
#
#  Lancement :
#    python security_server.py
#    ou : gunicorn -w 2 security_server:app -b 0.0.0.0:5001
# ==========================================================

import os
import json
import sqlite3
import smtplib
import threading
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

# ===========================================================
#  CONFIGURATION  <-- modifier ces valeurs
# ===========================================================
ALERT_EMAIL   = "seydoubakhayokho1@gmail.com"
SMTP_HOST     = "smtp.gmail.com"
SMTP_PORT     = 587
SMTP_USER     = "seydoubakhayokho1@gmail.com"
# Mot de passe APPLICATION Gmail (pas votre mot de passe principal)
# Creer sur : https://myaccount.google.com/apppasswords
SMTP_PASS     = "wkis efdl sowa aysa"
DB_PATH       = "security_alerts.db"
COOLDOWN_SEC  = 30   # Delai min entre 2 emails du meme type
ADMIN_TOKEN   = "alkebulan_admin_2025"
SERVER_PORT   = 5001
# ===========================================================

app = Flask(__name__)
CORS(app)
last_notif = {}
lock = threading.Lock()


def is_authorized(req):
    """Accept either ?token=... or Authorization: Bearer <token>"""
    auth = req.headers.get("Authorization", "") or ""
    token = ""
    if auth and auth.lower().startswith("bearer "):
        try:
            token = auth.split(None, 1)[1].strip()
        except Exception:
            token = ""
    else:
        token = req.args.get("token", "") or ""
    return token == ADMIN_TOKEN


# -----------------------------------------------------------
#  BASE DE DONNEES
# -----------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS alerts ("
        "id         INTEGER PRIMARY KEY AUTOINCREMENT,"
        "type       TEXT NOT NULL,"
        "url        TEXT,"
        "ip         TEXT,"
        "user_agent TEXT,"
        "timestamp  TEXT NOT NULL"
        ")"
    )
    conn.commit()
    conn.close()
    print(f"[DB] Base initialisee : {DB_PATH}")


def save_alert(data: dict, ip: str):
    ts = data.get("timestamp", datetime.utcnow().isoformat())
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO alerts (type, url, ip, user_agent, timestamp) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            data.get("type", "inconnu"),
            data.get("url", ""),
            ip,
            data.get("userAgent", "")[:300],
            ts,
        ),
    )
    conn.commit()
    conn.close()


# -----------------------------------------------------------
#  SON D'ALERTE  (cross-platform)
# -----------------------------------------------------------
def play_alert():
    # Tentative 1 : fichier WAV (si present dans le dossier)
    try:
        import playsound
        wav = os.path.join(os.path.dirname(__file__), "alert.wav")
        if os.path.exists(wav):
            playsound.playsound(wav, block=False)
            return
    except Exception:
        pass

    # Tentative 2 : Windows winsound
    try:
        import winsound
        winsound.Beep(880, 350)
        time.sleep(0.1)
        winsound.Beep(440, 300)
        return
    except Exception:
        pass

    # Tentative 3 : Linux / macOS terminal bell
    try:
        os.system('printf "\\a"')
    except Exception:
        pass


# -----------------------------------------------------------
#  EMAIL DE NOTIFICATION
# -----------------------------------------------------------
def send_email(alert_type: str, ip: str, url: str, ua: str, ts: str):
    with lock:
        now = time.time()
        if alert_type in last_notif and now - last_notif[alert_type] < COOLDOWN_SEC:
            print(f"[EMAIL] Cooldown actif pour '{alert_type}', email ignore")
            return
        last_notif[alert_type] = now

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[ALKEBULAN TECH] Alerte securite : {alert_type}"
        msg["From"]    = SMTP_USER
        msg["To"]      = ALERT_EMAIL

        # ── Texte brut
        texte = (
            f"ALERTE SECURITE - ALKEBULAN TECH\n"
            f"==================================\n"
            f"Type     : {alert_type}\n"
            f"IP       : {ip}\n"
            f"Page     : {url}\n"
            f"Heure    : {ts} UTC\n"
            f"Agent    : {ua[:120]}\n"
        )

        # ── HTML
        html = f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#08060E;font-family:Arial,sans-serif;">
  <div style="max-width:600px;margin:0 auto;padding:32px;">

    <!-- Header -->
    <div style="border-bottom:2px solid #00BFFF;padding-bottom:20px;margin-bottom:24px;">
      <h1 style="color:#00BFFF;font-size:22px;letter-spacing:3px;
                 text-transform:uppercase;margin:0 0 6px 0;">
        &#128274; Alerte Securite
      </h1>
      <p style="color:#8A8AA3;font-size:12px;letter-spacing:2px;margin:0;">
        ALKEBULAN TECH &mdash; Systeme de protection
      </p>
    </div>

    <!-- Message -->
    <p style="color:#C8C8E0;font-size:15px;line-height:1.6;margin-bottom:24px;">
      Une tentative d&rsquo;acces au code source a ete detectee sur votre site.
    </p>

    <!-- Tableau details -->
    <table style="width:100%;border-collapse:collapse;background:#12101E;
                  border:1px solid #242038;">
      <tr style="border-bottom:1px solid #242038;">
        <td style="padding:12px 16px;color:#8A8AA3;font-size:11px;
                   letter-spacing:2px;text-transform:uppercase;width:130px;">
          Type
        </td>
        <td style="padding:12px 16px;color:#E91E8C;
                   font-weight:bold;font-size:16px;">
          {alert_type}
        </td>
      </tr>
      <tr style="border-bottom:1px solid #242038;">
        <td style="padding:12px 16px;color:#8A8AA3;font-size:11px;
                   letter-spacing:2px;text-transform:uppercase;">
          Adresse IP
        </td>
        <td style="padding:12px 16px;color:#00BFFF;font-weight:bold;">
          {ip}
        </td>
      </tr>
      <tr style="border-bottom:1px solid #242038;">
        <td style="padding:12px 16px;color:#8A8AA3;font-size:11px;
                   letter-spacing:2px;text-transform:uppercase;">
          Page visitee
        </td>
        <td style="padding:12px 16px;color:#F5F3FF;font-size:13px;
                   word-break:break-all;">
          {url or "Inconnue"}
        </td>
      </tr>
      <tr style="border-bottom:1px solid #242038;">
        <td style="padding:12px 16px;color:#8A8AA3;font-size:11px;
                   letter-spacing:2px;text-transform:uppercase;">
          Navigateur
        </td>
        <td style="padding:12px 16px;color:#C8C8E0;font-size:11px;">
          {ua[:120] if ua else "Inconnu"}
        </td>
      </tr>
      <tr>
        <td style="padding:12px 16px;color:#8A8AA3;font-size:11px;
                   letter-spacing:2px;text-transform:uppercase;">
          Heure (UTC)
        </td>
        <td style="padding:12px 16px;color:#C8C8E0;">
          {ts}
        </td>
      </tr>
    </table>

    <!-- Lien journal -->
    <div style="margin-top:24px;padding:16px;background:#1A1528;
                border:1px solid #242038;">
      <p style="color:#8A8AA3;font-size:12px;margin:0 0 8px 0;">
        Consulter le journal complet des incidents :
      </p>
      <a href="http://localhost:{SERVER_PORT}/api/alerts?token={ADMIN_TOKEN}"
         style="color:#00BFFF;font-size:12px;word-break:break-all;">
        /api/alerts?token={ADMIN_TOKEN}
      </a>
    </div>

    <!-- Footer -->
    <p style="color:#8A8AA3;font-size:10px;margin-top:28px;
              border-top:1px solid #242038;padding-top:16px;
              letter-spacing:1px;">
      Email automatique &mdash; ALKEBULAN TECH Security System 2025
    </p>
  </div>
</body>
</html>"""

        msg.attach(MIMEText(texte, "plain", "utf-8"))
        msg.attach(MIMEText(html,  "html",  "utf-8"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASS)
            srv.sendmail(SMTP_USER, ALERT_EMAIL, msg.as_string())

        print(f"[EMAIL OK] '{alert_type}' notifie -> {ALERT_EMAIL}")

    except Exception as exc:
        print(f"[EMAIL ERR] {exc}")


# -----------------------------------------------------------
#  TRAITEMENT D'UNE ALERTE
# -----------------------------------------------------------
def handle_alert(data: dict, ip: str):
    t  = data.get("type", "inconnu")
    url = data.get("url", "")
    ua  = data.get("userAgent", "")
    ts  = data.get("timestamp", datetime.utcnow().isoformat())

    print(f"[ALERT] {t} | IP: {ip} | {ts}")

    # 1. Sauvegarder en base
    save_alert(data, ip)

    # 2. Son d'alerte (non bloquant)
    threading.Thread(target=play_alert, daemon=True).start()

    # 3. Email (non bloquant)
    threading.Thread(
        target=send_email,
        args=(t, ip, url, ua, ts),
        daemon=True
    ).start()


# -----------------------------------------------------------
#  ROUTES FLASK
# -----------------------------------------------------------
@app.route("/api/security-alert", methods=["POST"])
def route_alert():
    data = request.get_json(silent=True) or {}
    ip   = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip   = ip.split(",")[0].strip()
    handle_alert(data, ip)
    return jsonify({"ok": True}), 200


@app.route("/api/ping")
def route_ping():
    """Beacon image fallback (pixel GIF transparent)."""
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    ip = ip.split(",")[0].strip()
    t  = request.args.get("t", "ping")
    data = {
        "type":      t,
        "url":       request.referrer or "",
        "userAgent": request.user_agent.string,
        "timestamp": datetime.utcnow().isoformat(),
    }
    handle_alert(data, ip)
    # Pixel GIF 1x1 transparent
    gif = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
        b"\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )
    return Response(gif, mimetype="image/gif")


@app.route("/api/alerts")
def route_list():
    """Journal des incidents (token requis)."""
    if not is_authorized(request):
        return jsonify({"error": "Acces refuse"}), 403
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT * FROM alerts ORDER BY id DESC LIMIT 200"
    ).fetchall()
    conn.close()
    cols = ["id", "type", "url", "ip", "user_agent", "timestamp"]
    return jsonify([dict(zip(cols, r)) for r in rows])


@app.route("/api/stats")
def route_stats():
    """Statistiques rapides (token requis)."""
    if not is_authorized(request):
        return jsonify({"error": "Acces refuse"}), 403
    conn = sqlite3.connect(DB_PATH)
    total   = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    by_type = conn.execute(
        "SELECT type, COUNT(*) as n FROM alerts GROUP BY type ORDER BY n DESC"
    ).fetchall()
    by_ip   = conn.execute(
        "SELECT ip, COUNT(*) as n FROM alerts GROUP BY ip ORDER BY n DESC LIMIT 10"
    ).fetchall()
    conn.close()
    return jsonify({
        "total": total,
        "by_type": [{"type": r[0], "count": r[1]} for r in by_type],
        "top_ips": [{"ip": r[0], "count": r[1]} for r in by_ip],
    })


# -----------------------------------------------------------
#  POINT D'ENTREE
# -----------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  ALKEBULAN TECH - Security Alert Server")
    print("=" * 50)
    print(f"  Email alertes  -> {ALERT_EMAIL}")
    print(f"  Base de donnees: {DB_PATH}")
    print(f"  Port           : {SERVER_PORT}")
    print(f"  Journal admin  : /api/alerts?token={ADMIN_TOKEN}")
    print(f"  Statistiques   : /api/stats?token={ADMIN_TOKEN}")
    print("=" * 50)
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False)
