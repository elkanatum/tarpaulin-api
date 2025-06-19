from flask import Blueprint, request, jsonify, send_file
from google.cloud import datastore
from google.cloud import storage
from utils.auth import requires_auth
import io
import os

user_bp = Blueprint('users', __name__)

def get_storage_client():
    """Get Cloud Storage client"""
    return storage.Client()

def upload_avatar_to_storage(user_id, file_content):
    """Upload avatar to Cloud Storage"""
    client = get_storage_client()
    bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
    bucket = client.bucket(bucket_name)
    
    blob_name = f"avatars/{user_id}.png"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_content, content_type='image/png')
    
    return blob_name

def get_avatar_from_storage(user_id):
    """Get avatar from Cloud Storage"""
    client = get_storage_client()
    bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
    bucket = client.bucket(bucket_name)
    
    blob_name = f"avatars/{user_id}.png"
    blob = bucket.blob(blob_name)
    
    if blob.exists():
        return blob.download_as_bytes()
    return None

def delete_avatar_from_storage(user_id):
    """Delete avatar from Cloud Storage"""
    client = get_storage_client()
    bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
    bucket = client.bucket(bucket_name)
    
    blob_name = f"avatars/{user_id}.png"
    blob = bucket.blob(blob_name)
    
    if blob.exists():
        blob.delete()
        return True
    return False

def avatar_exists(user_id):
    """Check if avatar exists in Cloud Storage"""
    client = get_storage_client()
    bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
    bucket = client.bucket(bucket_name)
    
    blob_name = f"avatars/{user_id}.png"
    blob = bucket.blob(blob_name)
    
    return blob.exists()

def get_user_courses(user_id, role, datastore_client):
    """Get courses for instructor or student"""
    courses = []
    
    if role == 'instructor':
        # Get courses where this user is the instructor
        course_query = datastore_client.query(kind='courses')
        course_query.add_filter('instructor_id', '=', user_id)
        user_courses = list(course_query.fetch())
        
        for course in user_courses:
            courses.append(f"{request.host_url.rstrip('/')}/courses/{course.key.id}")
    
    elif role == 'student':
        # Get enrollments for this student
        enrollment_query = datastore_client.query(kind='enrollments')
        enrollment_query.add_filter('student_id', '=', user_id)
        enrollments = list(enrollment_query.fetch())
        
        for enrollment in enrollments:
            courses.append(f"{request.host_url.rstrip('/')}/courses/{enrollment['course_id']}")
    
    return courses

@user_bp.route('/users', methods=['GET'])
@requires_auth
def get_all_users(payload):
    """Get all users - Admin only"""
    try:
        client = datastore.Client()
        
        # Check if user is admin
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users or users[0]['role'] != 'admin':
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Get all users
        query = client.query(kind='users')
        all_users = list(query.fetch())
        
        result = []
        for user in all_users:
            result.append({
                "id": user.key.id,
                "role": user['role'],
                "sub": user['sub']
            })
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in get_all_users: {e}")
        return jsonify({"Error": "Internal server error"}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@requires_auth
def get_user(payload, user_id):
    """Get a specific user"""
    try:
        client = datastore.Client()
        
        # Get the requesting user
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        requesting_users = list(query.fetch())
        
        if not requesting_users:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        requesting_user = requesting_users[0]
        
        # Get the target user
        user_key = client.key('users', user_id)
        target_user = client.get(user_key)
        
        if not target_user:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Check permissions
        if requesting_user['role'] != 'admin' and requesting_user.key.id != user_id:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Build response
        result = {
            "id": target_user.key.id,
            "role": target_user['role'],
            "sub": target_user['sub']
        }
        
        # Add avatar_url if avatar exists
        if avatar_exists(user_id):
            result["avatar_url"] = f"{request.host_url.rstrip('/')}/users/{user_id}/avatar"
        
        # Add courses for instructors and students
        if target_user['role'] in ['instructor', 'student']:
            result["courses"] = get_user_courses(user_id, target_user['role'], client)
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in get_user: {e}")
        return jsonify({"Error": "Internal server error"}), 500

@user_bp.route('/users/<int:user_id>/avatar', methods=['POST'])
@requires_auth
def create_update_avatar(payload, user_id):
    """Create or update user avatar"""
    try:
        # FIRST: Check if file is in request (400 takes precedence over everything)
        if 'file' not in request.files:
            return jsonify({"Error": "The request body is invalid"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"Error": "The request body is invalid"}), 400
        
        # SECOND: Check authentication and permissions (after 400 checks)
        client = datastore.Client()
        
        # Check if user owns this profile
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users or users[0].key.id != user_id:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Upload the file to Cloud Storage
        file_content = file.read()
        upload_avatar_to_storage(user_id, file_content)
        
        return jsonify({
            "avatar_url": f"{request.host_url.rstrip('/')}/users/{user_id}/avatar"
        }), 200
        
    except Exception as e:
        print(f"Error in create_update_avatar: {e}")
        return jsonify({"Error": "The request body is invalid"}), 400

@user_bp.route('/users/<int:user_id>/avatar', methods=['GET'])
@requires_auth 
def get_user_avatar(payload, user_id):
    """Get user avatar"""
    try:
        client = datastore.Client()
        
        # Check permissions
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users or users[0].key.id != user_id:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Get avatar from Cloud Storage
        avatar_data = get_avatar_from_storage(user_id)
        
        if avatar_data is None:
            return jsonify({"Error": "Not found"}), 404
        
        # Return the file
        return send_file(
            io.BytesIO(avatar_data),
            mimetype='image/png',
            as_attachment=False
        )
        
    except Exception as e:
        print(f"Error in get_user_avatar: {e}")
        return jsonify({"Error": "Internal server error"}), 500

@user_bp.route('/users/<int:user_id>/avatar', methods=['DELETE'])
@requires_auth
def delete_user_avatar(payload, user_id):
    """Delete user avatar"""
    try:
        client = datastore.Client()
        
        # Check permissions
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users or users[0].key.id != user_id:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Check if avatar exists and delete it
        if delete_avatar_from_storage(user_id):
            return '', 204
        else:
            return jsonify({"Error": "Not found"}), 404
        
    except Exception as e:
        print(f"Error in delete_user_avatar: {e}")
        return jsonify({"Error": "Internal server error"}), 500