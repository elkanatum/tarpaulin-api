from flask import Flask, request, jsonify
import os

# Import route modules
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.course_routes import course_bp

app = Flask(__name__)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(course_bp)

@app.route('/')
def home():
    return jsonify({"message": "Tarpaulin API is running"}), 200

@app.route('/test-datastore')
def test_datastore():
    try:
        from google.cloud import datastore
        client = datastore.Client()
        
        key = client.key('test', 'test1')
        entity = datastore.Entity(key=key)
        entity['message'] = 'Datastore is working!'
        client.put(entity)
        
        retrieved = client.get(key)
        return jsonify({"status": "success", "message": retrieved['message']}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/populate-users-real')
def populate_users_real():
    try:
        from google.cloud import datastore
        client = datastore.Client()
        
        # Delete existing users first to avoid duplicates
        query = client.query(kind='users')
        existing_users = list(query.fetch())
        for user in existing_users:
            client.delete(user.key)
        
        # Real user data with actual sub values from Auth0
        users_data = [
            {"role": "admin", "sub": "auth0|683b8e5d7653872d9ac7444c"},
            {"role": "instructor", "sub": "auth0|683b8efa7653872d9ac74459"},
            {"role": "instructor", "sub": "auth0|683b8f277653872d9ac7445f"},
            {"role": "student", "sub": "auth0|683b8f4ba7e405995ecde2e8"},
            {"role": "student", "sub": "auth0|683b8f67a7e405995ecde2ec"},
            {"role": "student", "sub": "auth0|683b8f84a7e405995ecde2ef"},
            {"role": "student", "sub": "auth0|683b8fa7e405995ecde2f3"},
            {"role": "student", "sub": "auth0|683b8fb3a7e405995ecde2f6"},
            {"role": "student", "sub": "auth0|683b8fc4a7e405995ecde2f9"},
        ]
        
        created_users = []
        for user_data in users_data:
            key = client.key('users')
            entity = datastore.Entity(key=key)
            entity.update(user_data)
            client.put(entity)
            
            result = dict(entity)
            result['id'] = entity.key.id
            created_users.append(result)
        
        return jsonify({"status": "success", "users_created": len(created_users), "users": created_users}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/decode-token', methods=['POST'])
def decode_token():
    try:
        import jwt
        data = request.get_json()
        token = data.get('token')
        
        decoded = jwt.decode(token, options={"verify_signature": False})
        return jsonify({"sub": decoded.get("sub"), "email": decoded.get("email")}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/check-storage-bucket')
def check_storage_bucket():
    """Check if the Cloud Storage bucket exists and is accessible"""
    try:
        from google.cloud import storage
        
        storage_client = storage.Client()
        bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
        
        try:
            bucket = storage_client.bucket(bucket_name)
            bucket.reload()  # This will raise an exception if bucket doesn't exist
            
            # List some blobs to test access
            blobs = list(bucket.list_blobs(max_results=5))
            
            return jsonify({
                "status": "success",
                "bucket_name": bucket_name,
                "bucket_exists": True,
                "blob_count": len(blobs),
                "sample_blobs": [blob.name for blob in blobs]
            }), 200
            
        except Exception as bucket_error:
            return jsonify({
                "status": "error",
                "bucket_name": bucket_name,
                "bucket_exists": False,
                "error": str(bucket_error),
                "suggestion": "Create the bucket: gsutil mb gs://" + bucket_name
            }), 404
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/fix-student-subs', methods=['POST'])
def fix_student_subs():
    """Fix the student sub matching issue"""
    try:
        from google.cloud import datastore
        import jwt
        
        client = datastore.Client()
        data = request.get_json()
        
        if not data:
            return jsonify({"Error": "Send JWT tokens"}), 400
        
        # Get all current users
        query = client.query(kind='users')
        all_users = list(query.fetch())
        
        # Extract student tokens and update subs
        student_tokens = []
        for key, token in data.items():
            if key.startswith('student') and key.endswith('_jwt'):
                try:
                    decoded = jwt.decode(token, options={"verify_signature": False})
                    sub = decoded.get('sub')
                    if sub:
                        student_num = int(key.replace('student', '').replace('_jwt', ''))
                        student_tokens.append((student_num, sub))
                except Exception as e:
                    print(f"Error decoding {key}: {e}")
        
        # Sort by student number
        student_tokens.sort(key=lambda x: x[0])
        
        # Get all students from database
        students = [u for u in all_users if u.get('role') == 'student']
        students.sort(key=lambda x: x.key.id)  # Sort by ID for consistent assignment
        
        updated_count = 0
        for i, (student_num, sub) in enumerate(student_tokens):
            if i < len(students):
                student = students[i]
                student['sub'] = sub
                client.put(student)
                updated_count += 1
                print(f"Updated student {student.key.id} with sub {sub}")
        
        return jsonify({
            "status": "success",
            "students_updated": updated_count,
            "message": "Student subs have been updated. Run the tests again."
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create-test-avatar', methods=['POST'])
def create_test_avatar():
    """Create a test avatar for testing purposes"""
    try:
        from google.cloud import storage
        import base64
        
        data = request.get_json()
        user_id = data.get('user_id', 5642368648740864)  # Default to student1 ID from your tests
        
        # Create a test image (1x1 PNG)
        test_image_data = base64.b64decode(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
        )
        
        # Upload to Cloud Storage
        storage_client = storage.Client()
        bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
        bucket = storage_client.bucket(bucket_name)
        
        blob_name = f"avatars/{user_id}.png"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(test_image_data, content_type='image/png')
        
        return jsonify({
            "status": "success",
            "message": "Test avatar created",
            "user_id": user_id,
            "blob_name": blob_name,
            "avatar_url": f"http://127.0.0.1:8080/users/{user_id}/avatar"
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/debug-users')
def debug_users():
    """Debug endpoint to check user data"""
    try:
        from google.cloud import datastore
        client = datastore.Client()
        
        # Get all users
        query = client.query(kind='users')
        all_users = list(query.fetch())
        
        result = {
            "total_users": len(all_users),
            "users": []
        }
        
        for user in all_users:
            user_data = {
                "id": user.key.id,
                "role": user.get('role', 'NO_ROLE'),
                "sub": user.get('sub', 'NO_SUB'),
                "all_properties": list(user.keys())
            }
            result["users"].append(user_data)
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)