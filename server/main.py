from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
import base64
from typing import List

from server.database import (
    init_db, add_student_server, get_student_server, 
    log_event_server, get_logs_server
)

app = FastAPI(title="Lab Access Control Central API")

# Setup API Key authentication
API_KEY = "super-secret-lab-key" # In production, use OAuth2/JWT or load from env vars
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    return api_key_header

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Pydantic models for data validation
class RegisterRequest(BaseModel):
    roll_number: str
    name: str
    face_encoding_b64: str  # Base64 encoded encrypted bytes
    totp_secret_b64: str    # Base64 encoded encrypted bytes

class LogEventRequest(BaseModel):
    roll_number: str
    event: str
    severity: str = "INFO"

@app.post("/register", dependencies=[Depends(get_api_key)])
def register_student(req: RegisterRequest):
    try:
        enc_face = base64.b64decode(req.face_encoding_b64)
        enc_totp = base64.b64decode(req.totp_secret_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 payload")
        
    success = add_student_server(req.roll_number, req.name, enc_face, enc_totp)
    if not success:
        raise HTTPException(status_code=500, detail="Database write failed")
    return {"message": f"Successfully registered {req.roll_number}"}

@app.get("/student/{roll_number}", dependencies=[Depends(get_api_key)])
def get_student(roll_number: str):
    data = get_student_server(roll_number)
    if not data:
        raise HTTPException(status_code=404, detail="Student not found")
        
    # Return as base64 so the client can decode back to bytes, then decrypt locally (E2EE)
    return {
        "roll_number": roll_number,
        "name": data["name"],
        "face_encoding_b64": base64.b64encode(data["face_encoding"]).decode('utf-8'),
        "totp_secret_b64": base64.b64encode(data["totp_secret"]).decode('utf-8'),
        "registered_date": data["registered_date"]
    }

@app.post("/log", dependencies=[Depends(get_api_key)])
def log_event(req: LogEventRequest):
    success = log_event_server(req.roll_number, req.event, req.severity)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to write log")
    return {"message": "Event logged"}

@app.get("/logs", dependencies=[Depends(get_api_key)])
def get_logs():
    return {"logs": get_logs_server()}
