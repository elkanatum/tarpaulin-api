from google.cloud import storage
import os

def get_storage_client():
    """Get Cloud Storage client"""
    return storage.Client()

def upload_avatar(user_id, file_content, filename):
    """Upload avatar to Cloud Storage"""
    client = get_storage_client()
    bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
    bucket = client.bucket(bucket_name)
    
    blob_name = f"avatars/{user_id}.png"
    blob = bucket.blob(blob_name)
    blob.upload_from_string(file_content, content_type='image/png')
    
    return blob_name

def get_avatar(user_id):
    """Get avatar from Cloud Storage"""
    client = get_storage_client()
    bucket_name = os.environ.get('BUCKET_NAME', 'tume-tarpaulin-avatars')
    bucket = client.bucket(bucket_name)
    
    blob_name = f"avatars/{user_id}.png"
    blob = bucket.blob(blob_name)
    
    if blob.exists():
        return blob.download_as_bytes()
    return None

def delete_avatar(user_id):
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
