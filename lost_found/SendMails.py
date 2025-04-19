from fastapi import FastAPI, Form, UploadFile, File
from pymongo import MongoClient
from bson.objectid import ObjectId
import base64
import smtplib
from email.mime.text import MIMEText

app = FastAPI()
client = MongoClient("mongodb://localhost:27017/")
db = client["lost_and_found"]
lost_collection = db["lost"]
found_collection = db["found"]


def send_email(subject, body, to_email):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "your_email@example.com"
    msg["To"] = to_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("your_email@example.com", "your_password")
        server.send_message(msg)


def encode_image_to_base64(file):
    return base64.b64encode(file.file.read()).decode('utf-8')


@app.post("/found")
async def report_found_item(description: str = Form(...), email: str = Form(...), image: UploadFile = File(None)):
    doc = {
        "description": description,
        "email": email
    }
    if image:
        doc["image"] = encode_image_to_base64(image)
    result = found_collection.insert_one(doc)

    # Find potential match in lost items
    match = lost_collection.find_one({"description": {"$regex": description, "$options": "i"}})
    if match:
        # Notify the owner of the lost item
        send_email(
            "Good news! Your lost item was found",
            f"Hi! Someone found something that matches your lost item:\n\n{description}",
            match["email"]
        )
        # Thank the founder
        send_email(
            "Thank you for reporting a found item",
            f"Thank you for posting the found item: '{description}'. We’ve notified the potential owner!",
            email
        )
        # Remove the matched lost item
        lost_collection.delete_one({"_id": ObjectId(match["_id"])})

    return {"status": "ok"}
