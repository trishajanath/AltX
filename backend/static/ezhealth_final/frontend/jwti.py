from jose import jwt

SECRET_KEY = "e8b3f5d7a1c9f2b6e4d8a0c7b3f5d7a1c9f2b6e4d8a0c7b3f5d7a1c9f2b6e4d8"
ALGORITHM = "HS256"

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0cmlzaGFqYW5hdGhAZ21haWwuY29tIiwiZXhwIjoxNzQwNzExNzQwfQ.5fqdQu5AaVw_KhqPRyrgXAa8kqcEv5YEQY7PpIjpcNA"

try:
    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    print("✅ Token is valid:", decoded)
except Exception as e:
    print("❌ Token is invalid:", str(e))

