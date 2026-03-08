from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import sessionmaker, declarative_base
from minio import Minio
import psycopg2
import time
import uuid
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # untuk development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# WAIT FOR POSTGRESQL
# =========================

def wait_for_db():
    while True:
        try:
            conn = psycopg2.connect(
                host="postgres",
                database="usersdb",
                user="admin",
                password="admin"
            )
            conn.close()
            print("PostgreSQL siap!")
            break
        except:
            print("Menunggu PostgreSQL...")
            time.sleep(3)

wait_for_db()

# =========================
# DATABASE CONFIG
# =========================

DATABASE_URL = "postgresql://admin:admin@postgres:5432/usersdb"

engine = create_engine(DATABASE_URL)

Session = sessionmaker(bind=engine)

Base = declarative_base()

# =========================
# MODEL DATABASE
# =========================

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String)

    email = Column(String)

    photo_url = Column(String)


Base.metadata.create_all(engine)

# =========================
# MINIO CONFIG
# =========================

minio_client = Minio(
    "minio:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

BUCKET = "photos"

MAX_FILE_SIZE = 5 * 1024 * 1024

# =========================
# CREATE USER
# =========================

@app.post("/users")
async def create_user(
    name: str = Form(...),
    email: str = Form(...),
    photo: UploadFile = File(...)
):

    file_data = await photo.read()

    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File lebih dari 5MB"
        )

    filename = str(uuid.uuid4()) + "_" + photo.filename

    with open(filename, "wb") as f:
        f.write(file_data)

    minio_client.fput_object(
        BUCKET,
        filename,
        filename
    )

    photo_url = f"http://192.168.1.12:9000/{BUCKET}/{filename}"

    db = Session()

    user = User(
        name=name,
        email=email,
        photo_url=photo_url
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    os.remove(filename)

    return {
        "message": "user created",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "photo": user.photo_url
        }
    }

# =========================
# GET ALL USERS
# =========================

@app.get("/users")
def get_users():

    db = Session()

    users = db.query(User).all()

    return users

# =========================
# GET USER BY ID
# =========================

@app.get("/users/{user_id}")
def get_user(user_id: int):

    db = Session()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User tidak ditemukan"
        )

    return user

# =========================
# UPDATE USER
# =========================

@app.put("/users/{user_id}")
def update_user(
    user_id: int,
    name: str,
    email: str
):

    db = Session()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User tidak ditemukan"
        )

    user.name = name

    user.email = email

    db.commit()

    return {"message": "user updated"}

# =========================
# DELETE USER
# =========================

@app.delete("/users/{user_id}")
def delete_user(user_id: int):

    db = Session()

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User tidak ditemukan"
        )

    filename = user.photo_url.split("/")[-1]

    minio_client.remove_object(
        BUCKET,
        filename
    )

    db.delete(user)

    db.commit()

    return {"message": "user deleted"}
