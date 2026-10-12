
from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def home():
    return {"message": "Welcome to FastAPI"}


@app.get("/api/data")
def get_data():
    return {
        "message": "Hello from FastAPI!",
        "course": "Python and FastAPI",
        "status": "Success"
    }
