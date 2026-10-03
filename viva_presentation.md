# Viva Presentation: Slide Content
**Lab Face-Verified Access Lock System**

> Rule for the deck: max 5 bullets per slide, one idea per line. Say more than you show.

---

## PART A: SLIDES

### Slide 1: Title
**Lab Face-Verified Access Lock System**
*Continuous Biometric Access Control for Shared Computer Labs*
- Dipak Shinde (Roll No: ______)
- Guide: [Guide Name], [Designation]
- Department of [CSE / Cyber Security]
- Tatyasaheb Kore Institute of Engineering & Technology (TKIET), Warananagar
- B.Tech Final Year Project, 2025–26

**Visual:** College logo top-left. One clean icon in the centre (face outline inside a padlock). Nothing else.

---

### Slide 2: The Problem: "Log in once, trusted forever"
- Lab PCs check identity **only at login**
- Student walks away, session stays **open**
- Anyone can sit down and act **as them**
- Logs can't prove **who** was really at the keyboard

**Visual:** 3-panel strip: (1) student logs in → (2) student leaves seat → (3) a different person typing on the same unlocked PC, red "!" on panel 3.

---

### Slide 3: Objectives
- Strong login with **3 factors**
- Re-verify identity **every 30 seconds**
- **Auto-lock** on absence, stranger, or second face
- Block **photo/video spoofing** with liveness
- Keep logs **encrypted and tamper-evident**

**Visual:** 5 numbered icons in a row (key, clock, lock, eye, chain-link).

---

### Slide 4: Existing Systems & the Gap

| | Password / PIN | Face/Fingerprint at login | Windows Dynamic Lock | **Proposed** |
|---|:---:|:---:|:---:|:---:|
| Checks after login? | ✗ | ✗ | Phone distance only | **✓ every 30 s** |
| Knows *who* is sitting? | ✗ | Only at login | ✗ | **✓** |
| Stops photo spoof? | n/a | Often ✗ | n/a | **✓ liveness** |
| Extra hardware | None | Scanner | Phone per student | **Webcam only** |

- **Gap:** no one verifies identity *during* the session on a shared lab PC

**Visual:** The table itself, with the "Proposed" column highlighted in your accent colour.

---

### Slide 5: Proposed System
> **"A lab PC that keeps checking it's still you, and locks the moment it isn't."**

- Login: roll no. + face + authenticator code + liveness
- Face re-check in the background every 30 s
- Auto-lock: no face · wrong face · two faces · server down
- One central server for all lab PCs, every event logged

**Key differentiator badge:** **CONTINUOUS** authentication, not one-time.

**Visual:** Large pitch line as a quote, plus a bold "CONTINUOUS" badge/stamp.

---

### Slide 6: System Architecture
- **Lab PCs:** camera, face check, OS lock
- **Central FastAPI server:** students, devices, logs
- **HTTPS (TLS) + per-device JWT** on every request
- **Discord webhook:** instant HIGH-severity alerts

**Visual:** Clean block diagram (draw in PPT using this as the layout):
```
 [Lab PC 1] [Lab PC 2] ... [Lab PC N]      (camera + keyring + OS lock)
      \          |            /
       \   HTTPS + JWT token /
        v        v          v
     [ Central FastAPI Server ] ---> [ Discord Alerts ]
                 |
          [ SQLite Database ]
   (students · devices · hash-chained logs)
```

---

### Slide 7: Security Features (KEY SLIDE)
One tile per layer: **Feature / How / Stops**

| # | Feature | How | Stops |
|:-:|---|---|---|
| 1 | **MFA (3-factor)** | Roll no. + face + TOTP code | Shared / stolen passwords |
| 2 | **Liveness** | Random: blink / mouth / turn L / turn R in 4 s | Photo & video replay |
| 3 | **Continuous auth** | Face re-check every 30 s | Walk-away takeover |
| 4 | **Encryption at rest** | Fernet (AES + HMAC), key in OS keyring | Stolen database file |
| 5 | **TLS** | All client–server traffic over HTTPS | Network sniffing |
| 6 | **JWT per device** | Each lab PC has its own token (24 h expiry) | Rogue laptops calling the API |
| 7 | **Hash-chained logs** | Each entry carries SHA-256 of the previous | Silent log editing |
| 8 | **Real-time alerts** | Discord webhook on HIGH events | Late response to attacks |

**Footer strip:** *Plus: fail-closed design · confidence-scored face matching*

**Visual:** 4×2 grid of tiles, one icon each, colour-coded by layer:
- Blue = identity (MFA, liveness, continuous auth)
- Green = data protection (encryption, TLS, JWT)
- Orange = monitoring (hash chain, alerts)
On the slide, show only **Feature + one-line "Stops"** per tile. Keep the "How" column for your speech.

---

### Slide 8: 3-Factor Login Flow
1. **Roll number:** 3 wrong tries → locked out
2. **Face match:** confidence score, below 0.50 rejected
3. **TOTP:** 6-digit code from authenticator app
4. **Liveness:** random challenge within 4 s
- All pass → session starts + background monitor begins

**Visual:** Horizontal flowchart: 4 boxes with green ✓ arrows to the next step; each box has a red ✗ arrow down to one shared box: **"Denied + logged + alert"**.

---

### Slide 9: Continuous Verification & Fail-Closed
Every 30 s the camera checks:
- Match **> 0.60** → OK, logged
- **0.50 – 0.60** → allowed, flagged MEDIUM
- **< 0.50** or **2+ faces** → lock now + alert
- **No face for 2 checks (~60 s)** → lock
- **Server unreachable** → lock (fail-closed)

**Visual:** Decision tree with traffic-light colours: green (OK), yellow (flag), red (LOCK). Put a big padlock at every red end.

---

### Slide 10: Tamper-Evident Logging
- Each entry hashes **its own data + the previous hash**
- Edit one row → its hash breaks → **every later link breaks**
- `log_viewer.py --verify-integrity` finds the **exact row**
- Confidence score is **inside** the hash, so a score can't be faked

**Visual:** Two rows of chained blocks:
```
OK:       [Genesis 000…] → [#1 LOGIN | h1] → [#2 MATCH 0.88 | h2] → [#3 LOCK | h3]

TAMPERED: [Genesis 000…] → [#1 LOGIN | h1] → [#2 MATCH 0.98 ✗] → [#3 LOCK ✗]
```
Colour the tampered block and everything after it red.

---

### Slide 11: Database Schema
- **students:** roll_number (PK), name, face_encoding 🔒, totp_secret 🔒
- **devices:** device_id (PK), label, secret, revoked
- **logs:** event, severity, confidence, entry_hash, previous_hash
- **No face photos stored**, only an encrypted 128-number vector

**Visual:** 3-box ER diagram: `students 1 ── M logs M ── 1 devices`, padlock icon on the encrypted columns.

---

### Slide 12: Testing Summary
- **Automated integration suite: all checks PASS** (can run live)
- Layer interactions tested: **expired JWT**, **liveness fail mid-chain**, **score tampering**
- Manual edge-case sweep: server down, corrupted data, brute force, multiple faces, session reset
- Tamper test: score changed **0.88 → 0.98**, caught at the exact row

**Visual:** Small PASS table (Test → ✓) + one screenshot of the terminal summary output.

---

### Slide 13: Results / Demo
*[PLACEHOLDER: insert screenshots]*
- Registration + TOTP QR code
- Liveness challenge prompt with countdown
- Lock triggered + Discord alert
- Log viewer + integrity check (SUCCESS and TAMPER DETECTED)

**Visual:** 2×2 screenshot grid. If the panel allows it, **demo live** and keep this slide as backup.

---

### Slide 14: Limitations & Future Work

| Limitation (honest) | Next step |
|---|---|
| 2D webcam can't stop a realistic 3D mask | IR / depth camera |
| Self-signed TLS certificate (demo) | College certificate authority |
| No instant JWT revoke (valid until 24 h expiry) | Token blacklist |
| A full DB admin could rebuild the whole chain | Publish latest hash outside the server daily |
| Low light / face masks → more false locks | Adaptive thresholds, better lighting |

**Visual:** Two-column table, left in grey, right in your accent colour.

---

### Slide 15: Conclusion
- From **"trust once"** to **"verify continuously"**
- 8 security layers, **tested together** as one system
- Runs on **existing webcams**, no new hardware
- **Fails safe:** when in doubt, it locks

**Thank you. Questions?**

**Visual:** The 8 feature icons from Slide 7, small, in one row above "Thank you".

---

## PART B: SPEAKER NOTES (say this, don't read the slide)

**Slide 1:** "Good morning. I'm Dipak Shinde, and my project is the Lab Face-Verified Access Lock System, guided by [Guide Name]. In one line: it makes sure the person using a lab computer is the person who logged in, for the whole session, not just at the start."

**Slide 2:** "In our labs, the computer checks who you are only once, at login. After that, if you get up to ask a teacher something or collect a printout, your session is wide open, and anyone can sit down and submit work in your name. And later, nothing in the logs can prove it wasn't you."

**Slide 3:** "So I set five goals: a strong three-factor login, re-checking identity every 30 seconds, locking the PC automatically, stopping people from fooling the camera with a photo, and keeping records that can't be secretly edited."

**Slide 4:** "Passwords get shared, face or fingerprint login checks you only once, and Windows Dynamic Lock only checks whether your phone is nearby. It has no idea who is actually sitting there. None of them keep verifying identity *during* the session on a shared lab PC, and that's the exact gap I targeted."

**Slide 5:** "My system keeps asking one question every 30 seconds: is this still the same person? If the answer is no, or nobody's there, the PC locks itself. That continuous part is the main thing that's different from everything else."

**Slide 6:** "Each lab PC runs the client, which handles the camera, face checking and the lock. All PCs talk to one central FastAPI server, always over HTTPS, and every PC has to prove its own identity with a token before the server accepts anything. Serious events go out instantly as Discord alerts to the lab admin."

**Slide 7:** "This slide is the whole project on one page. Each tile is one security layer and the attack it stops. For example, liveness stops photo tricks, encryption protects the data if someone copies the database, and the hash chain stops anyone quietly editing logs. The idea is defense in depth: if one layer is beaten, the next one still catches you."

**Slide 8:** "Login has four gates. You enter your roll number, the camera matches your face and gives a confidence score, you type the six-digit code from your authenticator app, and finally you do a random action like 'turn left' within four seconds. Fail any gate and you're denied and it's logged. Three failures and that roll number is locked out on that terminal."

**Slide 9:** "Once you're in, the camera checks again every 30 seconds. A strong match means nothing happens. A borderline match means you keep working but it's flagged. A stranger or a second face means it locks immediately and alerts the admin. If you're gone for two checks, about a minute, it locks. And if the server can't be reached it also locks, because the system is built to fail closed, never open."

**Slide 10:** "Every log entry stores a fingerprint of itself plus the fingerprint of the entry before it, so they form a chain. If someone edits even one number, say a confidence score, that link breaks and every link after it breaks too. One command checks the whole chain and points to the exact row that was changed."

**Slide 11:** "There are just three tables: students, devices and logs. The important point is that we never store face photos. We store a 128-number face vector, and even that is encrypted, along with the TOTP secret. The encryption key itself lives in the Windows keyring, not in the code or the database."

**Slide 12:** "I tested in two stages. First a manual edge-case sweep: server down, corrupted data, repeated wrong attempts, multiple faces. Then an automated integration test that checks the layers working together. Every check passes, and I can run it live right now if you'd like."

**Slide 13:** "These are the main screens: registration with the QR code, the liveness prompt, the lock with the Discord alert, and the integrity check. If there's time, I'd rather show it to you live."

**Slide 14:** "I want to be upfront about the limits. A normal webcam can't stop a realistic 3D mask, the certificate is self-signed for the demo, and someone with full database control could in theory rebuild the whole chain. Each of these has a clear next step: an IR camera, a college certificate authority, and publishing the latest hash outside the server every day."

**Slide 15:** "To sum up, this changes lab PCs from 'trust you once' to 'keep checking it's you', using webcams the lab already has. And when anything goes wrong, it locks rather than staying open. Thank you, I'm happy to take questions."

---

## PART C: SLIDES MOST LIKELY TO BE ATTACKED (and your one-line defense)

**1. Slide 8: Login flow**
- **If they ask:** *"Face match and liveness are separate steps. Couldn't someone show your photo for the face match, then do the liveness action with their own face?"*
- **Say:** "On its own, yes, but they'd still need my phone for the TOTP code, and the 30-second check would see their real face and lock. Running the face match on the same frames as the liveness challenge is my next fix."

**2. Slide 7 / 14: Liveness**
- **If they ask:** *"What about a 3D mask or a deepfake?"*
- **Say:** "A normal 2D webcam can't fully stop a realistic 3D mask. That needs IR depth hardware, which is listed future work. A recorded video can't follow a random prompt in 4 seconds, and the attacker still needs the TOTP code."

**3. Slide 10: Hash-chained logs**
- **If they ask:** *"The admin owns the database. Can't he just recompute every hash?"*
- **Say:** "Yes. The chain makes tampering *detectable*, not *impossible*. The fix is to publish the latest hash outside the server every day, by email or through a timestamp authority, so a rebuilt chain won't match."

**4. Slide 9: Continuous verification**
- **If they ask:** *"So an impersonator still gets up to 30 seconds?"*
- **Say:** "Yes. The interval is a trade-off between camera and CPU load and exposure, and it's one value in `config.json`, so an exam lab can lower it. The lock event still records exactly when and on which PC it happened."

**Also be ready for:**
- *"Self-signed cert, so isn't a man-in-the-middle attack possible?"* → "For the demo, yes. In production, clients trust only the college's certificate authority. JWTs also expire in 24 hours, and a revocation blacklist is listed future work."
- *"Is storing student biometrics ethical?"* → "We store only an encrypted 128-number vector, never photos, which is data minimisation, the same principle India's DPDP Act 2023 is built on. In a real deployment, enrolment would include written student consent."
