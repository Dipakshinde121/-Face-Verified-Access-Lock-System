# Final Cross-Artifact Consistency Sweep & Audit
## Lab Face-Verified Access Lock System
**Project Defense Verification & Architectural Alignment**

---

## 1. Parameters & Numerical Alignment Matrix

Every technical parameter, interval, cryptographic specification, and security threshold across all project files has been cross-audited against the live codebase:

| Parameter Name | Code Definition | Report (`final_project_report.md`) | Slides (`viva_presentation.md` & `.pptx`) | README (`README.md`) | Viva Pack (`mock_viva_prep_pack.md`) | Audit Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **Verification Interval** | `30` seconds (`config.py`, `config.json`) | $30\text{ seconds}$ (§3.2, §5.4) | 30s Heartbeat (Slide 5, 7, 9) | 30 seconds (§1, §2) | 30-second interval (Q6, Q28, Trap 6) | **MATCH** |
| **Grace Period Window** | `2` missed cycles / $60\text{ s}$ (`config.py`) | $60\text{ seconds}$ / 2 cycles (§3.2, §5.4) | 2 cycles / 60s timeout (Slide 9) | 2 cycles (60s) (§4) | 2 cycles / 60s timeout (Q6, Q28) | **MATCH** |
| **Biometric Distance Threshold** | `0.60` Euclidean norm (`config.py`) | $d \le 0.60$ (§4.3, §5.3) | $d \le 0.60$ (Slide 8, 9) | $d \le 0.60$ (§1, §2) | $d \le 0.60$ Euclidean distance (Q8, Q9) | **MATCH** |
| **Liveness Challenge Window** | `4.0` seconds (`liveness_check.py`) | $4.0\text{ seconds}$ (§4.3, §5.3) | 4.0s countdown (Slide 7, 8) | 4.0s timeout (§1, §4) | 4.0s challenge window (Q11, Q12, Trap 1) | **MATCH** |
| **Faculty Pause Timeout** | `300` seconds / 5 mins (`config.py`, `config.json`) | $300\text{ seconds}$ / 5 min (§5.5, §7.3) | 300s failsafe (Slide 9) | 300s failsafe (§1) | 300s auto-resumption (Q29) | **MATCH (Fixed)** |
| **Per-Device JWT Lifetime** | `24` hours (`config.py`, `server/main.py`) | 24 hours (§4.4, §5.1) | 24-hour JWT (Slide 6, 7) | 24-hour JWT (§1, §2) | 24-hour signed JWT (Q20) | **MATCH** |
| **Symmetric Encryption** | Fernet AES-128-CBC + HMAC-SHA256 (`crypto_utils.py`) | Fernet AES-128 + HMAC (§4.4) | Fernet AES-128 (Slide 6, 7) | Fernet AES-128 (§1) | Fernet AES-128 (Q14) | **MATCH** |
| **Key Enclave Store** | `keyring` (Windows Credential Manager) | OS Keyring enclave (§4.4, §5.1) | Host OS Keyring (Slide 6, 7) | Host OS Keyring (§1) | Host OS Keyring (Q15, Trap 2) | **MATCH** |
| **Transport Security** | TLS 1.2/1.3 (`server/cert.pem`) | TLS 1.2/1.3 HTTPS (§4.4) | TLS HTTPS (Slide 6, 7) | TLS / HTTPS (§1, §3) | TLS 1.2/1.3 (Q16, Trap 4) | **MATCH** |
| **Audit Ledger Hashing** | SHA-256 Hash Chain (`server/database.py`) | SHA-256 linear hash chain (§4.4) | SHA-256 hash chain (Slide 7, 10)| SHA-256 chain (§1) | SHA-256 hash chain (Q17, Q18, Trap 3) | **MATCH** |
| **Genesis Hash Value** | `0` * 64 (`server/database.py`) | $0000\dots0000$ (§4.4, §5.4) | 64-zero Genesis Block (Slide 10)| Genesis Hash (§1) | $H_0 = 0000\dots0000$ (Q17) | **MATCH** |
| **Automated Test Count** | 9 integration tests (`test_integration.py`) | 9 automated tests (§6.1, Ch. 9) | 9/9 tests passed (Slide 12) | 9 automated tests (§6) | 9 automated tests (Q27) | **MATCH** |

---

## 2. Fixed Discrepancies (Resolved)
1. **`max_pause_duration_seconds` in `config.json`:**
   - *Previous Value:* `60` seconds.
   - *Code Default & Report Value:* `300` seconds (5 minutes).
   - *Resolution:* Updated `config.json` to `"max_pause_duration_seconds": 300` to maintain absolute synchronization with `config.py`, the architectural specification, and presentation slides.
2. **Automated Test Counts in Chapter 9:**
   - *Previous Report Wording:* "...where all ten defense-in-depth test vectors passed with zero defects."
   - *Actual Test Execution:* `test_integration.py` executes 9 automated validation steps (9/9 PASS).
   - *Resolution:* Corrected Chapter 9 to explicitly state "where all nine defense-in-depth test vectors passed with zero defects".

---

## 3. Threat Model & Limitations Consistency
All documentation artifacts now maintain consistent terminology regarding system boundaries:
- **Presentation Attack Defense:** 2D printed photo and looping video replay spoofing are defended via randomized challenge-response and identity verification on the passing frame.
- **Explicit Physical Limitation:** 3D hyper-realistic silicone masks cannot be defeated on standard RGB webcams without active infrared depth sensors (e.g. Intel RealSense / Apple TrueDepth), which is consistently documented as future work across the Report (Ch. 8), Slides (Slide 14), and Viva Pack (Trap 1 & Q13).
