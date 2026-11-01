"""Admin authentication: login/logout, CSRF protection, rate limiting."""

import hmac
import secrets
import time
from functools import wraps

from flask import current_app, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash


def rate_limited(key, limit, window_seconds, record=True):
    """Return True if `key` already made `limit` hits within the window; otherwise optionally record a hit."""
    rate_hits = current_app.extensions['rate_hits']  # key -> list of timestamps (per app, best effort)
    now = time.time()
    hits = [t for t in rate_hits.get(key, []) if now - t < window_seconds]
    if len(hits) >= limit:
        rate_hits[key] = hits
        return True
    if record:
        hits.append(now)
    rate_hits[key] = hits
    return False


def csrf_token():
    """Per-session CSRF token, created on first use."""
    if not current_app.secret_key:
        return ''  # sessions are unavailable when admin login is not configured
    if 'csrf' not in session:
        session['csrf'] = secrets.token_urlsafe(32)
    return session['csrf']

def csrf_valid(submitted):
    expected = session.get('csrf')
    return bool(expected and submitted) and hmac.compare_digest(expected, submitted)

def inject_csrf_token():
    return {'csrf_token': csrf_token}

def admin_required(view):
    """Allow only the logged-in admin: JSON 401 for API calls, redirect to /login for pages."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('admin'):
            if request.path.startswith('/api/'):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped

def check_csrf():
    """State-changing API calls and logout must carry the session's CSRF token."""
    if request.method in ('POST', 'PUT', 'DELETE') and (request.path.startswith('/api/') or request.path == '/logout'):
        if not session.get('admin'):
            return None  # admin_required answers 401 for the API; logout of an anonymous user is harmless
        submitted = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not csrf_valid(submitted):
            return jsonify({"error": "Invalid CSRF token"}), 403
    return None

def client_ip():
    # Behind Render's proxy the last X-Forwarded-For entry is the one the proxy added (client-supplied entries come first)
    forwarded = request.headers.get('X-Forwarded-For', '')
    return forwarded.split(',')[-1].strip() or request.remote_addr or 'unknown'

def login():
    """Single-admin password login"""
    if not current_app.secret_key or not current_app.config['ADMIN_PASSWORD_HASH']:
        return render_template('login.html', error='Admin login is not configured'), 503
    if request.method == 'GET':
        return render_template('login.html', error=None)

    if not csrf_valid(request.form.get('csrf_token')):
        return render_template('login.html', error='Session expired, please try again'), 403
    attempts_key = f'login:{client_ip()}'
    if rate_limited(attempts_key, 5, 15 * 60, record=False):
        return render_template('login.html', error='Too many attempts, try again later'), 429
    if not check_password_hash(current_app.config['ADMIN_PASSWORD_HASH'], request.form.get('password', '')):
        rate_limited(attempts_key, 5, 15 * 60)  # count the failure
        return render_template('login.html', error='Invalid password'), 401

    session.clear()  # drop any pre-login session state
    session['admin'] = True
    session.permanent = True
    return redirect(url_for('manage'))

def logout():
    session.clear()
    return redirect(url_for('index'))
