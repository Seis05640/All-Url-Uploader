"""Lightweight Flask dashboard for analytics and monitoring."""
from __future__ import annotations

import os
import secrets
from functools import wraps

from flask import Flask, jsonify, render_template, request, session

from services.analytics import AnalyticsStore


def create_dashboard_app(analytics_store: AnalyticsStore, admin_token: str) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.secret_key = secrets.token_hex(32)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = False  # Set True in production with HTTPS
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    def require_auth(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("authenticated"):
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Unauthorized"}), 401
                return render_template("login.html")
            return f(*args, **kwargs)
        return decorated

    @app.route("/login", methods=["GET"])
    def login_page():
        return render_template("login.html")

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json() or {}
        token = data.get("token", "")
        if secrets.compare_digest(token, admin_token):
            session["authenticated"] = True
            return jsonify({"success": True})
        return jsonify({"error": "Invalid token"}), 403

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        return jsonify({"success": True})

    @app.route("/")
    @require_auth
    def index():
        stats = analytics_store.get_overview_stats()
        return render_template("index.html", stats=stats)

    @app.route("/api/overview")
    @require_auth
    def api_overview():
        return jsonify(analytics_store.get_overview_stats())

    @app.route("/api/jobs")
    @require_auth
    def api_jobs():
        limit = min(int(request.args.get("limit", 50)), 100)
        offset = int(request.args.get("offset", 0))
        status = request.args.get("status")
        jobs = analytics_store.get_jobs(limit=limit, offset=offset, status=status)
        return jsonify({"jobs": jobs, "limit": limit, "offset": offset})

    @app.route("/api/daily-stats")
    @require_auth
    def api_daily_stats():
        days = min(int(request.args.get("days", 7)), 90)
        return jsonify(analytics_store.get_daily_stats(days=days))

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "service": "dashboard"})

    return app


def run_dashboard(analytics_store: AnalyticsStore, admin_token: str, host: str = "127.0.0.1", port: int = 5000) -> None:
    app = create_dashboard_app(analytics_store, admin_token)
    app.run(host=host, port=port, debug=False)
