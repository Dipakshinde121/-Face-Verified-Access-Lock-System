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
        
        # Devices Table for Per-Device JWT Authentication (TRD & Schema Doc §2)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            device_label TEXT NOT NULL,
            device_secret TEXT NOT NULL,
            registered_date TEXT NOT NULL,
            last_seen TEXT,
            revoked INTEGER DEFAULT 0
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
        
        # Central hash-chained audit trail (Schema Doc §3)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT,
            device_id TEXT,
            event TEXT NOT NULL,
            severity TEXT NOT NULL,
            confidence_score REAL,
            timestamp TEXT NOT NULL,
            entry_hash TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            FOREIGN KEY (roll_number) REFERENCES students (roll_number)
        );
        """)
        
        # Dynamic migrations for devices table
        for col_name, col_type, default_val in [
            ("device_label", "TEXT", "'Lab-PC'"),
            ("last_seen", "TEXT", "NULL"),
            ("revoked", "INTEGER", "0")
        ]:
            try:
                cursor.execute(f"ALTER TABLE devices ADD COLUMN {col_name} {col_type} DEFAULT {default_val};")
            except sqlite3.OperationalError:
                pass

        # Dynamic migrations for logs table
        for col_name, col_type, default_val in [
            ("device_id", "TEXT", "NULL"),
            ("confidence_score", "REAL", "NULL"),
            ("previous_hash", "TEXT", f"'{GENESIS_HASH}'"),
            ("entry_hash", "TEXT", "NULL")
        ]:
            try:
                cursor.execute(f"ALTER TABLE logs ADD COLUMN {col_name} {col_type} DEFAULT {default_val};")
            except sqlite3.OperationalError:
                pass
            
        conn.commit()
    finally:
        conn.close()

def register_device_server(device_id: str, device_secret: str, device_label: str = "Lab-PC", db_path=DB_PATH):
    registered_date = datetime.now().isoformat()
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO devices (device_id, device_label, device_secret, registered_date, last_seen, revoked)
            VALUES (?, ?, ?, ?, ?, 0)
            """,
            (device_id, device_label, device_secret, registered_date, registered_date)
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
        cursor.execute("PRAGMA table_info(devices)")
        cols = [col[1] for col in cursor.fetchall()]
        revoked_col = "revoked" if "revoked" in cols else "is_revoked"
        label_col = "device_label" if "device_label" in cols else "'Lab-PC'"
        last_seen_col = "last_seen" if "last_seen" in cols else "NULL"
        
        cursor.execute(
            f"SELECT device_secret, {revoked_col}, {label_col}, {last_seen_col} FROM devices WHERE device_id = ?",
            (device_id,)
        )
        row = cursor.fetchone()
        if row:
            return {
                "device_secret": row[0],
                "is_revoked": bool(row[1]),
                "revoked": int(row[1] or 0),
                "device_label": row[2],
                "last_seen": row[3]
            }
        return None
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to fetch device {device_id}: {e}")
        return None
    finally:
        conn.close()

def update_device_last_seen(device_id: str, db_path=DB_PATH):
    now_iso = datetime.now().isoformat()
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE devices SET last_seen = ? WHERE device_id = ?", (now_iso, device_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to update last_seen for {device_id}: {e}")
        return False
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

def log_event_server(roll_number: str = None, event: str = "", severity: str = "INFO", 
                     confidence_score: float = None, device_id: str = None, db_path=DB_PATH):
    timestamp = datetime.now().isoformat()
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # 1. Fetch the previous entry's hash to chain them together
        cursor.execute("SELECT entry_hash FROM logs ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        prev_hash = row[0] if (row and row[0]) else GENESIS_HASH
        
        # 2. Compute the new cryptographic hash over the payload + previous hash
        conf_str = f"{float(confidence_score):.2f}" if confidence_score is not None else ""
        payload = f"{timestamp}|{roll_number or ''}|{device_id or ''}|{event}|{severity}|{conf_str}|{prev_hash}"
        entry_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        
        # 3. Store the log entry securely with previous_hash and confidence_score
        cursor.execute(
            """
            INSERT INTO logs (roll_number, device_id, event, severity, confidence_score, timestamp, entry_hash, previous_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (roll_number, device_id, event, severity, confidence_score, timestamp, entry_hash, prev_hash)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to log event for {roll_number}: {e}")
        return False
    finally:
        conn.close()

def get_logs_server(limit: int = 100, db_path=DB_PATH):
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, roll_number, device_id, event, severity, confidence_score, timestamp, entry_hash, previous_hash 
            FROM logs ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        )
        rows = cursor.fetchall()
        logs = []
        for r in rows:
            logs.append({
                "id": r[0],
                "roll_number": r[1],
                "device_id": r[2],
                "event": r[3],
                "severity": r[4],
                "confidence_score": r[5],
                "timestamp": r[6],
                "entry_hash": r[7],
                "previous_hash": r[8]
            })
        return logs
    except sqlite3.Error as e:
        print(f"[Server DB Error] Failed to fetch logs: {e}")
        return []
    finally:
        conn.close()
