"""Firebase ID-token verification and per-account device endpoints."""
import json
import os
from functools import wraps

from flask import current_app, g, jsonify, request
from firebase_admin import auth as firebase_auth, credentials, get_app, initialize_app
from firebase_admin.exceptions import FirebaseError

from .extensions import db
from .models import User, UserDevice


def _firebase_app():
    try:
        return get_app()
    except ValueError:
        raw = os.environ.get('FIREBASE_SERVICE_ACCOUNT_JSON')
        if raw:
            try:
                cred = credentials.Certificate(json.loads(raw))
            except (ValueError, TypeError) as exc:
                current_app.logger.error('FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON')
                raise RuntimeError('Firebase Admin credentials are misconfigured') from exc
        else:
            # On Google Cloud this can use Application Default Credentials. On Render,
            # configure FIREBASE_SERVICE_ACCOUNT_JSON in the service environment.
            cred = credentials.ApplicationDefault()
        project_id = os.environ.get('FIREBASE_PROJECT_ID', 'recipe-5f201')
        return initialize_app(cred, {'projectId': project_id})


def firebase_user_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return jsonify({'error': 'Missing Firebase ID token'}), 401
        token = header[7:].strip()
        if not token:
            return jsonify({'error': 'Missing Firebase ID token'}), 401
        try:
            decoded = firebase_auth.verify_id_token(token, app=_firebase_app(), check_revoked=True)
        except (FirebaseError, ValueError, RuntimeError):
            current_app.logger.exception('Firebase token verification failed')
            return jsonify({'error': 'Invalid or expired authentication token'}), 401
        uid = decoded.get('uid')
        if not uid:
            return jsonify({'error': 'Invalid authentication token'}), 401
        user = User.query.filter_by(firebase_uid=uid).first()
        if user is None:
            user = User(firebase_uid=uid, phone_number=decoded.get('phone_number'))
            db.session.add(user)
            db.session.commit()
        elif decoded.get('phone_number') and user.phone_number != decoded.get('phone_number'):
            user.phone_number = decoded.get('phone_number')
            db.session.commit()
        g.firebase_user = user
        return view(*args, **kwargs)
    return wrapped


@firebase_user_required
def account():
    user = g.firebase_user
    return jsonify({'id': user.id, 'phoneNumber': user.phone_number, 'createdAt': user.created_at.isoformat() if user.created_at else None})


@firebase_user_required
def devices():
    user = g.firebase_user
    if request.method == 'GET':
        rows = UserDevice.query.filter_by(user_id=user.id).order_by(UserDevice.created_at.asc()).all()
        return jsonify({'devices': [{'id': d.device_id, 'label': d.label, 'createdAt': d.created_at.isoformat() if d.created_at else None, 'lastSeenAt': d.last_seen_at.isoformat() if d.last_seen_at else None} for d in rows]})
    data = request.get_json(silent=True) or {}
    device_id = str(data.get('deviceId', '')).strip()
    label = str(data.get('label', '')).strip()[:120]
    if not device_id or len(device_id) > 128:
        return jsonify({'error': 'A valid deviceId is required'}), 400
    row = UserDevice.query.filter_by(user_id=user.id, device_id=device_id).first()
    if row is None:
        row = UserDevice(user_id=user.id, device_id=device_id, label=label or None)
        db.session.add(row)
    else:
        row.label = label or row.label
        row.last_seen_at = db.func.now()
    db.session.commit()
    return jsonify({'success': True, 'deviceId': device_id}), 200


@firebase_user_required
def delete_device(device_id):
    row = UserDevice.query.filter_by(user_id=g.firebase_user.id, device_id=device_id).first()
    if row is None:
        return jsonify({'error': 'Device not found'}), 404
    db.session.delete(row)
    db.session.commit()
    return jsonify({'success': True})
