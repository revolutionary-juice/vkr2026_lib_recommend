from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User

db = SessionLocal()

users = db.query(User).all()
for user in users:
    if not user.password_hash.startswith("$2b$"):
        plain = user.password_hash
        user.password_hash = hash_password(plain)
        print(f"Хешировано: {user.username}")
    else:
        print(f"Уже хеш:    {user.username}")

db.commit()
db.close()
print("Готово.")
