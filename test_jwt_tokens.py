import jwt
import datetime

SECRET_KEY = "61i489^f7d_h&l*2f&9_u71j^_a7fy!di939^lgo_u(lg%m99i"   # same as in your FastAPI/Django settings
ALGORITHM = "HS256"

payload = {
    "sub": "Arjun",  # could be UUID or email
    "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30),
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(token)
