class Course:
    """
    Course model representing courses in the Tarpaulin system.
    Note: This is a simple data class - actual storage is handled by Datastore.
    """
    def __init__(self, id=None, subject=None, number=None, title=None, term=None, instructor_id=None, self_url=None):
        self.id = id
        self.subject = subject
        self.number = number
        self.title = title
        self.term = term
        self.instructor_id = instructor_id
        self.self_url = self_url
    
    def to_dict(self):
        """Convert course to dictionary for JSON responses"""
        return {
            "id": self.id,
            "subject": self.subject,
            "number": self.number,
            "title": self.title,
            "term": self.term,
            "instructor_id": self.instructor_id,
            "self": self.self_url
        }