# Security Validation & Test Checklist

This checklist contains edge-case testing scenarios to validate the reliability and security of the Face-Verified Access Lock System. Use this before any major deployment or presentation (like a viva) to catch regressions.

## 1. Registration (`register.py`)
- [ ] **Valid Registration:** Complete registration with a new roll number. Ensure the TOTP QR code is scannable and the data writes to the central API.
- [ ] **Duplicate Registration:** Attempt to register an existing roll number. *Expected:* The central API safely overwrites the old entry (or handles the conflict without crashing).
- [ ] **No Face Detected:** Step out of the frame while registering. *Expected:* Handled safely; prompts the user to adjust lighting/position.
- [ ] **Multiple Faces Detected:** Have two people in the frame. *Expected:* Handled safely; rejects the capture to prevent corrupted biometric state.
- [ ] **Server Unreachable:** Stop the central FastAPI server and try to register. *Expected:* The client fails gracefully with a "[SECURITY] API Server is Unreachable" message rather than crashing with a stack trace.

## 2. Authentication (`login.py`)
- [ ] **Valid Login (All 3 Factors):** Enter correct roll number, valid TOTP from phone, and pass liveness check. *Expected:* Success, continuous verification starts.
- [ ] **Wrong TOTP:** Enter an invalid or expired TOTP code. *Expected:* Fails fast, logs `LOGIN_DENIED_INVALID_TOTP` to central server, triggers webhook alert.
- [ ] **Liveness Spoof (No Blink):** Hold a static photo up to the camera during login. *Expected:* The blink challenge expires, login denied, logs `LOGIN_DENIED_LIVENESS_FAIL`, triggers webhook alert.
- [ ] **Wrong Face (Impersonation):** Have a different person sit in front of the camera *after* entering a valid TOTP code. *Expected:* Liveness passes, but face match fails. Immediate lockdown triggered.
- [ ] **Server Unreachable:** Stop the server during login. *Expected:* System immediately enforces a Fail-Closed policy, denying all logins until connection is restored.

## 3. Continuous Verification (`verify.py`)
- [ ] **Authorized Face Present:** Sit normally. *Expected:* Logs `PERIODIC_CHECK_SUCCESS` silently to the server.
- [ ] **Face Absent (Walk Away):** Step out of the frame. *Expected:* Missed checks increment. Once the grace period expires, logs `LOCK_NO_FACE_TIMEOUT` and locks the OS workstation.
- [ ] **Impersonation (Face Swap):** While logged in, have an unregistered person sit down. *Expected:* Immediate detection. Logs `LOCK_FACE_MISMATCH`, triggers HIGH severity webhook alert, and locks the OS workstation instantly.
- [ ] **Network Outage (Fail-Closed):** While logged in, stop the central server. *Expected:* The next heartbeat check fails to write to the API, immediately triggering `[SECURITY] Central API Unreachable! Triggering Fail-Closed lockdown.`

## 4. System Controls (`tray_app.py` & Concurrency)
- [ ] **Pause Monitoring:** Right-click the system tray icon and pause monitoring. *Expected:* Check loop suspends, logs `POLICY_OVERRIDE`.
- [ ] **Auto-Resume (Anti-Tamper):** Leave it paused until the `max_pause_duration_seconds` expires. *Expected:* System automatically resumes checking and logs `AUTO_RESUME_FAILSAFE` to prevent indefinite bypassing.
- [ ] **Resume Monitoring:** Manually resume. *Expected:* Monitoring continues and grace period is reset.

## 5. Centralized Server & Alerts
- [ ] **Multi-Client Isolation:** Run `login.py` simultaneously from two different terminals with two different roll numbers. *Expected:* Both sessions maintain their own local state and do not interfere with each other. Both successfully log heartbeats to the central API.
- [ ] **Webhook Filtering:** Ensure Discord alerts only trigger on HIGH severity events (like MFA failures or face mismatches), not on INFO events.
