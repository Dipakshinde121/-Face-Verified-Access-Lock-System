import sqlite3
import os

DB_PATH = "access_control.db"

def print_table(headers, rows):
    if not rows:
        print("   (No data found)")
        return
    widths = [max(len(str(val)) for val in col) for col in zip(headers, *rows)]
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    fmt = lambda row: "|" + "|".join(f" {str(val):<{widths[i]}} " for i, val in enumerate(row)) + "|"
    print(f"{sep}\n{fmt(headers)}\n{sep}")
    for r in rows:
        print(fmt(r))
    print(sep)

def main():
    print(f"=== Database Inspector ({DB_PATH}) ===")
    
    if not os.path.exists(DB_PATH):
        print(f"[Warning] Database file '{DB_PATH}' does not exist yet. Please run registration or database init first.")
        return
        
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Inspect registered students
        print("\n--- Registered Students ---")
        # Query roll_number, name, registered_date, and size of the face_encoding blob in bytes
        cursor.execute("SELECT roll_number, name, LENGTH(face_encoding), registered_date FROM students")
        students = cursor.fetchall()
        
        headers_students = ["Roll Number", "Full Name", "Encoding Blob Size (Bytes)", "Registered Date"]
        print_table(headers_students, students)
        print(f"Total registered students: {len(students)}")
        
        # 2. Inspect logs
        print("\n--- Event Logs ---")
        cursor.execute("SELECT id, roll_number, event, timestamp FROM logs ORDER BY id DESC LIMIT 20")
        logs = cursor.fetchall()
        
        headers_logs = ["Log ID", "Roll Number", "Event Details", "Timestamp"]
        print_table(headers_logs, logs)
        print(f"Showing last {len(logs)} log events.")
        
    except sqlite3.Error as e:
        print(f"[Error] Failed to read database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()
