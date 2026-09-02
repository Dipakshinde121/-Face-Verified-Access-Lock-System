from fastapi import FastAPI, Depends, HTTPException, Security, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import base64
import jwt
from datetime import datetime, timedelta
from typing import List

from server.database import (
    init_db, register_device_server, get_device_server,
    add_student_server, get_student_server, 
    log_event_server, get_logs_server
)

import uuid
import secrets

app = FastAPI(title="Lab Access Control Central API (JWT Protected)")

# Mount the Vaporwave Dashboard
app.mount("/dashboard", StaticFiles(directory="frontend", html=True), name="dashboard")

# --- JWT OAUTH2 SECURITY CONFIGURATION ---
JWT_SECRET = "highly-complex-production-signature-key-2026"
JWT_ALGORITHM = "HS256"
# Principle of Least Privilege: Short-lived tokens to reduce damage window
ACCESS_TOKEN_EXPIRE_HOURS = 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict):
    to_encode = data.copy()
    now = datetime.utcnow()
    expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"iat": now, "exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        device_id: str = payload.get("device_id")
        if device_id is None:
            raise HTTPException(status_code=403, detail="Invalid token payload")
            
        # Additional Security Check: Was the device revoked mid-session?
        device = get_device_server(device_id)
        if not device or device.get("is_revoked"):
            print(f"[SECURITY] Access Denied: Device {device_id} has been revoked!")
            log_event_server("SYSTEM", f"API_AUTH_FAILED_REVOKED_DEVICE ({device_id})", severity="HIGH")
            raise HTTPException(status_code=403, detail="Device has been revoked by administrator.")
            
        return device_id
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired. Please authenticate again.")
    except jwt.InvalidTokenError:
        print("[SECURITY] Invalid or tampered JWT token received!")
        log_event_server("SYSTEM", "API_AUTH_FAILED_INVALID_TOKEN", severity="HIGH")
        raise HTTPException(status_code=403, detail="Invalid token signature")

# --- ENDPOINTS ---

@app.on_event("startup")
def startup_event():
    init_db()

@app.post("/device/register", summary="Dynamically Register a New Lab PC")
def register_device():
    """
    Registers a new Lab PC. Returns a unique device_id and device_secret.
    In a real enterprise, this endpoint would itself be protected by an admin token,
    or devices would be pre-provisioned. For this project, we allow dynamic provisioning.
    """
    device_id = f"lab-pc-{uuid.uuid4().hex[:8]}"
    device_secret = secrets.token_urlsafe(32)
    
    success = register_device_server(device_id, device_secret)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to register device")
        
    return {"device_id": device_id, "device_secret": device_secret}

@app.post("/token", summary="Issue Per-Device JWT Access Token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Verify the Lab PC's dynamic credentials
    device_id = form_data.username
    device_secret = form_data.password
    
    device = get_device_server(device_id)
    
    if not device or device.get("device_secret") != device_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect Device ID or Secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if device.get("is_revoked"):
        raise HTTPException(status_code=403, detail="Device has been revoked.")
    
    # Issue the temporary JWT with the device_id claim
    access_token = create_access_token(data={"device_id": device_id})
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

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Run the server over HTTPS using our self-signed TLS certs
    key_path = os.path.join(os.path.dirname(__file__), "key.pem")
    cert_path = os.path.join(os.path.dirname(__file__), "cert.pem")
    
    uvicorn.run(
        "server.main:app", 
        host="127.0.0.1", 
        port=8000, 
        ssl_keyfile=key_path, 
        ssl_certfile=cert_path
    )