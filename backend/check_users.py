from database import MongoDB

db = MongoDB.get_database()
users = list(db.users.find())

print(f"\n{'='*60}")
print(f"USERS IN DATABASE: {len(users)} total")
print(f"{'='*60}\n")

if users:
    for i, u in enumerate(users, 1):
        print(f"{i}. Email: {u.get('email')}")
        print(f"   Username: {u.get('username')}")
        print(f"   ID: {u.get('_id')}")
        print(f"   Active: {u.get('is_active', False)}")
        print()
else:
    print("No users found in database!\n")
    print("To create a test user, sign up through the UI or run:")
    print("  POST http://localhost:8000/api/auth/signup")
    print("  Body: {\"email\": \"test@example.com\", \"username\": \"testuser\", \"password\": \"password123\"}")
