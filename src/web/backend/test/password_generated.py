from core.security import hash_password

plain_password = "123456"
hashed_password = hash_password(plain_password)
print(hashed_password)