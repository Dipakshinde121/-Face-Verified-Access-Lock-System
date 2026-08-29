from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import base64
import jwt
from datetime import datetime, timedelta
from typing import List

from server.database import (
    init_db, add_student_server, get_student_server, 
    log_event_server, get_logs_server
)

app = FastAPI(title="Lab Access Control Central API (JWT Protected)")

# --- JWT OAUTH2 SECURITY CONFIGURATION ---
JWT_SECRET = "highly-complex-production-signature-key-2026"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# In a real system, these would be in a database of registered devices.
# For this lab, we authorize "lab-pc-01" as a trusted client.
REGISTERED_CLIENTS = {
    "lab-pc-01": "secure-lab-password-123"
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        client_id: str = payload.get("sub")
        if client_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return client_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please authenticate again.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token signature")

# --- ENDPOINTS ---

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/token", summary="Issue JWT Access Token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Verify the Lab PC's credentials
    client_id = form_data.username
    client_secret = form_data.password
    
    if client_id not in REGISTERED_CLIENTS or REGISTERED_CLIENTS[client_id] != client_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Client ID or Secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Issue the temporary JWT
    access_token = create_access_token(data={"sub": client_id})
    return {"access_token": access_token, "token_type": "bearer"}


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

@app.post("/register", dependencies=[Depends(verify_jwt_token)])
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

@app.get("/student/{roll_number}", dependencies=[Depends(verify_jwt_token)])
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

@app.post("/log", dependencies=[Depends(verify_jwt_token)])
def log_event(req: LogEventRequest):
    success = log_event_server(req.roll_number, req.event, req.severity)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to write log")
    return {"message": "Event logged"}

@app.get("/logs", dependencies=[Depends(verify_jwt_token)])
def get_logs():
    return {"logs": get_logs_server()}
