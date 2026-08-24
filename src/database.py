import sqlite3
import pickle
# pyrefly: ignore [missing-import]
import numpy as np
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "access_control.db")

def get_db_connection(db_path=DB_PATH):
    """
    Establishes and returns a database connection.
    Enables foreign keys in SQLite.
    """
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=DB_PATH):
    """
    Initializes the SQLite database schema if tables do not exist.
    Applies schema migrations for older versions.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        
        # Create students table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            roll_number TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            face_encoding BLOB NOT NULL,
            registered_date TEXT NOT NULL
        );
        """)
        
        # Create logs table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT NOT NULL,
            event TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (roll_number) REFERENCES students (roll_number)
        );
        """)
        
        # Migration: Add severity column if it doesn't exist (for older DBs)
        try:
            cursor.execute("ALTER TABLE logs ADD COLUMN severity TEXT DEFAULT 'INFO';")
        except sqlite3.OperationalError:
            # Column already exists, safe to ignore
            pass
        
        conn.commit()
    finally:
        conn.close()

def add_student(roll_number, name, face_encoding, db_path=DB_PATH):
    """
    Registers or updates a student in the database.
    
    Parameters:
        roll_number (str): The student's unique roll number.
        name (str): The student's name.
        face_encoding (numpy.ndarray): The 128-dimensional face encoding vector.
        db_path (str): Path to the database file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    # Serialize numpy array to bytes
    serialized_encoding = pickle.dumps(face_encoding)
    
    # ENCRYPT-THEN-STORE: Encrypt the biometric PII before it hits the disk
    import crypto_utils
    encrypted_encoding = crypto_utils.encrypt_data(serialized_encoding)
    
    registered_date = datetime.now().isoformat()
    
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO students (roll_number, name, face_encoding, registered_date)
            VALUES (?, ?, ?, ?)
            """,
            (roll_number, name, encrypted_encoding, registered_date)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB Error] Failed to add student {roll_number}: {e}")
        return False
    finally:
        conn.close()

def get_face_by_roll(roll_number, db_path=DB_PATH):
    """
    Fetches a student's face encoding by their roll number.
    
    DESIGN NOTE: This function is completely self-contained. If we scale to a
    multi-PC lab environment in the future, we can swap the SQLite database query
    within this function for a REST API call (e.g., using 'requests' to a central server)
    without modifying the rest of the application.
    
    Parameters:
        roll_number (str): The student's unique roll number.
        db_path (str): Path to the database file.
        
    Returns:
        numpy.ndarray: The 128-dimensional face encoding vector, or None if not found/error.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT face_encoding FROM students WHERE roll_number = ?", (roll_number,))
        row = cursor.fetchone()
        if row:
            encrypted_encoding = row[0]
            
            # DECRYPT-IN-MEMORY: Decrypt the cipher back to bytes only in RAM
            import crypto_utils
            serialized_encoding = crypto_utils.decrypt_data(encrypted_encoding)
            
            face_encoding = pickle.loads(serialized_encoding)
            return face_encoding
        return None
    except sqlite3.Error as e:
        print(f"[DB Error] Failed to fetch encoding for roll {roll_number}: {e}")
        return None
    finally:
        conn.close()

def get_student_by_roll(roll_number, db_path=DB_PATH):
    """
    Fetches student details (name, registered_date) by roll number.
    
    Parameters:
        roll_number (str): The student's unique roll number.
        db_path (str): Path to the database file.
        
    Returns:
        dict: A dictionary containing 'name' and 'registered_date', or None if not found.
    """
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT name, registered_date FROM students WHERE roll_number = ?", (roll_number,))
        row = cursor.fetchone()
        if row:
            return {"name": row[0], "registered_date": row[1]}
        return None
    except sqlite3.Error as e:
        print(f"[DB Error] Failed to fetch student details for {roll_number}: {e}")
        return None
    finally:
        conn.close()

def log_event(roll_number, event, severity="INFO", db_path=DB_PATH):
    """
    Logs an access control or authentication event for a student.
    
    Parameters:
        roll_number (str): The student's roll number.
        event (str): The details of the event (e.g. 'ACCESS_GRANTED', 'ACCESS_DENIED').
        severity (str): Threat severity level ('INFO', 'LOW', 'MEDIUM', 'HIGH'). Default 'INFO'.
        db_path (str): Path to the database file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    timestamp = datetime.now().isoformat()
    conn = get_db_connection(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs (roll_number, event, timestamp, severity) VALUES (?, ?, ?, ?)",
            (roll_number, event, timestamp, severity)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"[DB Error] Failed to log event for {roll_number}: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    import os
    print("=== Running database.py Self-Test ===")
    test_db = "test_access_control.db"
    
    # Reset any previous test DB
    if os.path.exists(test_db):
        os.remove(test_db)
        
    try:
        print("1. Initializing DB...")
        init_db(test_db)
        
        print("2. Creating dummy face encoding (128-element random float)...")
        dummy_encoding = np.random.randn(128)
        
        print("3. Inserting student '21BCE001' (John Doe)...")
        added = add_student("21BCE001", "John Doe", dummy_encoding, db_path=test_db)
        print(f"   Result: {'Success' if added else 'Failed'}")
        
        print("4. Retrieving face encoding for '21BCE001'...")
        retrieved_encoding = get_face_by_roll("21BCE001", db_path=test_db)
        if retrieved_encoding is not None:
            print(f"   Success! Shape: {retrieved_encoding.shape}")
            match = np.allclose(dummy_encoding, retrieved_encoding)
            print(f"   Does retrieved encoding match the inserted one? {match}")
        else:
            print("   Failed to retrieve encoding.")
            
        print("5. Logging access event...")
        logged = log_event("21BCE001", "ACCESS_GRANTED_BY_FACE", db_path=test_db)
        print(f"   Result: {'Success' if logged else 'Failed'}")
        
    finally:
        if os.path.exists(test_db):
            os.remove(test_db)
            print("6. Cleaned up test database.")
            
    print("=== Self-Test Finished ===")
