# Mock Viva Examination Preparation Pack
## Lab Face-Verified Access Lock System
**Department of Computer Science & Engineering / Cybersecurity**  
**Project Defense Reference Guide**

---

## Part 1: Core Viva Questions & Model Spoken Answers (30 Questions)

*Note: Answers are written in natural spoken language—the exact phrasing you can use when talking to external examiners.*

---

### Category A: Basics & Motivation

#### Q1. What problem does this project solve, and why is it needed in an institutional computer lab?
- **Spoken Answer:** "In colleges, computer labs face a major insider-threat problem: session abandonment and proxy logins. Students routinely share passwords to fake attendance or submit assignments for peers, and when a student walks away from a logged-in PC, any unauthorized person can step in and access sensitive files or exam portals. Traditional systems only check identity once at login. Our project solves this by enforcing three-factor login and then maintaining **continuous biometric verification** in the background, automatically locking the PC the moment the authorized student leaves or someone else sits down."
- **Reference:** Chapter 1 (Section 1.1–1.2) | Slide 2

#### Q2. Why aren't traditional passwords or RFID student identity cards sufficient?
- **Spoken Answer:** "Passwords and RFID cards only verify *what you know* or *what you possess*, not *who you actually are*. Both can easily be shared, stolen, or passed around the lab without the system ever knowing. More importantly, neither solves the post-login vulnerability window—once a student swipes an RFID card or types a password, the session remains open even after they walk away. Biometric inherence paired with continuous checks is the only mechanism that ties the active session directly to physical presence."
- **Reference:** Chapter 1 (Section 1.2), Chapter 2 | Slide 2, Slide 4

#### Q3. What is the single core differentiator of your project compared to standard commercial biometric attendance systems?
- **Spoken Answer:** "Standard commercial systems are point-in-time—they verify the face once, unlock the door or mark attendance, and terminate. Our key differentiator is **continuous, zero-trust session governance**. Our system treats every 30 seconds as a new authentication event. Even after granting access, a background daemon continuously verifies that the exact same authorized face is sitting in front of the screen, failing closed the moment that condition changes."
- **Reference:** Chapter 1 (Section 1.3), Chapter 3 | Slide 5

#### Q4. What were the specific objectives you established for this project?
- **Spoken Answer:** "We set five concrete objectives: first, eliminate proxy logins using three-factor authentication; second, eliminate unattended terminal hijacking via periodic background verification; third, secure all biometric data at rest using authenticated symmetric encryption; fourth, protect multi-PC network traffic using TLS and per-device JWTs; and fifth, maintain mathematical audit accountability using a tamper-evident SHA-256 hash chain."
- **Reference:** Chapter 1 (Section 1.4) | Slide 3

---

### Category B: Authentication & Biometrics

#### Q5. Can you walk us through the 3 factors in your authentication pipeline?
- **Spoken Answer:** "Yes, sir. Factor 1 is identity claim and knowledge: the student provides their institutional roll number. Factor 2 is biometric inherence: the camera captures their face, verifies liveness to prevent photo spoofing, and checks mathematical facial similarity. Factor 3 is physical possession: the student submits a 6-digit Time-based One-Time Password generated on their smartphone via Google Authenticator using the RFC 6238 standard. All three must pass before the desktop unlocks."
- **Reference:** Chapter 4 (Section 4.3), Chapter 5 (Section 5.3) | Slide 7, Slide 8

#### Q6. What is continuous authentication, and how does your background verification cycle work?
- **Spoken Answer:** "Continuous authentication means session trust is ephemeral rather than permanent. Every 30 seconds, a lightweight background worker thread wakes up, captures a single video frame, computes the facial embedding, and compares it to the enrolled student's template. If the face matches with high confidence, the cycle sleeps for another 30 seconds. If no face is detected, it grants a single 30-second grace period. If two consecutive checks fail, or if an unrecognized face is detected, it immediately invokes the operating system lock workstation API."
- **Reference:** Chapter 3 (Section 3.2), Chapter 5 (Section 5.4) | Slide 9

#### Q7. What exactly is a 'face encoding' or 'embedding', and how is it generated?
- **Spoken Answer:** "A face encoding is not a photo or an image. It is a 128-dimensional floating-point vector that quantifies distinctive facial geometry—such as the ratio between the eyes, nose bridge curvature, and jawline contour. We generate it using dlib's ResNet-based deep convolutional neural network, which extracts these 128 numerical landmarks from 68 localized points on the face. Raw camera frames are converted into this array in RAM and immediately discarded."
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.2) | Slide 8, Slide 11

#### Q8. How does face matching work mathematically in your system?
- **Spoken Answer:** "We compute the Euclidean distance between the 128-dimensional vector of the live face and the decrypted enrolled vector stored in the database. In 128-dimensional space, identical faces yield a distance close to 0.0, while different individuals yield distances above 0.60. We convert this into a confidence score as $1.0 - \text{distance}$. If the distance is under 0.60, it's a match; if it's over 0.60, it's classified as an impersonation mismatch."
- **Reference:** Chapter 4 (Section 4.3), Chapter 5 (Section 5.3) | Slide 8, Slide 9

#### Q9. What are False Acceptance Rate (FAR) and False Rejection Rate (FRR), and how did you balance them?
- **Spoken Answer:** "FAR is the probability that an unauthorized impostor is incorrectly accepted as legitimate. FRR is the probability that a genuine student is incorrectly rejected. They represent an inherent security trade-off. We configured our distance threshold at $0.60$. Lowering it to $0.45$ would minimize FAR but dramatically increase FRR under uneven lab lighting. Raising it above $0.65$ would allow lookalikes to pass. The $0.60$ threshold, combined with our TOTP factor and liveness challenge, provides defense-in-depth so biometric accuracy doesn't carry the entire security burden alone."
- **Reference:** Chapter 2 (Section 2.4), Chapter 7 (Section 7.3) | Slide 8, Slide 14

---

### Category C: Anti-Spoofing & Liveness Detection

#### Q10. What is a presentation attack, and what specific attack vectors did you defend against?
- **Spoken Answer:** "A presentation attack, or biometric spoofing, occurs when an attacker presents a synthetic or stolen artifact to the sensor instead of a live human face. We defended against 2D print attacks—where an attacker holds a printed photograph of the student—and digital replay attacks, where someone replays a pre-recorded smartphone video of the student in front of the lens. We mitigate these using an active, randomized challenge-response protocol."
- **Reference:** Chapter 3 (Section 3.3), Chapter 7 (Section 7.2) | Slide 8, Slide 14

#### Q11. How does your randomized challenge-response liveness detection work?
- **Spoken Answer:** "Instead of passive blink detection which can be fooled by looping video clips, our system issues a randomized interactive prompt chosen at runtime from four possibilities: Blink, Open Mouth, Turn Left, or Turn Right. Using dlib's 68 facial landmarks, we calculate the Eye Aspect Ratio for blinks, Mouth Aspect Ratio for mouth opening, and nose-to-jaw horizontal symmetry for head turns. Furthermore, on the exact frame the challenge is completed, the system cross-verifies that the face performing the motion actually matches the enrolled student's face vector."
- **Reference:** Chapter 4 (Section 4.3), Chapter 5 (Section 5.3) | Slide 8

#### Q12. Why did you choose a 4.0-second window for the liveness challenge?
- **Spoken Answer:** "4.0 seconds is a deliberate engineering trade-off based on human motor response time versus attacker staging latency. Human reaction time—reading the prompt, processing the required direction, and initiating head movement—takes between 1.5 and 2.5 seconds. If we gave 10 seconds, an attacker with a gallery of recorded clips would have enough time to find and play the demanded motion. A 4.0-second limit gives legitimate students enough time to react while denying an attacker the window needed to stage a matching replay."
- **Reference:** Chapter 5 (Section 5.3), Chapter 7 (Section 7.3) | Slide 8

#### Q13. Can a real-time deepfake or an advanced video replay beat your liveness check?
- **Spoken Answer:** "A simple pre-recorded replay cannot beat it because the challenge is chosen at random after login begins, giving the attacker no prior knowledge of whether to blink, open their mouth, or turn. However, we acknowledge that an advanced real-time generative deepfake injected via a virtual webcam software driver could theoretically mimic the prompts. In our threat model, we mitigate virtual drivers by relying on OS hardware camera feeds, but true mitigation against physical 3D silicone masks and high-end deepfakes requires hardware infrared depth sensors, which we have highlighted as future work."
- **Reference:** Chapter 3 (Section 3.3), Chapter 7 (Section 7.4), Chapter 8 | Slide 8, Slide 14

---

### Category D: Cryptography & Data Protection

#### Q14. Why did you use Fernet symmetric encryption instead of just hashing the face encodings or storing raw numbers?
- **Spoken Answer:** "Biometric data cannot simply be hashed like passwords using bcrypt or SHA-256. Facial landmark coordinates fluctuate slightly on every capture due to lighting and angle, so two captures of the same face never produce bitwise-identical numbers. Therefore, the system needs the actual 128-dimensional floating vector to compute Euclidean distance. Because the vector must be recovered, we use symmetric encryption. We chose Fernet because it is an authenticated cryptography standard combining AES-128 in CBC mode with HMAC-SHA256 for message integrity, preventing ciphertext tampering."
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.2) | Slide 7, Slide 11

#### Q15. Where is the encryption master key stored, and why did you use the host OS Keyring?
- **Spoken Answer:** "Storing encryption keys in source code, configuration files, or the same database creates a major CWE-798 vulnerability—if the repository or database is leaked, all data is compromised. To avoid this, we isolate the 256-bit Fernet key in the host Operating System's secure credential enclave—Windows Credential Manager via the Python `keyring` library. This enforces separation of duties: an attacker who steals the SQLite database file cannot decrypt biometric vectors without administrative compromise of the underlying OS user session."
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.1) | Slide 7

#### Q16. What is the role of TLS/HTTPS in your multi-PC architecture?
- **Spoken Answer:** "The system uses a client-server model where lab workstations communicate with a central FastAPI server over the local LAN. Without TLS, all REST traffic—including biometric vectors, TOTP secrets, and JWT bearer tokens—would travel in plaintext, making it vulnerable to local ARP spoofing, packet sniffing, or session hijacking via tools like Wireshark. TLS 1.2/1.3 encrypts the transport channel end-to-end and provides server authentication."
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.1) | Slide 6, Slide 7

#### Q17. What is a cryptographic hash chain and why did you use it for audit logging?
- **Spoken Answer:** "In a standard SQL database, any privileged insider or attacker with SQL access can update or delete log rows to erase traces of an attack. A hash chain prevents this by linking each log entry mathematically to the previous one. Every new entry's SHA-256 hash is calculated over its own fields plus the hash of the preceding record ($H_i = \text{SHA256}(\text{data}_i \parallel H_{i-1})$), anchored to a fixed Genesis Hash. If anyone modifies even a single character or timestamp in a historical record, every subsequent hash in the chain breaks, immediately exposing the exact row where tampering occurred."
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.4) | Slide 7, Slide 10

#### Q18. Why use SHA-256 for the audit chain rather than MD5 or SHA-1?
- **Spoken Answer:** "Both MD5 and SHA-1 are cryptographically broken; practical collision attacks have been demonstrated against them, meaning an attacker could theoretically generate a forged audit row that produces the exact same hash. SHA-256 has a 256-bit digest size with collision resistance of $2^{128}$ operations, making computational collision attacks physically impossible on modern hardware. It is the NIST standard for cryptographic hash chaining."
- **Reference:** Chapter 4 (Section 4.4) | Slide 10

---

### Category E: Architecture & Scalability

#### Q19. Why did you choose a client-server architecture with FastAPI instead of a standalone desktop app?
- **Spoken Answer:** "A computer lab consists of dozens of workstations. If the application were standalone, student enrollment data and audit logs would be scattered across every individual PC, requiring manual synchronization and making revocation or centralized monitoring impossible. A central FastAPI server allows a student to enroll once and log in at any available lab machine. Furthermore, FastAPI provides asynchronous high-throughput request handling and native OpenAPI Swagger documentation for administrative maintenance."
- **Reference:** Chapter 4 (Section 4.1–4.2) | Slide 6

#### Q20. Why did you implement per-device JWTs rather than a single shared API key?
- **Spoken Answer:** "Using a single shared API key creates a single point of failure: if one PC is compromised or a student extracts the key from a client script, the entire lab API is exposed, and the server cannot identify which physical computer made an API call. Per-device authentication provisions a unique `device_id` and secret for each workstation during commissioning. The server issues a short-lived 24-hour signed JWT containing the machine ID, enabling granular per-device revocation and attributing every audit log entry directly to the originating workstation."
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.1) | Slide 6, Slide 7

#### Q21. What happens if the central server or network connection drops while a student is working?
- **Spoken Answer:** "The system adheres strictly to the security principle of **Fail-Closed**. When a background verification cycle cannot reach the server or validate credentials, it does not default to open access. The client records a network failure and locks the workstation after the grace counter expires. In high-security environments, maintaining security during network partitions takes precedence over convenience to prevent attackers from unplugging Ethernet cables to bypass verification."
- **Reference:** Chapter 3 (Section 3.2), Chapter 5 (Section 5.4) | Slide 9

#### Q22. How does the system handle anti-tailgating or multiple faces appearing in the camera frame?
- **Spoken Answer:** "In academic labs, shoulder surfing and crowding around someone's monitor are common privacy risks. During background verification, our face detection counts the total number of faces in the frame. If `len(faces) > 1`, the system immediately classifies it as a potential tailgating or unauthorized observation event, logs `LOCK_MULTIPLE_FACES` at HIGH severity, dispatches an alert, and locks the screen instantly."
- **Reference:** Chapter 3 (Section 3.2), Chapter 5 (Section 5.4) | Slide 9

---

### Category F: Privacy, Ethics & Legal Compliance

#### Q23. Facial biometrics are sensitive personal data. How does your system protect student privacy?
- **Spoken Answer:** "We protect privacy through strict data minimization and cryptographic isolation. First, raw facial images and webcam video feeds are never saved to disk—they are processed in volatile RAM and immediately discarded. Second, only numerical 128-dimensional vectors are stored, and those vectors are encrypted at rest using Fernet AES-128 before reaching SQLite. Third, an embedding vector cannot be reverse-engineered back into a recognizable photograph of the student's face."
- **Reference:** Chapter 3 (Section 3.2), Chapter 4 (Section 4.4) | Slide 7, Slide 11

#### Q24. How does your system align with India's Digital Personal Data Protection (DPDP) Act 2023?
- **Spoken Answer:** "The DPDP Act mandates purpose limitation, explicit consent, and security safeguards for digital personal data. Our system aligns with this by strictly limiting biometric processing to lab access authorization; providing transparent user consent prompts during the onboarding flow; isolating encryption keys; ensuring data minimization by rejecting raw image retention; and maintaining an immutable audit log to demonstrate organizational accountability under regulatory review."
- **Reference:** Chapter 3 (Section 3.2), Chapter 4 (Section 4.4) | Slide 11, Slide 14

#### Q25. Is raw video or webcam imagery ever stored on disk or transmitted over the network?
- **Spoken Answer:** "No, sir. At no point in the lifecycle is any raw video or photographic image stored on disk or transmitted over the network. In `register.py` and `login.py`, frames captured by OpenCV exist only as NumPy arrays in memory. The moment dlib extracts the 128-point floating array, the image buffer is deallocated. Network requests to `/student/register` carry only encrypted ciphertext vectors over TLS."
- **Reference:** Chapter 4 (Section 4.3), Chapter 5 (Section 5.2) | Slide 8, Slide 11

#### Q26. How does the enrollment process ensure transparency and consent?
- **Spoken Answer:** "During enrollment, `register.py` presents an interactive console interface where the student voluntarily inputs their roll number and name and reviews a privacy declaration explaining that only mathematical coordinates will be stored for session security. The student actively confirms the capture by looking at the camera and scanning their TOTP QR code, ensuring that enrollment is an explicit opt-in procedure."
- **Reference:** Chapter 3 (Section 3.2), Chapter 5 (Section 5.2) | Slide 8, Slide 11

---

### Category G: Testing, Resilience & Limitations

#### Q27. How did you test your system, and how do automated tests verify cross-layer defense?
- **Spoken Answer:** "We built an automated defense-in-depth integration test harness in `test_integration.py` utilizing FastAPI's in-memory `TestClient`. It executes 9 automated validation vectors testing end-to-end interactions: per-device provisioning and JWT issuance, E2EE registration and Fernet decryption parity, TOTP code validation, expired token rejection, hash chain cryptographic integrity, and simulated SQL database tampering where the test deliberately alters a confidence score and asserts that the chain detects the tampering."
- **Reference:** Chapter 6 (Section 6.1–6.3) | Slide 12

#### Q28. What happens under poor lighting or if a student turns slightly while typing?
- **Spoken Answer:** "To prevent false rejections caused by natural movements or lighting changes, we implemented **confidence-scored risk banding** and a **grace period counter**. Instead of a binary match/fail, scores between $0.50$ and $0.60$ are classified as borderline and logged as MEDIUM severity without immediately locking the PC. Furthermore, if a student looks down at their keyboard and the camera temporarily loses their face, the system grants one 30-second grace period (`missed_checks = 1`), locking only if two consecutive checks fail."
- **Reference:** Chapter 5 (Section 5.4), Chapter 7 (Section 7.3) | Slide 9

#### Q29. What happens if a teacher or lab assistant needs to sit next to a student to help debug code?
- **Spoken Answer:** "Normally, two people in the camera frame triggers the anti-tailgating lockout. To support legitimate lab instruction, we built a system tray utility (`tray_app.py`) that allows authorized faculty to pause continuous monitoring. To prevent students from abusing this to leave workstations permanently unlocked, the pause feature has an **Anti-Tamper Auto-Resumption Failsafe**: it automatically re-engages monitoring after a maximum of 300 seconds (5 minutes) and writes a HIGH-severity event to the audit log."
- **Reference:** Chapter 5 (Section 5.5), Chapter 7 (Section 7.3) | Slide 9

#### Q30. What are the primary technical limitations of your system?
- **Spoken Answer:** "We have three documented limitations: first, we rely on standard RGB 2D webcams, which lack hardware depth sensing and are vulnerable to sophisticated 3D masks; second, extreme darkness or strong direct backlighting degrades facial landmark extraction; and third, while our audit log detects database tampering, a malicious local administrator who rewrites the entire SQLite database file and restarts the chain from the Genesis Hash could theoretically forge a clean ledger. We document all three transparently as future work."
- **Reference:** Chapter 7 (Section 7.4), Chapter 8 | Slide 14

---

## Part 2: Trap Questions & Honest Defense Strategies (8 Questions)

*Examiners ask these specific questions to catch candidates overclaiming. Use these honest, well-reasoned answers.*

---

#### Trap 1: "If I hold up a high-resolution iPad playing a video of the student blinking and turning their head, does your system pass?"
- **The Attack:** The examiner is challenging your liveness detection's resistance to video replay attacks.
- **Honest Spoken Answer:**  
  "If the attacker guesses the exact randomized challenge and plays the matching clip within 4 seconds, there is a possibility a 2D camera could be fooled. We do not claim 100% immunity against targeted video playback on standard webcams.  
  However, our system significantly raises the attacker's work factor: the prompt is chosen at random after login begins, giving an attacker only 4 seconds to locate, queue, and position the correct motion clip. Furthermore, on the successful frame, our system verifies that the face performing the motion matches the enrolled student's biometric vector. To completely eliminate high-resolution screen replays, hardware-level active infrared structured light—such as an Intel RealSense or Apple TrueDepth sensor—is necessary, which is our primary future work recommendation."
- **Examiner Takeaway:** Shows you understand presentation attack detection levels and hardware limitations without pretending software solves physics.
- **Reference:** Chapter 7 (Section 7.4) | Slide 8, Slide 14

---

#### Trap 2: "Who protects the server's encryption key? If an attacker gets physical admin access to the PC, haven't they won anyway?"
- **The Attack:** The examiner is questioning the value of OS Keyring isolation.
- **Honest Spoken Answer:**  
  "Yes, sir, under standard physical security axioms, if an attacker gains unrestricted physical root access to an unlocked running machine, memory dump attacks can eventually extract keys. No software architecture can defend against a compromised physical host.  
  What our OS Keyring isolation defends against is **database exfiltration and credential dumping**. If an attacker exploits an SQL injection vulnerability or steals a database backup from the server disk, they obtain only encrypted Fernet blobs. They cannot decrypt the biometrics without the OS master key, preventing offline credential cracking. For enterprise deployments, this key would be backed by a hardware TPM chip or an external Hardware Security Module (HSM)."
- **Examiner Takeaway:** Differentiates between physical host compromise and database exfiltration boundaries (CWE-798 mitigation).
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.1) | Slide 7

---

#### Trap 3: "If I am the rogue lab administrator with full SQLite database access, can't I just modify a log entry and recompute all subsequent hashes from that point forward?"
- **The Attack:** Challenging the immutability of an in-database hash chain.
- **Honest Spoken Answer:**  
  "That is an accurate observation. Because the SQLite database is local, a rogue administrator with direct write access could alter row 10 and write a Python script to recalculate hashes for rows 11 through 50, creating a mathematically consistent falsified chain on that single machine.  
  Our hash chain specifically defends against **opportunistic or localized log tampering**, such as an insider updating a single confidence score or deleting an embarrassing lockout record. To fully prevent full-chain recomputation by a root administrator, the current head hash must be periodically anchored to an external, append-only system—such as an RFC 3161 timestamping authority or a remote syslog server. We have documented this exact threat in our Chapter 7 discussion."
- **Examiner Takeaway:** Demonstrates deep cryptographic maturity by acknowledging local ledger limits versus decentralized anchoring.
- **Reference:** Chapter 5 (Section 5.4), Chapter 7 (Section 7.3) | Slide 10, Slide 14

---

#### Trap 4: "You use self-signed TLS certificates in your implementation. Isn't self-signed TLS insecure and vulnerable to Man-in-the-Middle attacks?"
- **The Attack:** Pointing out that self-signed certificates trigger browser warnings and lack CA trust.
- **Honest Spoken Answer:**  
  "In a public internet context, yes, unvetted self-signed certificates invite Man-in-the-Middle attacks because clients cannot verify identity through a trusted public Certificate Authority.  
  However, in our project, this operates in a closed institutional intranet where public domain validation is not feasible. To mitigate MitM risks in production, our architecture uses certificate pinning: the lab client workstation explicitly trusts only the specific root certificate generated by `gen_cert.py` for that lab cluster, rejecting any rogue certificates. For campus-wide deployment, the certificates would be signed by the university's internal private Public Key Infrastructure (PKI)."
- **Examiner Takeaway:** Distinguishes public PKI from enterprise intranet certificate pinning.
- **Reference:** Chapter 4 (Section 4.4), Chapter 5 (Section 5.1) | Slide 6, Slide 7

---

#### Trap 5: "Your face recognition relies on dlib and Euclidean distance. Can't identical twins or high-quality 3D masks easily bypass this?"
- **The Attack:** Probing fundamental limitations of 2D facial biometrics.
- **Honest Spoken Answer:**  
  "Identical twins have virtually identical 2D facial bone structure, meaning dlib's Euclidean distance would indeed evaluate them as a match. Similarly, a custom 3D silicone mask with correct eye-spacing could fool a standard 2D camera.  
  This is precisely why our architecture enforces **Three-Factor Authentication rather than biometrics alone**. Even if an identical twin attempts to log in as their sibling, they cannot complete authentication without possessing the victim's physical smartphone to provide the rotating TOTP code. Biometrics provide inherence, but TOTP guarantees possession."
- **Examiner Takeaway:** Reinforces the core value of multi-factor defense-in-depth: when one factor has an inherent biological weakness, the other factor catches it.
- **Reference:** Chapter 3 (Section 3.3), Chapter 4 (Section 4.3) | Slide 7, Slide 8

---

#### Trap 6: "Your background check runs every 30 seconds. What prevents an attacker from doing something malicious in the 29 seconds between checks?"
- **The Attack:** Attacking the temporal granularity of the continuous verification cycle.
- **Honest Spoken Answer:**  
  "There is a 30-second window between verification cycles. In security engineering, verification frequency is a trade-off between the attack window, CPU utilization, and user distraction.  
  If we checked every 2 seconds, the webcam LED would blink continuously, causing thermal throttling and distracting students during programming tasks. More importantly, comparing the 30-second window to the existing baseline—where unattended workstations remain completely unlocked for 10 to 15 minutes until a screensaver timeout—our system reduces the vulnerability window by over 90%. In high-risk environments like online exams, the interval in `config.json` can simply be reduced to 10 seconds."
- **Examiner Takeaway:** Shows practical systems engineering thinking—balancing security boundaries against resource constraints and user experience.
- **Reference:** Chapter 3 (Section 3.2), Chapter 7 (Section 7.3) | Slide 9

---

#### Trap 7: "If network connectivity drops between the PC and the server, your system locks the screen. Isn't that an easy Denial of Service against students during exams?"
- **The Attack:** Highlighting operational friction caused by fail-closed policies.
- **Honest Spoken Answer:**  
  "In an academic environment, an unexpected lock during an exam is indeed an operational disruption. However, from a cybersecurity posture, **Failing Open is catastrophic**: an attacker who knows that network failure keeps the PC unlocked could simply disconnect the Ethernet cable or spoof a DHCP failure to permanently disable all security controls.  
  To soften the operational impact without compromising security, we implemented a 1-cycle grace period (30 seconds) before locking. If network dropouts are frequent in a specific lab, the system can cache a short-lived cryptographically signed offline lease, allowing temporary local verification while logging a warning."
- **Examiner Takeaway:** Clearly justifies why security systems must fail-closed, while proposing pragmatic operational mitigations (cached offline leases).
- **Reference:** Chapter 3 (Section 3.2), Chapter 5 (Section 5.4) | Slide 9

---

#### Trap 8: "Why build a custom access lock in Python instead of using Microsoft Active Directory Group Policies or Windows Hello Enterprise?"
- **The Attack:** Questioning the practical need for a custom academic software project.
- **Honest Spoken Answer:**  
  "Active Directory and Windows Hello are powerful commercial tools, but they have major limitations in resource-constrained academic environments. First, Windows Hello requires specialized, expensive infrared depth cameras on every machine, which most colleges cannot afford. Second, Active Directory does not support continuous mid-session face verification or randomized challenge-response anti-spoofing on commodity webcams. Third, Active Directory relies on heavy centralized domain controllers and proprietary licensing.  
  Our project proves that an institution can achieve multi-factor authentication, continuous zero-trust session governance, and cryptographic audit logging using **standard commodity webcams and free, open-source Python libraries**."
- **Examiner Takeaway:** Explains economic, technical, and operational feasibility brilliantly (justifying the B.Tech project's existence).
- **Reference:** Chapter 1 (Section 1.3), Chapter 3 (Section 3.4) | Slide 4, Slide 5

---

## Part 3: Spoken Presentations (Timed Scripts)

---

### The 30-Second Elevator Pitch
> *"Good morning, respected examiners. Institutional computer labs face a major cybersecurity gap: proxy attendance and unattended terminal hijacking. Existing systems authenticate a user once at login and remain completely blind afterward.  
> Our project introduces a **Continuous, Zero-Trust Access Lock System**. We combine Three-Factor Authentication—roll number, TOTP, and randomized face liveness—with a background daemon that verifies student presence every 30 seconds, automatically locking the workstation if the student leaves or an impostor steps in.  
> All biometrics are Fernet-encrypted at rest in the OS Keyring, network traffic is protected via TLS and per-device JWTs, and audit logs are secured in a tamper-evident SHA-256 hash chain—providing continuous security using commodity webcams."*

---

### The 2-Minute Comprehensive Viva Pitch
> *"Respected examiners, computer laboratories in educational institutions handle sensitive academic portals, practical examinations, and proprietary software. However, their physical access security remains fundamentally broken. Students frequently share credentials to submit peer assignments, and when a legitimate user walks away from an open terminal, the session remains vulnerable for up to 15 minutes before screensavers kick in.  
> 
> To eliminate this vulnerability window, we designed and built the **Lab Face-Verified Access Lock System**.  
> 
> Our architecture operates across three synchronized tiers:  
> 
> First, at the authentication boundary, we enforce strict **Three-Factor Verification**: identity claim via roll number, physical possession via Google Authenticator TOTP codes, and biometric inherence via facial verification. To defeat photo and video replay attacks, we implemented an active, randomized challenge-response liveness check that verifies blinking, mouth movement, or head turns within a 4-second window, while confirming the mover's identity.  
> 
> Second, we introduce **Continuous Session Governance**. Authentication does not terminate at login. A background worker thread executes every 30 seconds, evaluating facial presence and Euclidean distance against the decrypted template. If the student walks away, a 30-second grace period triggers, followed by an immediate fail-closed OS-level workstation lock. If an unauthorized peer sits down or multiple faces are detected, the system locks instantly.  
> 
> Third, we established a **Defense-in-Depth Cryptographic Layer**. We store zero raw images. 128-dimensional biometric embeddings are encrypted using authenticated Fernet AES-128, with master keys isolated in the host OS Keyring enclave. Network communication across lab PCs uses TLS and per-device JWT tokens. Finally, all system events are written to an append-only SQLite audit log protected by a mathematical SHA-256 hash chain, ensuring that any unauthorized log alteration is immediately detected.  
> 
> Our automated test harness confirms that all security layers pass with zero cross-layer defects, delivering an enterprise-grade, zero-trust security architecture on standard commodity hardware. Thank you, and I am ready for your questions."*

---

## Part 4: "When You Don't Know The Answer" Cheat Sheet

*Use these structured phrasing strategies if an examiner asks something unexpected or highly theoretical.*

| Situation | What NOT to Do | What to Say (Spoken Script) |
| :--- | :--- | :--- |
| **Edge-case attack vector you haven't considered** | Don't bluff or invent fake algorithms. | *"That is a very sharp attack vector, sir. In our current implementation, we designed primarily against 2D presentation attacks and physical session hijacking. If I were to mitigate that specific attack, I would approach it by [mentioning depth sensors, tighter thresholds, or out-of-band MFA alerts]. We have noted that as a valuable direction for future hardening."* |
| **Deep mathematical question about dlib or ResNet weights** | Don't recite memorized random formulas. | *"The underlying facial feature extraction uses dlib's pre-trained ResNet deep metric model, which maps facial landmarks into a 128-dimensional Euclidean space where distance correlates with facial difference. While our project focuses on the system-level access control, encryption, and session governance layers, the core mathematical metric we evaluate directly is the Euclidean norm $d = \lVert x_1 - x_2 \rVert_2 \le 0.60$."* |
| **Theoretical legal / DPDP Act clause number** | Don't guess legal sections or pretend to be a lawyer. | *"While I do not have the specific section clause number committed to memory, our technical architecture was designed to satisfy the core principles of the DPDP Act 2023—specifically Data Minimization by discarding raw camera frames, Storage Limitation through encrypted vectors, and Audit Accountability through our SHA-256 hash chain."* |
| **Examiner insists your system can be bypassed** | Don't become defensive or argue aggressively. | *"I agree with you, sir—no security system provides 100% absolute defense, especially on standard commodity webcams without active infrared sensors. Our design objective was to dramatically increase the attacker's work factor and eliminate the 15-minute unattended session gap. Your point highlights exactly why hardware depth sensors are our top future improvement."* |

---

## Part 5: Master Viva Question-to-Report Cross-Reference Matrix

| Question # | Topic | Report Chapter & Section | Presentation Slide # |
| :---: | :--- | :--- | :---: |
| **Q1** | Problem Statement & Need | Chapter 1 (1.1, 1.2) | Slide 2 |
| **Q2** | Password / RFID Inadequacy | Chapter 1 (1.2), Chapter 2 | Slide 2, 4 |
| **Q3** | Continuous Auth Differentiator | Chapter 1 (1.3), Chapter 3 | Slide 5 |
| **Q4** | Project Objectives | Chapter 1 (1.4) | Slide 3 |
| **Q5** | 3-Factor Authentication Pipeline | Chapter 4 (4.3), Chapter 5 (5.3) | Slide 7, 8 |
| **Q6** | Continuous Verification Logic | Chapter 3 (3.2), Chapter 5 (5.4) | Slide 9 |
| **Q7** | 128-d Vector Face Encodings | Chapter 4 (4.4), Chapter 5 (5.2) | Slide 8, 11 |
| **Q8** | Euclidean Distance & Scoring | Chapter 4 (4.3), Chapter 5 (5.3) | Slide 8, 9 |
| **Q9** | FAR vs. FRR Trade-off | Chapter 2 (2.4), Chapter 7 (7.3) | Slide 8, 14 |
| **Q10** | Presentation Attack Vectors | Chapter 3 (3.3), Chapter 7 (7.2) | Slide 8, 14 |
| **Q11** | Challenge-Response Liveness | Chapter 4 (4.3), Chapter 5 (5.3) | Slide 8 |
| **Q12** | 4.0-Second Liveness Window | Chapter 5 (5.3), Chapter 7 (7.3) | Slide 8 |
| **Q13** | Deepfake & Video Replay Defense | Chapter 3 (3.3), Chapter 7 (7.4) | Slide 8, 14 |
| **Q14** | Fernet Symmetric Encryption | Chapter 4 (4.4), Chapter 5 (5.2) | Slide 7, 11 |
| **Q15** | OS Keyring Master Key Isolation | Chapter 4 (4.4), Chapter 5 (5.1) | Slide 7 |
| **Q16** | Transport Layer Security (TLS) | Chapter 4 (4.4), Chapter 5 (5.1) | Slide 6, 7 |
| **Q17** | SHA-256 Hash Chained Logs | Chapter 4 (4.4), Chapter 5 (5.4) | Slide 7, 10 |
| **Q18** | Why SHA-256 (Collision Resistance)| Chapter 4 (4.4) | Slide 10 |
| **Q19** | Multi-PC FastAPI Client-Server | Chapter 4 (4.1, 4.2) | Slide 6 |
| **Q20** | Per-Device OAuth2 JWT Tokens | Chapter 4 (4.4), Chapter 5 (5.1) | Slide 6, 7 |
| **Q21** | Fail-Closed Policy on Disconnect | Chapter 3 (3.2), Chapter 5 (5.4) | Slide 9 |
| **Q22** | Anti-Tailgating Multiple Faces | Chapter 3 (3.2), Chapter 5 (5.4) | Slide 9 |
| **Q23** | Biometric Data Privacy & Storage | Chapter 3 (3.2), Chapter 4 (4.4) | Slide 7, 11 |
| **Q24** | India DPDP Act 2023 Compliance | Chapter 3 (3.2), Chapter 4 (4.4) | Slide 11, 14 |
| **Q25** | Zero Raw Image Disk Persistence | Chapter 4 (4.3), Chapter 5 (5.2) | Slide 8, 11 |
| **Q26** | Explicit Enrollment Consent | Chapter 3 (3.2), Chapter 5 (5.2) | Slide 8, 11 |
| **Q27** | Automated Defense-in-Depth Tests | Chapter 6 (6.1–6.3) | Slide 12 |
| **Q28** | Lighting & Grace Periods | Chapter 5 (5.4), Chapter 7 (7.3) | Slide 9 |
| **Q29** | Faculty Pause & Auto-Resume | Chapter 5 (5.5), Chapter 7 (7.3) | Slide 9 |
| **Q30** | Stated Limitations | Chapter 7 (7.4), Chapter 8 | Slide 14 |
| **Trap 1** | iPad Video Screen Replay | Chapter 7 (7.4) | Slide 8, 14 |
| **Trap 2** | Physical Keyring Access | Chapter 4 (4.4), Chapter 5 (5.1) | Slide 7 |
| **Trap 3** | Admin Recomputing Hash Chain | Chapter 5 (5.4), Chapter 7 (7.3) | Slide 10, 14 |
| **Trap 4** | Self-Signed TLS Certificates | Chapter 4 (4.4), Chapter 5 (5.1) | Slide 6, 7 |
| **Trap 5** | Identical Twins / 3D Masks | Chapter 3 (3.3), Chapter 4 (4.3) | Slide 7, 8 |
| **Trap 6** | 30-Second Verification Window | Chapter 3 (3.2), Chapter 7 (7.3) | Slide 9 |
| **Trap 7** | DoS from Fail-Closed Disconnect | Chapter 3 (3.2), Chapter 5 (5.4) | Slide 9 |
| **Trap 8** | Why Not Active Directory? | Chapter 1 (1.3), Chapter 3 (3.4) | Slide 4, 5 |

---
*End of Mock Viva Preparation Pack*
