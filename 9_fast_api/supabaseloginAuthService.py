from operator import ge, le
import os
from urllib import response
from dotenv import load_dotenv
from supabase import create_client, Client
load_dotenv()
from fastapi import FastAPI
from pydantic import BaseModel

#Encrupt password save into db
import bcrypt

app = FastAPI()

SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SUPABASE_URL = os.getenv("SUPABASE_URL")
client = create_client(SUPABASE_URL, SUPABASE_KEY)


class User(BaseModel):
    username: str
    password: str
####################Authentication without Hashing####################

## registor user without hashed password
@app.post("/register")
def register_user(user: User):
   response =  client.table("users").insert({"username": user.username, "password": user.password}).execute()
   return response

## Login user without hashed password
@app.post("/login")
def login_user(user: User):
    response = client.table("users").select("*").eq("username", user.username).eq("password", user.password).execute()
    return response

####################Authentication with Hashing####################
## registor user with hashed password using bcrypt
@app.post("/register_hashed")
def register_user_hashed(user: User):
    print("encode into utf-8 :", user.password.encode('utf-8'))
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    print("Hashed password:", hashed_password)
    response = client.table("users").insert({"username": user.username, "password": hashed_password.decode('utf-8')}).execute()
    return response

## registor user with hashed password using bcrypt
@app.post("/login_hashed")
def login_user_hashed(user: User):
    response = client.table("users").select("*").eq("username", user.username).execute()
    print("Checking password for user:", user.username)
    print("Provided password:", user.password)
    print("Stored hashed password:", response.data[0]['password'].encode('utf-8'))
    print("Password entered:", user.password.encode('utf-8'))  
    if response.data and bcrypt.checkpw(user.password.encode('utf-8'), response.data[0]['password'].encode('utf-8')):
        return {"status": "success"}
    return {"status": "failure"}


####################JWT (Json web Token) Authentication####################
from fastapi import Depends
from fastapi.security import HTTPBearer
import jwt


SECRET_KEY= "euron123"
security = HTTPBearer()

## Generate Access Token
@app.post("/login_for_access_token")
def login_for_access_token(user: User):
    if user.username == "admin" and user.password == "admin":
        access_token = jwt.encode({"sub": user.username}, SECRET_KEY, algorithm="HS256")
        return {"access_token": access_token}
    return {"error": "Invalid credentials"}



####################JWT (Json web Token) Authentication and using token####################
## https://www.jwt.io/   use to decode and encode JWT tokens manually
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from supabase import create_client
from pwdlib import PasswordHash
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import jwt
import os


SECRET_KEY= os.getenv("SECRET_KEY")
security = HTTPBearer()
password_hash = PasswordHash.recommended()

#Store user and password as hashed using pwdlib
@app.post("/register_hashed_pwdlib")
def register_user_hashed(user: User):
    hashed_password = password_hash.hash(user.password)
    response = client.table("users").insert({"username": user.username, "password": hashed_password}).execute()
    return response


# Login with user and password hashed using pwdlib
# Generate Access Token after successful login
@app.post("/login_hashed_pwdlib")
def login_user_hashed_pwdlib(user: User):
    response = client.table("users").select("*").eq("username", user.username).execute()
    if response.data and password_hash.verify(user.password, response.data[0]['password']):
        access_token = jwt.encode({
                                   "sub": user.username,
                                   "exp": datetime.now(timezone.utc) + timedelta(minutes=30) # Token expiration time
                                   }, 
                                   SECRET_KEY, 
                                   algorithm="HS256")
        return {"status": "success", "access_token": access_token}
    return {"status": "failure"}

## Authorize using JWT token that we can get from /login_hashed_pwdlib api
@app.get("/access_profile")
def access_profile(token=Depends(security)):
    decoded = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
    return {"status": "success", "username": decoded["sub"]}
####################JWT (Json web Token) Authentication and using token####################


