from flask import Blueprint, request, jsonify
import requests
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/users/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({"Error": "The request body is invalid"}), 400
        
        username = data['username']
        password = data['password']
        
        print(f"Login attempt for: {username}")
        
        # Auth0 authentication - Resource Owner Password Grant
        auth0_domain = "dev-kxk3ej4jph3k8f8b.us.auth0.com"
        client_id = "BYPSkm15QBDm4NZYWyZH3Q3Z0ZK6J7eH"
        client_secret = "iVw1zKfvvSvvk0t9L5I9rYANKSd8n7-lCbk3FgA2gxhPgHkKJovm4zD4KEsVErOA"
        audience = "https://tume-tarpaulin-api"
        
        # Correct Auth0 token request format
        token_url = f"https://{auth0_domain}/oauth/token"
        token_data = {
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
            "username": username,
            "password": password,
            "audience": audience,
            "client_id": client_id,
            "client_secret": client_secret,
            "realm": "Username-Password-Authentication",
            "scope": "openid profile email"
        }
        
        print(f"Making request to: {token_url}")
        print(f"Request data: {token_data}")
        
        response = requests.post(token_url, json=token_data)
        
        print(f"Auth0 response status: {response.status_code}")
        print(f"Auth0 response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({"token": result.get("access_token")}), 200
        else:
            return jsonify({"Error": "Unauthorized"}), 401
            
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"Error": "The request body is invalid"}), 400