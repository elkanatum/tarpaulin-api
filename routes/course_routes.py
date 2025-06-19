from flask import Blueprint, request, jsonify
from google.cloud import datastore
from utils.auth import requires_auth

course_bp = Blueprint('courses', __name__)

@course_bp.route('/courses', methods=['GET'])
def get_all_courses():
    """Get all courses with pagination - Unprotected"""
    try:
        client = datastore.Client()
        
        # Get pagination parameters
        limit = int(request.args.get('limit', 3))
        offset = int(request.args.get('offset', 0))
        
        # Query courses ordered by subject
        query = client.query(kind='courses')
        query.order = ['subject']
        
        # Apply pagination
        courses = list(query.fetch(limit=limit, offset=offset))
        
        # Build response
        result = []
        for course in courses:
            course_data = dict(course)
            course_data['id'] = course.key.id
            course_data['self'] = f"{request.host_url.rstrip('/')}/courses/{course.key.id}"
            result.append(course_data)
        
        response = {
            "courses": result
        }
        
        # Add next link if there might be more results
        if len(courses) == limit:
            next_offset = offset + limit
            response["next"] = f"{request.host_url.rstrip('/')}/courses?limit={limit}&offset={next_offset}"
        
        return jsonify(response), 200
    except Exception as e:
        print(f"Error in get_all_courses: {e}")
        return jsonify({"Error": "Internal server error"}), 500

@course_bp.route('/courses/<int:course_id>', methods=['GET'])
def get_course(course_id):
    """Get a specific course - Unprotected"""
    try:
        client = datastore.Client()
        
        course_key = client.key('courses', course_id)
        course = client.get(course_key)
        
        if not course:
            return jsonify({"Error": "Not found"}), 404
        
        result = dict(course)
        result['id'] = course.key.id
        result['self'] = f"{request.host_url.rstrip('/')}/courses/{course.key.id}"
        
        return jsonify(result), 200
    except Exception as e:
        print(f"Error in get_course: {e}")
        return jsonify({"Error": "Internal server error"}), 500

@course_bp.route('/courses', methods=['POST'])
@requires_auth
def create_course(payload):
    """Create a course - Admin only"""
    try:
        client = datastore.Client()
        
        # Check if user is admin
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users or users[0]['role'] != 'admin':
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        data = request.get_json()
        required_fields = ['subject', 'number', 'title', 'term', 'instructor_id']
        
        if not data or not all(field in data for field in required_fields):
            return jsonify({"Error": "The request body is invalid"}), 400
        
        # Validate instructor exists and has instructor role
        instructor_key = client.key('users', data['instructor_id'])
        instructor = client.get(instructor_key)
        
        if not instructor or instructor['role'] != 'instructor':
            return jsonify({"Error": "The request body is invalid"}), 400
        
        # Create course
        course_key = client.key('courses')
        course = datastore.Entity(key=course_key)
        course.update({
            'subject': data['subject'],
            'number': data['number'],
            'title': data['title'],
            'term': data['term'],
            'instructor_id': data['instructor_id']
        })
        client.put(course)
        
        # Return course data
        result = dict(course)
        result['id'] = course.key.id
        result['self'] = f"{request.host_url.rstrip('/')}/courses/{course.key.id}"
        
        return jsonify(result), 201
        
    except Exception as e:
        print(f"Error in create_course: {e}")
        return jsonify({"Error": "The request body is invalid"}), 400

@course_bp.route('/courses/<int:course_id>', methods=['PATCH'])
@requires_auth
def update_course(payload, course_id):
    """Update a course - Admin only"""
    try:
        client = datastore.Client()
        
        # Check if user is admin
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users or users[0]['role'] != 'admin':
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Check if course exists
        course_key = client.key('courses', course_id)
        course = client.get(course_key)
        
        if not course:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({"Error": "The request body is invalid"}), 400
        
        # Validate instructor_id if provided
        if 'instructor_id' in data:
            instructor_key = client.key('users', data['instructor_id'])
            instructor = client.get(instructor_key)
            if not instructor or instructor['role'] != 'instructor':
                return jsonify({"Error": "The request body is invalid"}), 400
        
        # Update course fields
        allowed_fields = ['subject', 'number', 'title', 'term', 'instructor_id']
        for field in allowed_fields:
            if field in data:
                course[field] = data[field]
        
        client.put(course)
        
        result = dict(course)
        result['id'] = course.key.id
        result['self'] = f"{request.host_url.rstrip('/')}/courses/{course.key.id}"
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in update_course: {e}")
        return jsonify({"Error": "The request body is invalid"}), 400

@course_bp.route('/courses/<int:course_id>', methods=['DELETE'])
@requires_auth
def delete_course(payload, course_id):
    """Delete a course - Admin only"""
    try:
        client = datastore.Client()
        
        # Check if user is admin
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users or users[0]['role'] != 'admin':
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Check if course exists
        course_key = client.key('courses', course_id)
        course = client.get(course_key)
        
        if not course:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Delete all enrollments for this course
        enrollment_query = client.query(kind='enrollments')
        enrollment_query.add_filter('course_id', '=', course_id)
        enrollments = list(enrollment_query.fetch())
        
        for enrollment in enrollments:
            client.delete(enrollment.key)
        
        # Delete the course
        client.delete(course_key)
        
        return '', 204
        
    except Exception as e:
        print(f"Error in delete_course: {e}")
        return jsonify({"Error": "Internal server error"}), 500

@course_bp.route('/courses/<int:course_id>/students', methods=['PATCH'])
@requires_auth
def update_enrollment(payload, course_id):
    """Update enrollment in a course - Admin or course instructor only"""
    try:
        client = datastore.Client()
        
        # Get requesting user
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        requesting_user = users[0]
        
        # Check if course exists
        course_key = client.key('courses', course_id)
        course = client.get(course_key)
        
        if not course:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Check permissions (admin or instructor of this course)
        if requesting_user['role'] != 'admin' and course['instructor_id'] != requesting_user.key.id:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        data = request.get_json()
        if not data or 'add' not in data or 'remove' not in data:
            return jsonify({"Error": "Enrollment data is invalid"}), 409
        
        add_students = data['add']
        remove_students = data['remove']
        
        # Validate enrollment data
        all_students = add_students + remove_students
        if len(set(all_students)) != len(all_students):
            return jsonify({"Error": "Enrollment data is invalid"}), 409
        
        # Check if all IDs are valid students
        for student_id in all_students:
            if student_id:  # Skip empty values
                student_key = client.key('users', student_id)
                student = client.get(student_key)
                if not student or student['role'] != 'student':
                    return jsonify({"Error": "Enrollment data is invalid"}), 409
        
        # Add students (create enrollment entities)
        for student_id in add_students:
            if student_id:  # Skip empty values
                # Check if already enrolled
                enrollment_query = client.query(kind='enrollments')
                enrollment_query.add_filter('course_id', '=', course_id)
                enrollment_query.add_filter('student_id', '=', student_id)
                existing = list(enrollment_query.fetch())
                
                if not existing:
                    enrollment_key = client.key('enrollments')
                    enrollment = datastore.Entity(key=enrollment_key)
                    enrollment.update({
                        'course_id': course_id,
                        'student_id': student_id
                    })
                    client.put(enrollment)
        
        # Remove students (delete enrollment entities)
        for student_id in remove_students:
            if student_id:  # Skip empty values
                enrollment_query = client.query(kind='enrollments')
                enrollment_query.add_filter('course_id', '=', course_id)
                enrollment_query.add_filter('student_id', '=', student_id)
                enrollments = list(enrollment_query.fetch())
                
                for enrollment in enrollments:
                    client.delete(enrollment.key)
        
        return '', 200
        
    except Exception as e:
        print(f"Error in update_enrollment: {e}")
        return jsonify({"Error": "Enrollment data is invalid"}), 409

@course_bp.route('/courses/<int:course_id>/students', methods=['GET'])
@requires_auth
def get_enrollment(payload, course_id):
    """Get enrollment for a course - Admin or course instructor only"""
    try:
        client = datastore.Client()
        
        # Get requesting user
        query = client.query(kind='users')
        query.add_filter('sub', '=', payload['sub'])
        users = list(query.fetch())
        
        if not users:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        requesting_user = users[0]
        
        # Check if course exists
        course_key = client.key('courses', course_id)
        course = client.get(course_key)
        
        if not course:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Check permissions (admin or instructor of this course)
        if requesting_user['role'] != 'admin' and course['instructor_id'] != requesting_user.key.id:
            return jsonify({"Error": "You don't have permission on this resource"}), 403
        
        # Get enrolled students
        enrollment_query = client.query(kind='enrollments')
        enrollment_query.add_filter('course_id', '=', course_id)
        enrollments = list(enrollment_query.fetch())
        
        student_ids = [enrollment['student_id'] for enrollment in enrollments]
        
        return jsonify(student_ids), 200
        
    except Exception as e:
        print(f"Error in get_enrollment: {e}")
        return jsonify({"Error": "Internal server error"}), 500