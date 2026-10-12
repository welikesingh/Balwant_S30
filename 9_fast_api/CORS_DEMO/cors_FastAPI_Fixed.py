
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow the HTML frontend to call this API
origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


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
