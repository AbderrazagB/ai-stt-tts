import base64
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient

app = FastAPI()

# CORS if your frontend is hosted elsewhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")
db = client["lost_and_found"]
lost_collection = db["lost"]
found_collection = db["found"]

def encode_image_to_base64(file: UploadFile):
    return base64.b64encode(file.file.read()).decode('utf-8')

@app.post("/report/lost")
async def report_lost_item(
    description: str = Form(...),
    email: str = Form(...),
    image: UploadFile = None
):
    doc = {"description": description, "email": email}
    if image:
        doc["image"] = encode_image_to_base64(image)
    result = lost_collection.insert_one(doc)
    return {"message": "Lost item reported", "id": str(result.inserted_id)}

@app.post("/report/found")
async def report_found_item(
    description: str = Form(...),
    email: str = Form(...),
    image: UploadFile = None
):
    doc = {"description": description, "email": email}
    if image:
        doc["image"] = encode_image_to_base64(image)
    result = found_collection.insert_one(doc)
    return {"message": "Found item reported", "id": str(result.inserted_id)}
