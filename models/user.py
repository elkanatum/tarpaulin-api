class User:
    """
    User model representing users in the Tarpaulin system.
    Note: This is a simple data class - actual storage is handled by Datastore.
    """
    def __init__(self, id=None, sub=None, role=None, avatar_url=None, courses=None):
        self.id = id
        self.sub = sub
        self.role = role
        self.avatar_url = avatar_url
        self.courses = courses or []
    
    def to_dict(self):
        """Convert user to dictionary for JSON responses"""
        result = {
            "id": self.id,
            "role": self.role,
            "sub": self.sub
        }
        
        if self.avatar_url:
            result["avatar_url"] = self.avatar_url
            
        if self.role in ['instructor', 'student']:
            result["courses"] = self.courses
            
        return result