# Cybersecurity Career Package & Interview Defense Manual
## Lab Face-Verified Access Lock System
**Project Portfolio, Resume Bullets, STAR Interview Stories & Technical Demonstration Drills**

---

## 1. Resume Bullets (Action + What + How + Measurable Result)

*Tailored for cybersecurity resumes (Software Security, AppSec, SOC/Detection, IAM). Every metric is verified from actual test runs.*

---

### Bullet 1: Continuous Authentication & Session Governance
- **Full Version:**  
  > *"Architected a Zero-Trust desktop session governance daemon in Python, polling biometric presence via OpenCV every 30 seconds and automatically engaging OS-level fail-closed workstation locking (`LockWorkStation`) within 60 seconds of student absence to eliminate unattended terminal hijacking."*
- **Short Version (1-Line):**  
  > *"Engineered a Python Zero-Trust desktop daemon evaluating facial presence every 30s with fail-closed auto-lock within 60s."*

---

### Bullet 2: Multi-Factor Authentication & Presentation Attack Detection
- **Full Version:**  
  > *"Engineered a 3-factor authentication pipeline enforcing Roll Number claim, physical RFC 6238 TOTP (Google Authenticator), and randomized 4.0-second interactive facial liveness detection (blink/turn/mouth) with real-time biometric identity verification to defeat photo and video replay attacks."*
- **Short Version (1-Line):**  
  > *"Architected a 3-factor authentication pipeline (Roll No + RFC 6238 TOTP + randomized 4.0s facial liveness) with identity cross-verification."*

---

### Bullet 3: Cryptographic Storage & Secrets Hygiene
- **Full Version:**  
  > *"Implemented defense-in-depth cryptography using Fernet AES-128-CBC + HMAC-SHA256 for biometric data at rest, isolated symmetric master keys in the host OS Keyring (Windows Credential Manager / Secret Service, mitigating CWE-798), and enforced TLS 1.2/1.3 with per-device OAuth2 JWT tokens."*
- **Short Version (1-Line):**  
  > *"Hardened biometric storage via Fernet AES-128 encryption with OS Keyring key isolation (CWE-798 mitigated) and TLS-secured per-device JWTs."*

---

### Bullet 4: Forensic Audit Ledger & Tamper-Evident Hashing
- **Full Version:**  
  > *"Constructed an append-only, tamper-evident audit ledger using SHA-256 cryptographic hash chaining anchored to a Genesis Hash ($H_0 = 0^{64}$); engineered a forensic verification CLI that mathematically detects single-bit SQL database tampering at the exact corrupted record."*
- **Short Version (1-Line):**  
  > *"Built an append-only audit ledger with SHA-256 hash chaining, enabling mathematical detection of single-bit database tampering."*

---

### Bullet 5: Automated Security Testing & Real-Time Alerting
- **Full Version:**  
  > *"Developed an automated integration test harness driving an in-memory FastAPI TestClient to validate 9 cross-layer defense vectors with 100% pass rate; integrated asynchronous Discord webhook alerts for immediate incident escalation upon high-severity violations."*
- **Short Version (1-Line):**  
  > *"Built an automated FastAPI security test harness covering 9 cross-layer defense vectors (100% pass rate) with asynchronous webhook alerting."*

---

## 2. GitHub README Header (Skimmable Recruiter Showcase)

*Copy-paste ready header block designed to land within 30 seconds of recruiter review.*

```markdown
# 🛡️ Lab Face-Verified Access Lock System

> **A high-assurance, continuous Zero-Trust authentication and session governance framework engineered to eliminate proxy logins, session abandonment, and terminal hijacking in institutional computer laboratories.**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.11-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Security](https://img.shields.io/badge/Security-Zero%20Trust%20%7C%20Fail--Closed-success)](#threat-model)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

### 🎥 60-Second System Demo
```
+-----------------------------------------------------------------------------------------+
|                               [DEMO SCREENCAST PLACEHOLDER]                             |
|  1. Student Enrolls (Webcam Capture + TOTP QR)    ==> Encrypted vector stored in DB    |
|  2. 3-Factor Login (Roll No -> Face Match -> TOTP -> Randomized Liveness Challenge)     |
|  3. Desktop Unlocks & Continuous Daemon Engages   ==> 30s background heartbeats         |
|  4. Student Steps Away (Absence Timeout)          ==> Fail-Closed Workstation Lock      |
|  5. Rogue SQL Injection Simulated                 ==> SHA-256 Hash Chain Catches Tamper |
+-----------------------------------------------------------------------------------------+
```

### ⚡ Key Capabilities by Security Domain
* **Zero-Trust Session Governance:** Background daemon evaluates presence every 30s; locks OS within 60s of absence.
* **Multi-Factor Inherence & Possession:** Sequential pipeline enforcing Roll No + RFC 6238 TOTP + 128-d Facial Landmarks.
* **Presentation Attack Detection (PAD):** Randomized 4.0s challenge-response (Blink/Turn/Mouth) with mover identity check.
* **Authenticated Cryptography at Rest:** Fernet AES-128-CBC + HMAC-SHA256; master keys isolated in OS Keyring (CWE-798 mitigated).
* **Network & Gateway Security:** TLS 1.2/1.3 encrypted transport with short-lived per-device OAuth2 JWT tokens.
* **Tamper-Evident Forensic Ledger:** Forward-linked SHA-256 cryptographic hash chain anchored to Genesis Block ($H_0 = 0^{64}$).
* **Privacy & DPDP Act 2023 Compliance:** Zero raw image persistence on disk; biometric vectors deallocated from RAM post-inference.

### 🛡️ Threat Model: What It Defends Against vs. Explicit Limitations
| Defended In-Scope Threats | Explicit Documented Limitations (Out-of-Scope) |
| :--- | :--- |
| ✅ **Credential Sharing & Proxy Attendance** | ⚠️ **3D Silicone Masks:** 2D RGB webcams lack active infrared structured light; enterprise anti-mask defense requires hardware IR depth sensors. |
| ✅ **Unattended Workstation Hijacking (60s Lock)** | ⚠️ **Physical Root Host Compromise:** An attacker with local administrator root privileges can perform memory dumps on running processes. |
| ✅ **2D Photo & Video Replay Presentation Attacks** | ⚠️ **Local Full-Chain Recomputation:** A compromised root admin could recompute SQLite hashes; enterprise deployments require external RFC 3161 ledger anchoring. |
| ✅ **Shoulder Surfing (`len(faces) > 1` Lock)** | ⚠️ **Extreme Darkness (< 50 Lux):** Severe low-light conditions degrade facial landmark detection, requiring ambient room illumination. |
| ✅ **Offline Database Theft & SQL Tampering** | |
```

---

## 3. LinkedIn Post Draft (Authentic, Narrative-Driven)

```text
In college computer labs, physical access control is fundamentally broken.

Students routinely share passwords to fake attendance, or leave terminals logged in when stepping out for lunch—leaving grade portals, exam software, and private files wide open to anyone nearby. Traditional systems authenticate you once at the door and remain completely blind afterward.

For my final year cybersecurity project at TKIET Warananagar, I built the Lab Face-Verified Access Lock System: a zero-trust session governance architecture designed for standard lab PCs.

Here is how it works:
1. 3-Factor Login: Roll Number + Google Authenticator TOTP + Facial Landmark Match with a randomized 4-second liveness challenge (and we verify the person moving is actually the enrolled student).
2. Continuous Verification: A lightweight background daemon checks presence every 30 seconds. If you step away, the screen auto-locks within 60 seconds. If someone else sits down, it locks instantly.
3. Cryptographic Non-Repudiation: Zero raw photos are saved to disk. 128-d vectors are Fernet-encrypted with keys stored in the OS Keyring enclave, and every log is chained using SHA-256 so database tampering is mathematically detectable.

The biggest lesson I learned?
Security isn't just about stopping bad guys at login—it's about managing state after access is granted, designing systems that fail closed when components crash, and being honest about where software-level defense ends and hardware sensors begin.

Check out the full open-source repo, architecture diagrams, and threat model here: [GitHub Repository Link]

#Cybersecurity #ZeroTrust #AppSec #InformationSecurity #Python #Biometrics #Cryptography #BTech
```

---

## 4. STAR Interview Stories (60–90 Seconds Spoken)

*Memorize these three conversational stories. They highlight architectural maturity, debugging ability, and intellectual honesty.*

---

### Story 1: Architectural Trade-Off — "Fail-Closed Security vs. System Availability"
- **Situation:**  
  *"When designing our continuous verification loop for shared university labs, we faced a major architectural dilemma: what should happen when a lab workstation experiences a transient network dropout or the central authentication server restarts?"*
- **Task:**  
  *"I had to choose between prioritizing availability—allowing the student to keep working with cached credentials—or prioritizing security by locking the desktop immediately upon network loss."*
- **Action:**  
  *"From a security engineering standpoint, failing open is fatal: an attacker who knows network failure keeps machines open could simply unplug the Ethernet cable or spoof a DHCP failure to permanently bypass continuous verification. Therefore, I enforced a strict **Fail-Closed policy**. However, to avoid penalizing students during brief network blips, I introduced a two-stage temporal buffer: cycle 1 increments a missed-check warning counter, giving the network 30 seconds to recover. If cycle 2 also fails, the system immediately invokes the operating system's `LockWorkStation` API and logs a network severance event."*
- **Result:**  
  *"This cut the unattended vulnerability window down from the 15-minute screensaver baseline to just 60 seconds, while preventing denial-of-service disruptions from momentary network jitter. It demonstrated how to balance real-world operational friction against zero-trust guarantees."*

---

### Story 2: Security Bug / Vulnerability Sweep — "Fixing the Liveness Identity Gap"
- **Situation:**  
  *"During our security testing sweep, I conducted an adversarial review of our authentication pipeline: Roll Number -> Face Match -> TOTP -> Randomized Liveness Challenge."*
- **Task:**  
  *"I was specifically probing for presentation attack bypasses in `liveness_check.py`."*
- **Action:**  
  *"I realized we had a critical logic vulnerability: our liveness detector verified facial *motion*—using 68 dlib landmarks to measure Eye Aspect Ratio and yaw rotation—but it did not verify *whose face* was executing that motion. An attacker could hold up a printed photo of the legitimate student to clear the static face match, and then put their own live face in front of the lens to perform the demanded blink or head turn.  
  To close this gap, I refactored `liveness_check.py` to accept the enrolled student's reference embedding. The exact video frame that satisfies the physical motion threshold is now passed to `face_recognition.face_encodings()`, computing Euclidean distance against the enrolled template. If the person blinking isn't the enrolled student, access is instantly denied and a HIGH-severity incident is logged."*
- **Result:**  
  *"I wrote an automated mock test suite (`test_liveness_identity.py`) simulating enrolled faces, different faces, and mid-challenge swaps. All three test cases pass deterministically, closing the presentation attack loop without requiring live human intervention."*

---

### Story 3: Documented Limitations Chosen NOT to Solve — "2D Webcams vs. 3D Silicone Masks"
- **Situation:**  
  *"When finalizing the system's threat model, our team evaluated whether we could claim defense against hyper-realistic 3D silicone masks and deepfake video injection drivers."*
- **Task:**  
  *"I needed to define where our software security perimeter ended and where hardware physical constraints took over."*
- **Action:**  
  *"Rather than pretending our computer vision heuristics could reliably detect depth on a 2D RGB webcam, I made the deliberate decision to document 3D silicone masks and virtual camera drivers as **Explicit Out-of-Scope Limitations**. On standard consumer webcams, software algorithms cannot measure photon time-of-flight or structural infrared depth. Claiming anti-mask protection without hardware sensors would have been dishonest and dangerous. Instead, I focused our defenses on 2D print and replay attacks, and formally documented that enterprise-grade anti-mask protection requires active infrared structured light cameras, such as an Intel RealSense or Apple TrueDepth sensor."*
- **Result:**  
  *"During our project defense and architectural audits, examiners praised this intellectual honesty. Stating clear, defensible boundaries showed that I understood physical sensor axioms rather than overclaiming what Python and OpenCV can achieve."*

---

## 5. Role Mapping: Tailoring the Project for Job Applications

*Use these talking points to position the project depending on the specific job description you apply for.*

---

### Role A: Application Security (AppSec) / Product Security Engineer
- **Resume Headline:** *"AppSec & Software Security Specialist | Zero-Trust System Architecture"*
- **What to Lead With:**
  - **CWE-798 Mitigation:** Eliminating hardcoded keys by integrating the host OS Keyring enclave (`keyring` library / Windows Credential Manager).
  - **Cryptographic Implementation:** Fernet AES-128-CBC + HMAC-SHA256 authenticated encryption for biometric data at rest.
  - **Input Validation & Gateways:** FastAPI REST endpoints, Pydantic schema validation, and per-device OAuth2 JWT token validation.
  - **Automated Security Testing:** In-memory integration testing via `TestClient` covering expired JWT rejection, ciphertext bit-flipping, and SQL injection resistance.
- **Key Buzzwords:** *Threat Modeling, CWE-798, AES-128, HMAC-SHA256, OAuth2 JWT, Secrets Hygiene, Automated Regression Testing.*

---

### Role B: SOC Analyst / Detection & Incident Response (DFIR)
- **Resume Headline:** *"SOC Analyst / Incident Response | Detection Engineering & Audit Forensics"*
- **What to Lead With:**
  - **Cryptographic Hash Chaining:** Linear SHA-256 ledger providing mathematical non-repudiation (RFC 6962) and detecting single-bit database tampering.
  - **Incident Alerting Pipeline:** Real-time asynchronous Discord/Slack webhook dispatch on high-severity security events (`LOCK_FACE_MISMATCH`, `INVALID_TOTP`, `TAMPER_DETECTED`).
  - **Risk-Scored Categorization:** Mapping biometric Euclidean distances into High, Medium, and Reject risk bands.
  - **Forensic CLI Tooling:** Engineering `log_viewer.py --verify-integrity` to traverse historical records and pinpoint tampered rows.
- **Key Buzzwords:** *SIEM, Audit Ledgers, SHA-256 Non-Repudiation, Incident Response, Webhook Alerting, Forensic Attribution, Event Severity.*

---

### Role C: Identity & Access Management (IAM) / Cloud Security
- **Resume Headline:** *"Identity & Access Management (IAM) Engineer | Zero-Trust Multi-Factor Architecture"*
- **What to Lead With:**
  - **Three-Factor Pipeline:** Sequential binding of Identity Claim (Roll Number), Inherence (Facial Biometrics), and Possession (RFC 6238 TOTP).
  - **Continuous Session Verification:** Eliminating the vulnerability window of static point-in-time logins by re-evaluating identity every 30 seconds.
  - **Privacy & DPDP Act 2023:** Zero raw image persistence on disk; mathematical 128-d vectors deallocated from RAM post-inference.
  - **Per-Device Commissioning:** Machine enrollment issuing unique client UUIDs and short-lived 24-hour bearer tokens.
- **Key Buzzwords:** *Zero-Trust Architecture (NIST SP 800-207), MFA, RFC 6238 TOTP, Biometric Governance, DPDP Act 2023, Least Privilege.*

---

### Role D: Security Software Engineer / Systems Security
- **Resume Headline:** *"Systems Security Software Engineer | Python, C++ & OS-Level Enforcement"*
- **What to Lead With:**
  - **OS-Level Session Interception:** Calling Win32 `LockWorkStation` API via `ctypes` to immediately sever desktop input focus on security violations.
  - **Multithreading & Concurrency:** Synchronizing background verification worker threads using `threading.Event()` without blocking foreground UI applications.
  - **Computer Vision Pipeline:** dlib 68-point facial landmark regression tree and ResNet deep convolutional metric embeddings.
  - **Fail-Closed State Machines:** Deterministic state transitions handling sensor disconnects, server process drops, and grace period timeouts.
- **Key Buzzwords:** *Win32 API, Concurrency / Thread Synchronization, Fail-Closed States, Computer Vision, dlib, Low-Latency Daemon.*

---

## 6. "Show Me" Live Demonstration Drill (60 Seconds Each)

*When an interviewer or examiner says: "Prove it—show me that working right now", use these exact 60-second commands.*

---

### Drill 1: Prove Continuous Monitoring & Fail-Closed Auto-Lock
- **The Challenge:** *"Show me how the system detects absence and locks the screen."*
- **Action (60s):**
  1. Open terminal: `python verify.py` (or trigger continuous verification).
  2. Point camera at your face: terminal outputs `[VERIFY] Match: Confidence 0.88`.
  3. Cover camera lens or step out of frame.
  4. Point out terminal output: `[WARNING] Missed check 1/2. Grace period active.`
  5. Wait 30s for check 2: terminal displays `[ALERT] Absence timeout! Locking workstation.` and Windows immediately locks to the logon screen.
- **What to Say:** *"Notice that within 60 seconds of departure, the background daemon invoked the Win32 `LockWorkStation` API, eliminating the 15-minute unattended terminal hijacking window."*

---

### Drill 2: Prove Presentation Attack Defense (Liveness + Identity)
- **The Challenge:** *"Prove that your liveness check stops an attacker using a photo or video swap."*
- **Action (60s):**
  1. Run automated unit test: `python test_liveness_identity.py`.
  2. Terminal displays:
     - `CASE A: Enrolled face completes challenge -> PASS`
     - `CASE B: Different face performs challenge -> [SECURITY ALERT] Liveness identity mismatch! -> FAIL`
     - `CASE C: Face switches partway through -> [SECURITY ALERT] Liveness identity mismatch! -> FAIL`
  3. All tests pass with `OK`.
- **What to Say:** *"Here is automated proof without requiring live camera tricks: our liveness algorithm extracts facial coordinates on the exact frame the motion completes, asserting Euclidean distance against the enrolled student to defeat face-swapping attacks."*

---

### Drill 3: Prove Biometric Data Encryption & Key Isolation
- **The Challenge:** *"Show me where biometrics are stored and prove they are encrypted."*
- **Action (60s):**
  1. Run: `python log_viewer.py` (or inspect `server/central_access_control.db` in SQLite).
  2. Show the `face_encoding` column: it displays raw ciphertext bytes (`gAAAAABn...`).
  3. Open Python interactive console:
     ```python
     import keyring
     key = keyring.get_password("LabAccessControlSystem", "fernet_key")
     print(f"Key loaded from OS Keyring: {key[:10]}...")
     ```
- **What to Say:** *"The database holds zero plaintext vectors or images. Biometrics are Fernet-encrypted ciphertext, and the master key is stored in the host Operating System Keyring enclave, mitigating CWE-798."*

---

### Drill 4: Prove Tamper-Evident Hash Chain Detection
- **The Challenge:** *"Prove that you can detect a database administrator modifying logs."*
- **Action (60s):**
  1. Run clean verification: `python log_viewer.py --verify-integrity`.
     - Output: `[+] SUCCESS: Cryptographic Chain Verified! No tampering detected.`
  2. Run the tamper-test simulation in `test_integration.py` (Test 9):
     - Deliberately modifies Log ID confidence score from `0.88` to `0.98` via SQL `UPDATE`.
     - Output: `[TAMPER DETECTED] Hash mismatch at Log ID 63! Expected 676dc6c..., found 93e484d... Execution halted.`
- **What to Say:** *"Because each record hashes its contents with the previous hash, changing a single decimal in SQLite mathematically breaks the SHA-256 chain, proving non-repudiation."*

---

### Drill 5: Prove End-to-End Cross-Layer Testing
- **The Challenge:** *"Show me your test coverage across the multi-factor architecture."*
- **Action (60s):**
  1. Run: `python test_integration.py`.
  2. Watch the 9 automated vectors execute against the in-memory FastAPI `TestClient`:
     - Device Registration, E2EE Student Enrollment, Decryption Parity, RFC 6238 TOTP, Expired JWT Rejection, Liveness Failure Logging, Risk-Band Logging, Hash Chain Integrity, Tamper Detection.
  3. Output: `>>> ALL DEFENSE-IN-DEPTH INTEGRATION TESTS PASSED (9/9) <<<`.
- **What to Say:** *"Our test suite verifies cross-layer interactions—asserting that state transitions across network, cryptographic, and biometric boundaries preserve security invariants."*

---
*End of Career Package & Interview Defense Manual*
