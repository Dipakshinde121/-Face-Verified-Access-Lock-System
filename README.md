# Face-Verified Access Lock System

A high-assurance, continuous multi-factor authentication (MFA) system designed to secure computer laboratory environments against insider threats, impersonation, and physical session hijacking.

This project implements a **Centralized Client-Server Architecture** operating on a **Zero-Trust** model, utilizing biometric continuous verification, Time-Based One-Time Passwords (TOTP), and strict fail-closed security policies.

---

## 1. Project Overview & Problem Statement
In shared laboratory environments (e.g., University Computer Labs), traditional password-based authentication is insufficient. Students frequently share credentials or walk away from unlocked workstations, leaving the terminal vulnerable to unauthorized access or malicious actions (Insider Threats / Session Hijacking by Proximity).

**The Solution:** This system replaces local, implicit trust with a strict, continuous, multi-factor pipeline. Users must authenticate with three independent factors to start a session. Once authenticated, a continuous background daemon ensures the original user remains physically present at the terminal. If the user steps away or an unrecognized face appears, the system immediately forces an OS-level lockdown and dispatches high-severity alerts.

---

## 2. Threat Model & Security Scoping

A rigorous security system must explicitly define its scope. 

### What This System Defends Against (In-Scope)
* **Credential Sharing / Impersonation:** Prevented by the biometric Face Recognition factor ("Something You Are").
* **Physical Session Hijacking:** Prevented by the Continuous Verification daemon. If a user walks away, the camera detects a missing face or a different face and locks the terminal within the defined grace period (Fail-Closed).
* **Basic Presentation Attacks (2D Spoofing):** Prevented by the Liveness Detection module, which requires a randomized blink challenge (calculating Eye Aspect Ratio) to defeat photographs or tablet screens.
* **Database Compromise (Data-at-Rest):** Prevented by symmetric AES (Fernet) End-to-End Encryption. Biometric encodings and TOTP secrets are encrypted before leaving the client and remain encrypted in the centralized SQLite database. 

### Documented Limitations (Out-of-Scope / Future Work)
* **Sophisticated 3D Mask Spoofing:** The current liveness check (EAR calculation) cannot reliably defeat high-fidelity 3D masks or advanced deepfake injections at the driver level. Hardware-level IR/Depth cameras (e.g., Windows Hello hardware) would be required.
* **Network-Level Eavesdropping (Data-in-Transit):** The current API operates over plain HTTP for local testing. A true production deployment **MUST** wrap the FastAPI server in a reverse proxy (like Nginx) terminating TLS/HTTPS. Without TLS, the cryptographic JWT tokens are vulnerable to Man-In-The-Middle (MITM) theft.
* **Physical Hardware Tampering:** If a malicious user unplugs the webcam, the system assumes a hardware failure. While the continuous verification daemon will log this and eventually lock the screen (fail-closed), physical tampering of the host OS kernel is out of scope.

---

## 3. Architecture & Authentication Flow

### The 3-Factor Authentication Pipeline
This system implements strict **Fail-Fast** ordering, evaluating the cheapest and least intrusive factors before capturing biometrics:
1. **Identity Claim:** User enters their Roll Number.
2. **Something You Have (TOTP):** User enters a 6-digit code from Google Authenticator. Verified against the central server.
3. **Something You Are (Biometrics):** Liveness challenge (blink) followed by a strict facial encoding match.

### Client-Server Trust Boundary
* **Central Server (FastAPI):** Acts as the Single Source of Truth. Manages the SQLite database and issues OAuth2 JSON Web Tokens (JWT). It *never* possesses the decryption keys for biometric data.
* **Lab PC Clients (`login.py`, `verify.py`):** Acts as the untrusted edge. Authenticates via Client ID/Secret to obtain a JWT. Performs face detection, encrypts/decrypts data locally in RAM, and enforces OS-level lockdowns.

### Architecture Flow
```text
[ Lab PC (Client) ]                                      [ Central API Server ]
        |                                                          |
        |--- 1. Authenticate (Client ID/Secret) ------------------>|
        |<-- 2. Issue short-lived JWT (OAuth2) --------------------|
        |                                                          |
        |--- 3. Fetch Encrypted Biometrics (Bearer JWT) ---------->|
        |<-- 4. Return Fernet-Encrypted Blob ----------------------|
        |                                                          |
  [Decrypt in RAM]                                                 |
  [Verify Face]                                                    |
  [Start Session]                                                  |
        |                                                          |
        |--- 5. Continuous Audit Logging (POST /log) ------------->|
```

---

## 4. Setup & Testing

### Prerequisites
* Python 3.11
* `pip install -r requirements.txt` (Includes `fastapi`, `uvicorn`, `dlib`, `face_recognition`, `opencv-python`, `PyJWT`, `cryptography`, `pyotp`)

### Running the System
1. **Start the Server:**
   ```bash
   python -m uvicorn server.main:app --host 0.0.0.1 --port 8000
   ```
2. **Register a User:**
   ```bash
   python register.py
   ```
   *(Scan the provided QR code with Google Authenticator).*
3. **Start a Session:**
   ```bash
   python login.py
   ```
   *(The continuous verification daemon will launch in the background).*
