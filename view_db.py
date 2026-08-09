import sqlite3
import os

DB_PATH = "access_control.db"

def print_table(headers, rows):
    """
    Helper function to print formatted ASCII tables.
    """
    if not rows:
        print("   (No data found)")
        return
        
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
            
    # Print separator
    sep = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
    print(sep)
    
    # Print headers
    header_str = "|" + "|".join([f" {headers[i]:<{widths[i]}} " for i in range(len(headers))]) + "|"
    print(header_str)
    print(sep)
    
    # Print rows
    for row in rows:
        row_str = "|" + "|".join([f" {str(row[i]):<{widths[i]}} " for i in range(len(row))]) + "|"
        print(row_str)
        
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
