# Project Brain: Face-Verified Access Lock System

This document serves as the central knowledge base, architectural overview, and roadmap for the project.

## Current Architecture & Modules

### 1. Core Data & Security Configuration
- `config.json`: Externalized security policies (verification interval, grace period, biometric tolerance, max pause duration). Allows tuning without touching code.
- `database.py`: Handles SQLite DB initialization, schema migrations (e.g., adding `severity` tags), storage of biometric encodings, and robust event logging for the audit trail.

### 2. User Interfaces & Onboarding
- `register.py`: GUI (OpenCV) for capturing and registering new student faces. Ensures single-face validation before computing encodings.
- `login.py`: Initiates the user session. Validates roll numbers against the DB, loads biometrics, starts the continuous verification thread, and launches the system tray application.
- `tray_app.py`: Uses `pystray` to hide the application in the background (System Tray) after login, providing context menu options for Pause, Resume, and Logout.

### 3. Enforcement & Verification (Continuous Authentication)
- `verify.py`: The background engine. Periodically captures webcam frames to verify identity. 
  - **Threat A (No Face):** Logs a missed check. If grace period expires, triggers an auto-lock (`LOCK_NO_FACE_TIMEOUT`).
  - **Threat B (Wrong Face):** Instantly triggers an auto-lock (`LOCK_FACE_MISMATCH`).
  - **Anti-Tamper:** Monitors the "Pause" state. If paused beyond the max duration, it auto-resumes monitoring.
  - **Enforcement:** Uses OS-level commands (e.g., `ctypes.windll.user32.LockWorkStation()` on Windows) to physically secure the workstation.

### 4. Auditing & Forensics
- `log_viewer.py`: The Security Monitoring Dashboard. Parses raw SQLite logs into a readable ASCII table with plain-English descriptions and filters by Threat Severity (LOW/HIGH).
- `view_db.py`: CLI tool for inspecting registered users and raw data.
- `webcam_test.py`: Hardware diagnostic script to test Haar Cascades and camera feeds.

---

## Roadmap / Next Tasks

- [x] **Task 1: Liveness Detection (Anti-Spoofing)** - Implemented blink detection via Eye Aspect Ratio (EAR) using dlib's 68-point facial landmark predictor to prevent attackers from bypassing the system using photographs or videos.
- [x] **Task 2: Data-at-Rest Encryption** - Used `cryptography.fernet` to encrypt the 128-d face encodings in the SQLite database, protecting sensitive biometric PII in case the `.db` file is stolen.
- [x] **Task 3: Multi-Factor Authentication (MFA)** - Integrated `pyotp` and Google Authenticator TOTP as a fail-fast secondary layer ("Something You Have") before biometric challenge.
- [x] **Task 4: Real-Time Incident Alerting** - Added webhook integration (Discord) to send a push notification when a `HIGH` severity impersonation attempt occurs, completely decoupling the alerting from the core fail-safe lock.
