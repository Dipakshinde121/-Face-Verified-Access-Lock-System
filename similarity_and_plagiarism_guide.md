# Plagiarism & Similarity Reduction Guide
## Lab Face-Verified Access Lock System
**Department of Computer Science & Engineering / Cybersecurity**  
**Pre-Submission Turnitin / DrillBit Similarity Defense**

---

## 1. High-Risk Sections Identified by Similarity Scanners

Automated similarity algorithms (Turnitin, DrillBit, Urkund/Ouriginal, iThenticate) flag verbatim n-gram overlaps. In academic computing and cybersecurity reports, the sections most vulnerable to high similarity scores are:

1. **Chapter 2 (Literature Review & Related Work):** Quoting descriptions of existing biometric systems, commercial turnstiles, or standard papers.
2. **Standard Definitions (MFA, Zero Trust, HOG, Dlib, Fernet, TOTP):** Repeating standard textbook definitions of NIST SP 800-63B, RFC 6238, or OWASP Top 10.
3. **Common Cryptographic Formulas:** Copying verbatim mathematical descriptions of Euclidean distance or SHA-256 compression functions.
4. **Legal / Regulatory Framework Descriptions:** Copying statutory text from India's DPDP Act 2023 or GDPR articles.

---

## 2. Original Student Paraphrasing & Rewrites

Below are the high-risk sections rewritten in an **authentic, active engineering voice** that preserves technical precision while dropping automated similarity indices below 10%:

---

### High-Risk Section A: Literature Review on Continuous Authentication
- **Generic / Copied Text (High Similarity):**  
  *"Continuous authentication is an authentication method that verifies the user's identity not only at the initial login stage but repeatedly throughout the session. Traditional authentication methods such as passwords and tokens only authenticate the user at the start of a session, leading to vulnerability windows."*
- **Rewritten Original Text (Low Similarity - Student Voice):**  
  *"Unlike perimeter-only access gates that issue permanent session trust upon initial verification, continuous authentication treats identity as an ephemeral property that requires ongoing validation. In institutional environments where unattended workstations present immediate hijacking risks, our architecture periodically polls biometric markers during the active session. This continually tests whether the individual seated at the keyboard matches the student who initially cleared the three-factor login gate [1], [10]."*

---

### High-Risk Section B: Presentation Attack Detection (Liveness) & EAR
- **Generic / Copied Text (High Similarity):**  
  *"Eye Aspect Ratio (EAR) was introduced by Soukupová and Čech in 2016 for detecting eye blinks in video streams. The formula calculates the ratio of distances between vertical eye landmarks to the distance between horizontal landmarks. When the eye closes, the EAR drops significantly."*
- **Rewritten Original Text (Low Similarity - Student Voice):**  
  *"To determine whether an observed subject exhibits genuine biological vitality rather than a static paper portrait, we quantify orbital aperture using the Eye Aspect Ratio formulation established by Soukupová and Čech [7]. By computing the geometric ratio between two orthogonal vertical landmark vectors ($P_2-P_6$ and $P_3-P_5$) against the horizontal eye width ($P_1-P_4$), a transient drop below $0.25$ indicates an involuntary palpebral occlusion (a human blink). Crucially, our pipeline couples this physiological motion measurement with dynamic runtime prompts and identity matching, defeating pre-recorded looping video clips [5]."*

---

### High-Risk Section C: Time-Based One-Time Password (TOTP RFC 6238)
- **Generic / Copied Text (High Similarity):**  
  *"RFC 6238 specifies the Time-Based One-Time Password algorithm. It is an extension of the HMAC-Based One-Time Password (HOTP) algorithm, replacing the monotonic counter with an incrementing time-step derived from the current Unix epoch time divided by a 30-second window."*
- **Rewritten Original Text (Low Similarity - Student Voice):**  
  *"Physical possession is validated through the RFC 6238 standard [2], which derives transient six-digit codes from a shared 160-bit symmetric seed and the current Unix epoch. By dividing epoch seconds into discrete 30-second temporal buckets ($T = \lfloor \text{time} / 30 \rfloor$), both the server and the student's mobile device (Google Authenticator) independently calculate bitwise-identical HMAC-SHA1 digests without transmitting the underlying secret across the network. To accommodate minor clock drift across unmanaged lab terminals, our verification window tolerates a drift of $\pm 1$ step."*

---

### High-Risk Section D: Fernet Authenticated Symmetric Encryption
- **Generic / Copied Text (High Similarity):**  
  *"Fernet guarantees that a message encrypted using it cannot be manipulated or read without the key. It uses AES-128 in CBC mode and PKCS7 padding with HMAC-SHA256 for authentication."*
- **Rewritten Original Text (Low Similarity - Student Voice):**  
  *"Data-at-rest protection for biometric embeddings relies on the Fernet authenticated encryption specification [1]. Because raw 128-dimensional facial vectors cannot be securely stored in plaintext, the client serializes and encrypts them using AES-128 in Cipher Block Chaining (CBC) mode with a 128-bit randomized initialization vector. Ciphertext integrity is strictly enforced via an accompanying HMAC-SHA256 signature. Any bit-flipping attack executed against the SQLite database triggers an `InvalidToken` exception, preventing tampered biometric blobs from entering memory."*

---

### High-Risk Section E: Cryptographic Hash Chaining & Non-Repudiation
- **Generic / Copied Text (High Similarity):**  
  *"A hash chain is the successive application of a cryptographic hash function to a piece of data. In audit logging, each record contains the hash of the previous record, making it tamper-evident."*
- **Rewritten Original Text (Low Similarity - Student Voice):**  
  *"To guarantee forensic accountability without relying on proprietary database audit software, our audit subsystem constructs a forward-linked SHA-256 cryptographic hash chain rooted at a deterministic 64-character Genesis Hash ($H_0 = 0000\dots0000$) [4]. Every state transition—whether a benign continuous verification match or an unauthorized multiple-face alert—hashes its contextual fields together with the digest of the preceding row ($H_i = \text{SHA256}(\text{data}_i \parallel H_{i-1})$). Because SHA-256 exhibits extreme collision resistance, an adversary attempting to alter a historical confidence score immediately invalidates all subsequent digests, providing mathematical proof of tampering."*

---

## 3. Citation Guidelines (IEEE Reference Style)

Ensure every external concept is referenced using brackets (`[1]`, `[2]`, etc.) matching the formal bibliography:
- Use `[1]` for NIST Digital Identity Guidelines (SP 800-63B).
- Use `[2]` for RFC 6238 TOTP Standard.
- Use `[3]` for RFC 7519 JSON Web Tokens.
- Use `[4]` for RFC 6962 Certificate Transparency / Hash Chains.
- Use `[7]` for Soukupová & Čech (Real-Time Eye Blink Detection).
- Use `[8]` for Davis King (Dlib Machine Learning Toolkit).
- Use `[10]` for NIST SP 800-207 Zero Trust Architecture.

---

## 4. Pre-Check Turnitin Settings Recommendation
When submitting to your department's plagiarism portal:
1. **Exclude Bibliography / References:** Ensure the "Exclude Bibliography" toggle is enabled (citations will naturally match other papers).
2. **Exclude Small Matches (< 1% or < 8 words):** Standard institutional filtering for common technical terms like *"computer science and engineering"* or *"operating system lock"*.
3. **Target Similarity Score:** Aim for **< 10% overall similarity**, with zero individual source matches exceeding 3%.
