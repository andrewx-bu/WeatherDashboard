class User:
    def __init__(self, id, username, password_hash, salt):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.salt = salt
    
    def to_dict(self):
        # Converts a User object to a dictionary.
        return {
            'id': self.id,
            'username': self.username,
        }