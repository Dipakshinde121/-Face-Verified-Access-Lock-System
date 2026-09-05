import sqlite3
import argparse
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "access_control.db")

# Dictionary mapping raw technical events to Plain-English descriptions for the dashboard
EVENT_DESCRIPTIONS = {
    "LOGIN": "User initiated session",
    "LOGOUT": "User ended session manually",
    "LOGOUT_OR_LOCK": "Session terminated (manual or auto-lock)",
    "REGISTRATION_SUCCESS": "New student registered biometrics",
    "PERIODIC_CHECK_SUCCESS": "Continuous verification passed (High Conf)",
    "PERIODIC_CHECK_MATCH_LOW_CONFIDENCE": "Continuous verification passed (Medium Conf - Borderline)",
    "LOCK_NO_FACE_TIMEOUT": "User absent - Grace period expired (Auto-Locked)",
    "LOCK_FACE_MISMATCH": "Unrecognized face detected (Impersonation attempt - Auto-Locked)",
    "PERIODIC_CHECK_ERROR_CAMERA": "Failed to access webcam during check",
    "PERIODIC_CHECK_ERROR_FRAME": "Failed to read frame from webcam",
    "POLICY_OVERRIDE": "User explicitly paused security monitoring",
    "POLICY_RESUMED": "User manually resumed security monitoring",
    "AUTO_RESUME_FAILSAFE": "Max pause duration exceeded - Auto-resumed monitoring",
    "LOGIN_DENIED_LIVENESS_FAIL": "Login denied - Failed liveness check (Spoofing attempt)",
    "LOGIN_DENIED_INVALID_TOTP": "Login denied - Invalid MFA TOTP code",
    "LOGIN_FACE_MATCH_HIGH_CONF": "Login face verified (High Conf)",
    "LOGIN_FACE_MATCH_MED_CONF": "Login face verified (Medium Conf - Borderline)",
    "LOGIN_DENIED_FACE_MISMATCH": "Login denied - Unrecognized face",
    "LOGIN_DENIED_NO_FACE": "Login denied - No face detected"
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

def verify_log_integrity(conn):
    import hashlib
    print("\n[SECURITY AUDIT] Initiating Tamper-Evident Hash Chain Verification...")
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, roll_number, event, severity, entry_hash FROM logs ORDER BY id ASC")
        rows = cursor.fetchall()
        
        if not rows:
            print("[Info] The logs database is currently empty.")
            return

        prev_hash = GENESIS_HASH
        for row in rows:
            log_id, timestamp, roll_number, event, severity, stored_hash = row
            
            # Recompute what the hash SHOULD be
            payload = f"{timestamp}|{roll_number}|{event}|{severity}|{prev_hash}"
            expected_hash = hashlib.sha256(payload.encode('utf-8')).hexdigest()
            
            if expected_hash != stored_hash:
                print("\n" + "="*60)
                print("🚨 CRITICAL SECURITY ALERT: LOG TAMPERING DETECTED! 🚨")
                print("="*60)
                print(f"Chain broken at Log ID: {log_id}")
                print(f"Timestamp of Tampered Entry: {timestamp}")
                print(f"Event: {event}")
                print(f"\nExpected Hash : {expected_hash}")
                print(f"Stored Hash   : {stored_hash}")
                print("="*60)
                print("[!] All subsequent logs in this chain are mathematically invalidated.")
                return
                
            prev_hash = expected_hash
            
        print(f"\n✅ SUCCESS: Cryptographic Chain Verified!")
        print(f"Analyzed {len(rows)} sequential entries.")
        print("No tampering detected. The audit trail is fully intact.")
        
    except sqlite3.OperationalError as e:
        if "no such column: entry_hash" in str(e).lower():
            print("\n[Error] The 'entry_hash' column does not exist. Run login.py to trigger database migration.")
        else:
            print(f"[Error] Database failure: {e}")

def main():
    parser = argparse.ArgumentParser(description="Security Monitoring Dashboard - Log Viewer")
    parser.add_argument("--roll", type=str, help="Filter by Roll Number")
    parser.add_argument("--severity", type=str, choices=['INFO', 'LOW', 'MEDIUM', 'HIGH'], help="Filter by Threat Severity")
    parser.add_argument("--limit", type=int, default=20, help="Number of latest logs to display")
    parser.add_argument("--verify-integrity", action="store_true", help="Verify the cryptographic hash chain of the audit logs")
    
    args = parser.parse_args()
    
    if not os.path.exists(DB_PATH):
        print(f"[Error] Database {DB_PATH} not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        if args.verify_integrity:
            verify_log_integrity(conn)
            return
            
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
        import re
        
        for timestamp, roll_number, event_raw, severity in raw_logs:
            # Clean up timestamp for display (e.g. 2026-08-21 00:05:00)
            display_time = timestamp.replace("T", " ")[:19]
            
            # Extract confidence score if present
            conf_match = re.search(r'\(Conf:\s*([\d.]+)\)', event_raw)
            base_event = re.sub(r'\s*\(Conf:\s*[\d.]+\)', '', event_raw)
            
            # Map raw event to English description
            desc = EVENT_DESCRIPTIONS.get(base_event)
            if not desc:
                # Handle dynamic strings
                if "PERIODIC_CHECK_NO_FACE" in base_event:
                    desc = "User absent from camera frame"
                else:
                    desc = base_event
                    
            if conf_match:
                desc += f" (Score: {conf_match.group(1)})"
                    
            formatted_rows.append((display_time, roll_number, severity, event_raw, desc))
            
        print("\n=== SECURITY MONITORING DASHBOARD ===")
        print(f"Filters Active: Roll={args.roll or 'ALL'}, Severity={args.severity or 'ALL'}")
        
        headers = ["Timestamp", "Roll Number", "Severity", "Raw Event Code", "Description"]
        print_table(headers, formatted_rows)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
