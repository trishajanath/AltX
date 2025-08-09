import hashlib

class AuthManager:
    def hash_password(self, password):
        # VULNERABLE: MD5 is cryptographically broken
        return hashlib.md5(password.encode()).hexdigest()
    
    def verify_password(self, password, hash):
        # VULNERABLE: Still using MD5
        return hashlib.md5(password.encode()).hexdigest() == hash
    
    def generate_session_token(self):
        # VULNERABLE: Predictable token generation
        import time
        return str(int(time.time()))
    
    def check_admin(self, user_role):
        # VULNERABLE: Weak authorization check
        if user_role == "admin" or user_role == "administrator":
            return True
        return False

# VULNERABLE: Hardcoded admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"
