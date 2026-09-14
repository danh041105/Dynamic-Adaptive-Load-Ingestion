from core.security import (
    create_access_token,
    decode_access_token
)


token = create_access_token({
    "sub": "1",
    "username": "anhnd194",
    "role": "Data Engineer"
})

print("TOKEN:")
print(token)


payload = decode_access_token(token)

print("PAYLOAD:")
print(payload)