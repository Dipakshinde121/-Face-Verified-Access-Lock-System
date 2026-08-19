# Face-Verified Access Lock System

A clean, modular Python-based local face recognition registration and verification system utilizing OpenCV and SQLite.

## Project Structure
```
Face-Verified Access Lock System/
├── .venv/               # Isolated Python virtual environment
├── src/
│   ├── __init__.py      # Package indicator
│   └── database.py      # SQLite Database controller (schema + query logic)
├── requirements.txt     # Python project dependencies
├── webcam_test.py       # Live webcam Haar Cascade detection test script
├── register.py          # Interactive student registration system
├── view_db.py           # Text-based database inspector utility
└── README.md            # Project documentation (this file)
```

---

## Installation & Setup

1. **Activate the Virtual Environment**:
   - On Windows PowerShell:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```
   - On Windows CMD:
     ```cmd
     .venv\Scripts\activate.bat
     ```

2. **Verify Dependencies**:
   - Dependencies are defined in `requirements.txt` and have already been configured and verified. If you need to reinstall them:
     ```powershell
     pip install -r requirements.txt
     ```

---

## How to Run & Test

### 1. Test Webcam Face Tracking
To verify your camera is connected and runs real-time detection, run:
```powershell
python webcam_test.py
```
- It loads OpenCV's built-in Haar Cascade face classifier.
- Press **`q`** inside the webcam frame to exit.

### 2. Register Students
To register new students with face encodings, run:
```powershell
python register.py
```
1. Input a **Roll Number** (e.g. `21BCE001`) and **Student Name** (e.g. `John Doe`).
2. If the roll number is already in the database, the system will warn you and ask if you want to overwrite.
3. A live camera feed will open with cyan boxes around any detected faces to help you frame the shot.
4. Press **`c`** to capture a photo:
   - If **no faces** or **multiple faces** are in view, it will show an error alert and let you retake.
   - If **exactly one face** is in view, it compiles a 128-dimensional face encoding vector, saves it to SQLite, and displays a success message.
5. Press **`q`** in the video window at any time to cancel.

### 3. Inspect Database Contents
To verify that the records and face encodings were saved correctly, run:
```powershell
python view_db.py
```
- It prints a clean ASCII table of all registered students (without flooding the console with raw binary encoding BLOBs).
- It lists the last 20 access/registration log events.
