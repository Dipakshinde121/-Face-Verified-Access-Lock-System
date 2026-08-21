import sqlite3
import argparse
import os

DB_PATH = "access_control.db"

# Dictionary mapping raw technical events to Plain-English descriptions for the dashboard
EVENT_DESCRIPTIONS = {
    "LOGIN": "User initiated session",
    "LOGOUT": "User ended session manually",
    "LOGOUT_OR_LOCK": "Session terminated (manual or auto-lock)",
    "REGISTRATION_SUCCESS": "New student registered biometrics",
    "PERIODIC_CHECK_SUCCESS": "Continuous verification passed",
    "LOCK_NO_FACE_TIMEOUT": "User absent - Grace period expired (Auto-Locked)",
    "LOCK_FACE_MISMATCH": "Unrecognized face detected (Impersonation attempt - Auto-Locked)",
    "PERIODIC_CHECK_ERROR_CAMERA": "Failed to access webcam during check",
    "PERIODIC_CHECK_ERROR_FRAME": "Failed to read frame from webcam",
    "POLICY_OVERRIDE": "User explicitly paused security monitoring",
    "POLICY_RESUMED": "User manually resumed security monitoring",
    "AUTO_RESUME_FAILSAFE": "Max pause duration exceeded - Auto-resumed monitoring"
}

def print_table(headers, rows):
    """Prints a beautifully formatted ASCII table."""
    if not rows:
        print("   (No data found matching criteria)")
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
    parser = argparse.ArgumentParser(description="Security Monitoring Dashboard - Log Viewer")
    parser.add_argument("--roll", type=str, help="Filter by Roll Number")
    parser.add_argument("--severity", type=str, choices=['INFO', 'LOW', 'MEDIUM', 'HIGH'], help="Filter by Threat Severity")
    parser.add_argument("--limit", type=int, default=20, help="Number of latest logs to display")
    
    args = parser.parse_args()
    
    if not os.path.exists(DB_PATH):
        print(f"[Error] Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        
        query = "SELECT timestamp, roll_number, event, severity FROM logs"
        params = []
        conditions = []
        
        if args.roll:
            conditions.append("roll_number = ?")
            params.append(args.roll)
        if args.severity:
            conditions.append("severity = ?")
            params.append(args.severity)
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY id DESC LIMIT ?"
        params.append(args.limit)
        
        # Check if severity column exists (in case migration didn't run)
        try:
            cursor.execute(query, params)
            raw_logs = cursor.fetchall()
        except sqlite3.OperationalError:
            print("[Notice] Database migration for 'severity' pending. Run python login.py or database.py once to trigger migration.")
            query = query.replace(", severity", "")
            if args.severity:
                print("[Error] Cannot filter by severity before migration runs.")
                return
            cursor.execute(query, params)
            raw_logs = cursor.fetchall()
            raw_logs = [(t, r, e, "N/A") for t, r, e in raw_logs]

        # Format rows
        formatted_rows = []
        for timestamp, roll_number, event_raw, severity in raw_logs:
            # Clean up timestamp for display (e.g. 2026-08-21 00:05:00)
            display_time = timestamp.replace("T", " ")[:19]
            
            # Map raw event to English description
            desc = EVENT_DESCRIPTIONS.get(event_raw)
            if not desc:
                # Handle dynamic strings
                if "PERIODIC_CHECK_NO_FACE" in event_raw:
                    desc = "User absent from camera frame"
                else:
                    desc = event_raw
                    
            formatted_rows.append((display_time, roll_number, severity, event_raw, desc))
            
        print("\n=== SECURITY MONITORING DASHBOARD ===")
        print(f"Filters Active: Roll={args.roll or 'ALL'}, Severity={args.severity or 'ALL'}")
        
        headers = ["Timestamp", "Roll Number", "Severity", "Raw Event Code", "Description"]
        print_table(headers, formatted_rows)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
