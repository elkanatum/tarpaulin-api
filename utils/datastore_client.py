from google.cloud import datastore
import os

def get_datastore_client():
    """Get Datastore client"""
    return datastore.Client()

def create_user_entities():
    """Create the 9 required user entities in Datastore"""
    client = get_datastore_client()
    
    users_data = [
        {"role": "admin", "sub": "ADMIN_SUB_FROM_AUTH0"},
        {"role": "instructor", "sub": "INSTRUCTOR1_SUB_FROM_AUTH0"},
        {"role": "instructor", "sub": "INSTRUCTOR2_SUB_FROM_AUTH0"},
        {"role": "student", "sub": "STUDENT1_SUB_FROM_AUTH0"},
        {"role": "student", "sub": "STUDENT2_SUB_FROM_AUTH0"},
        {"role": "student", "sub": "STUDENT3_SUB_FROM_AUTH0"},
        {"role": "student", "sub": "STUDENT4_SUB_FROM_AUTH0"},
        {"role": "student", "sub": "STUDENT5_SUB_FROM_AUTH0"},
        {"role": "student", "sub": "STUDENT6_SUB_FROM_AUTH0"},
    ]
    
    for user_data in users_data:
        key = client.key('users')
        entity = datastore.Entity(key=key)
        entity.update(user_data)
        client.put(entity)
    
    print("User entities created successfully")
