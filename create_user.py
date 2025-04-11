import bcrypt

plain_password = "123"  # Change to your desired password
hashed = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

print("Hashed password:", hashed.decode('utf-8'))
