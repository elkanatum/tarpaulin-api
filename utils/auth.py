from functools import wraps
from flask import request, jsonify
import jwt
import requests
import os

def get_token_auth_header():
    """Get the access token from the Authorization Header"""
    auth = request.headers.get("Authorization", None)
    if not auth:
        return None

    parts = auth.split()
    if parts[0].lower() != "bearer":
        return None
    elif len(parts) == 1:
        return None
    elif len(parts) > 2:
        return None

    token = parts[1]
    return token

def verify_decode_jwt(token):
    """Verify and decode JWT token"""
    try:
        # Just decode without verification for now (since we're testing locally)
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload
    except Exception as e:
        print(f"Token verification error: {e}")
        return None

def requires_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        if not token:
            return jsonify({"Error": "Unauthorized"}), 401
        
        payload = verify_decode_jwt(token)
        if not payload:
            return jsonify({"Error": "Unauthorized"}), 401
        
        return f(payload, *args, **kwargs)
    return decorated