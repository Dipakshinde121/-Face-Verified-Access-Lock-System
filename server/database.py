import sqlite3
import os
import hashlib
from datetime import datetime

# Centralized server database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "central_access_control.db")

# The fixed cryptographic anchor for the very first log entry
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def get_db_connection(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=DB_PATH):
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # New Devices Table for Per-Device JWT Authentication
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            device_secret TEXT NOT NULL,
            registered_date TEXT NOT NULL,
            is_revoked BOOLEAN NOT NULL DEFAULT 0
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll_number TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            face_encoding BLOB NOT NULL,
            totp_secret BLOB NOT NULL,
            registered_date TEXT NOT NULL
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT NOT NULL,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            severity TEXT DEFAULT 'INFO',
            entry_hash TEXT,
            FOREIGN KEY (roll_number) REFERENCES students (roll_number)
        );
        """)
        
        # Perform dynamic migration if the table exists but lacks the entry_hash column
        try:
            cursor.execute("ALTER TABLE logs ADD COLUMN entry_hash TEXT;")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        conn.commit()
    finally:
        conn.close()

def register_device_server(device_id: str, device_secret: str, db_path=DB_PATH):
    registered_date = datetime.now().isoformat()
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO devices (device_id, device_secret, registered_date, is_revoked)
            VALUES (?, ?, ?, 0)
            """,
            (device_id, device_secret, registered_date)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to register device {device_id}: {e}")
        return False
    finally:
        conn.close()

def get_device_server(device_id: str, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT device_secret, is_revoked FROM devices WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        if row:
            return {
                "device_secret": row[0],
                "is_revoked": bool(row[1])
            }
        return None
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to fetch device {device_id}: {e}")
        return None
    finally:
        conn.close()

def add_student_server(roll_number: str, name: str, encrypted_encoding: bytes, encrypted_totp: bytes, db_path=DB_PATH):
    registered_date = datetime.now().isoformat()
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO students (roll_number, name, face_encoding, totp_secret, registered_date)
            VALUES (?, ?, ?, ?, ?)
            """,
            (roll_number, name, encrypted_encoding, encrypted_totp, registered_date)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to add student {roll_number}: {e}")
        return False
    finally:
        conn.close()

def get_student_server(roll_number: str, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, face_encoding, totp_secret, registered_date FROM students WHERE roll_number = ?", (roll_number,))
        row = cursor.fetchone()
        if row:
            return {
                "name": row[0],
                "face_encoding": row[1],
                "totp_secret": row[2],
                "registered_date": row[3]
            }
        return None
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to fetch student {roll_number}: {e}")
        return None
    finally:
        conn.close()

def log_event_server(roll_number: str, event: str, severity: str = "INFO", db_path=DB_PATH):
    timestamp = datetime.now().isoformat()
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # 1. Fetch the previous entry's hash to chain them together
        cursor.execute("SELECT entry_hash FROM logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if (row and row[0]) else GENESIS_HASH
        
        # 2. Compute the new cryptographic hash over the payload + previous hash
        payload = f"{timestamp}|{roll_number}|{event}|{severity}|{prev_hash}"
        entry_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        
        # 3. Store the log entry securely
        cursor.execute(
            "INSERT INTO logs (roll_number, event, timestamp, severity, entry_hash) VALUES (?, ?, ?, ?, ?)",
            (roll_number, event, timestamp, severity, entry_hash)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to log event for {roll_number}: {e}")
        return False
    finally:
        conn.close()

def get_logs_server(db_path=DB_PATH):
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, roll_number, event, timestamp, severity FROM logs ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r[0],
                "roll_number": r[1],
                "event": r[2],
                "timestamp": r[3],
                "severity": r[4]
            })
        return logs
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to fetch logs: {e}")
        return []
    finally:
        conn.close()
