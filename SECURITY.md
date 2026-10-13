# Security Policy & Responsible Disclosure

## 🛡️ Project Security Overview
The **Lab Face-Verified Access Lock System** is an academic cybersecurity research project developed for institutional computer laboratory security. We treat security integrity and secrets hygiene as core design requirements.

---

## 1. Supported Versions
Only the latest release / `main` branch is actively supported and tested for security patches:

| Version / Branch | Supported          |
| ---------------- | ------------------ |
| `main`           | :white_check_mark: |
| Legacy releases  | :x:                |

---

## 2. Reporting a Vulnerability
If you discover a security vulnerability, flaw, or credential exposure in this repository:
1. **Do NOT open a public GitHub Issue.**
2. Send an email to the project maintainer (`shindedipak@tkiet.ac.in` or via private GitHub Security Advisory).
3. Include:
   - A description of the vulnerability and attack scenario.
   - Proof-of-concept steps or code to reproduce.
   - Potential impact on access control, cryptographic integrity, or student privacy.
4. We aim to acknowledge receipt within 48 hours and provide an assessment or fix within 7 business days.

---

## 3. Vulnerability Scoping

### In-Scope Vulnerabilities
- Authentication bypasses in the 3-factor login flow (`login.py`).
- Flaws in the continuous verification daemon allowing session hijacking without lockout (`verify.py`).
- Mathematical breakages in the SHA-256 hash-chained audit ledger (`server/database.py`).
- Flaws in Fernet ciphertext decryption or OS Keyring integration (`src/crypto_utils.py`).
- Insecure direct object references (IDOR) or injection in FastAPI endpoints (`server/main.py`).

### Out-of-Scope (Documented Physical & Environmental Limitations)
- Presentation attacks using high-end physical 3D silicone masks or active infrared spoofing against standard RGB webcams (requires hardware-level IR depth sensors).
- Physical compromise of an unlocked workstation running with local administrator/root privileges.
- Re-computing the entire local SQLite hash chain from scratch on a fully compromised root machine (mitigated in production via remote append-only ledger anchoring).
- Network Denial-of-Service (DoS) attacks caused by deliberate physical network cable disconnection (by design, the system **fails closed** to preserve security).

---

## 4. Privacy Note & Data Protection (DPDP Act 2023 Alignment)

This project handles student biometric data with strict privacy safeguards adhering to the principles of the **Digital Personal Data Protection (DPDP) Act 2023**:

1. **Zero Raw Image Storage (Data Minimization):**
   - The system **never saves raw photographs, video streams, or camera frames to disk**.
   - Webcam frames are processed strictly in volatile memory (RAM) as NumPy arrays.
   - Immediately after dlib extracts the 128-dimensional mathematical landmark embedding, raw image buffers are discarded and overwritten in RAM.

2. **Encryption at Rest:**
   - 128-dimensional biometric floating vectors and TOTP secrets are encrypted using authenticated **Fernet AES-128-CBC + HMAC-SHA256** before being written to SQLite.
   - Stolen database files cannot be decrypted without the master Fernet key.

3. **Cryptographic Key Isolation:**
   - Encryption master keys are isolated in the host Operating System Credential Enclave (Windows Credential Manager / macOS Keychain / Linux Secret Service) via the Python `keyring` library—never hardcoded in source code or database tables (CWE-798 mitigated).

4. **Explicit Consent & Purpose Limitation:**
   - Enrollment requires voluntary participation: students actively enter their roll number, review a privacy notice, scan their TOTP QR code, and look into the camera.
   - Biometric embeddings are strictly utilized for laboratory workstation session authorization and are never shared with third-party services.
