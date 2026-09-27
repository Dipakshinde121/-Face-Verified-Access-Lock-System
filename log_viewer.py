import sqlite3
import argparse
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Check central server database path first, then fallback to local
SERVER_DB_PATH = os.path.join(BASE_DIR, "server", "central_access_control.db")
LOCAL_DB_PATH = os.path.join(BASE_DIR, "access_control.db")
DB_PATH = SERVER_DB_PATH if os.path.exists(SERVER_DB_PATH) else LOCAL_DB_PATH

# Dictionary mapping raw technical events to Plain-English descriptions (Schema Doc §4)
EVENT_DESCRIPTIONS = {
    "LOGIN": "Successful 3-factor login",
    "LOGOUT": "User ended session manually",
    "LOGOUT_OR_LOCK": "Session terminated (manual or auto-lock)",
    "REGISTRATION_SUCCESS": "New student registered biometrics",
    "MATCH": "Continuous verification passed (High Conf)",
    "MATCH_LOW_CONFIDENCE": "Continuous verification passed (Medium Conf - Borderline)",
    "LOCK_NO_FACE_TIMEOUT": "User absent - Grace period expired (Auto-Locked)",
    "LOCK_FACE_MISMATCH": "Unrecognized face detected (Impersonation attempt - Auto-Locked)",
    "PERIODIC_CHECK_ERROR_CAMERA": "Failed to access webcam during check",
    "PERIODIC_CHECK_ERROR_FRAME": "Failed to read frame from webcam",
    "POLICY_OVERRIDE_PAUSE": "Admin paused monitoring (auto-expires)",
    "POLICY_OVERRIDE": "Admin paused monitoring (auto-expires)",
    "POLICY_RESUMED": "Security monitoring resumed",
    "AUTO_RESUME_FAILSAFE": "Max pause duration exceeded - Auto-resumed monitoring",
    "LOGIN_DENIED_LIVENESS_FAIL": "Login denied - Failed liveness challenge (Spoofing attempt)",
    "LOGIN_DENIED_INVALID_TOTP": "Login denied - Invalid MFA TOTP code",
    "LOGIN_DENIED_FACE_MISMATCH": "Login denied - Unrecognized face",
    "LOGIN_DENIED_NO_FACE": "Login denied - No face detected",
    "LOGIN_DENIED_MULTIPLE_FACES": "Login denied - Multiple faces detected (Piggybacking attempt)",
    "LOCK_MULTIPLE_FACES": "Piggybacking detected - Multiple faces in frame (Auto-Locked)",
    "API_AUTH_FAILED_INVALID_TOKEN": "Rejected API call - Expired/tampered JWT",
    "API_AUTH_FAILED_REVOKED_DEVICE": "Rejected API call - Revoked Lab PC",
    "TAMPER_DETECTED": "Corrupted/tampered encrypted data detected on decrypt"
}

def print_table(headers, rows):
    """Prints a formatted ASCII table."""
    if not rows:
        print("   (No data found matching criteria)")
        return
    widths = [max(len(str(val)) for val in col) for col in zip(headers, *rows)]
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    fmt = lambda row: "|" + "|".join(f" {str(val):<{widths[i]}} " for i, val in enumerate(row)) + "|"
    print(f"{sep}\n{fmt(headers)}\n{sep}")
    for r in rows:
        print(fmt(r))
    print(sep)

def verify_log_integrity(conn):
    import hashlib
    print("\n[SECURITY AUDIT] Initiating Tamper-Evident Hash Chain Verification...")
    GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, timestamp, roll_number, device_id, event, severity, confidence_score, entry_hash, previous_hash
            FROM logs ORDER BY id ASC
        """)
        rows = cursor.fetchall()
        
        if not rows:
            print("[Info] The logs database is currently empty.")
            return

        prev_hash = GENESIS_HASH
        for row in rows:
            log_id, timestamp, roll_number, device_id, event, severity, confidence_score, stored_hash, stored_prev_hash = row
            
            # 1. Verify previous_hash link if column is stored
            if stored_prev_hash and stored_prev_hash != prev_hash:
                print("\n" + "="*60)
                print("[!] CRITICAL SECURITY ALERT: HASH CHAIN LINK BROKEN!")
                print("="*60)
                print(f"Broken at Log ID: {log_id}")
                print(f"Timestamp: {timestamp} | Event: {event}")
                print(f"Expected Previous Hash: {prev_hash}")
                print(f"Stored Previous Hash  : {stored_prev_hash}")
                print("="*60)
                return

            if not stored_hash:
                print("\n" + "="*60)
                print("[!] INTEGRITY CHECK: UNHASHED LEGACY LOG ENTRY DETECTED")
                print("="*60)
                print(f"Log ID: {log_id} | Timestamp: {timestamp} | Event: {event}")
                print("Explanation: This entry was recorded before hash-chaining was enabled (Day 19).")
                print("Per Schema Document Section 7: Rebuild the database from empty for a pristine chain.")
                print("="*60)
                return

            # 2. Recompute expected hash
            conf_str = f"{float(confidence_score):.2f}" if confidence_score is not None else ""
            payload_new = f"{timestamp}|{roll_number or ''}|{device_id or ''}|{event}|{severity}|{conf_str}|{prev_hash}"
            expected_hash = hashlib.sha256(payload_new.encode('utf-8')).hexdigest()
            
            if expected_hash != stored_hash:
                # Support legacy payload fallback for entries logged before schema upgrade
                payload_legacy = f"{timestamp}|{roll_number}|{event}|{severity}|{prev_hash}"
                expected_legacy = hashlib.sha256(payload_legacy.encode('utf-8')).hexdigest()
                if expected_legacy == stored_hash:
                    expected_hash = expected_legacy
                else:
                    print("\n" + "="*60)
                    print("[!] CRITICAL SECURITY ALERT: LOG TAMPERING DETECTED!")
                    print("="*60)
                    print(f"Chain broken at Log ID: {log_id}")
                    print(f"Timestamp of Tampered Entry: {timestamp}")
                    print(f"Event: {event}")
                    print(f"\nExpected Hash : {expected_hash}")
                    print(f"Stored Hash   : {stored_hash}")
                    print("="*60)
                    print("[!] All subsequent logs in this chain are mathematically invalidated.")
                    return
                
            prev_hash = stored_hash
            
        print(f"\n[+] SUCCESS: Cryptographic Chain Verified!")
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
    parser.add_argument("--device", type=str, help="Filter by Device ID")
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
        conditions, params = [], []
        if args.roll:
            conditions.append("roll_number = ?")
            params.append(args.roll)
        if args.device:
            conditions.append("device_id = ?")
            params.append(args.device)
        if args.severity:
            conditions.append("severity = ?")
            params.append(args.severity)
            
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT timestamp, roll_number, device_id, severity, confidence_score, event FROM logs{where} ORDER BY id DESC LIMIT ?"
        params.append(args.limit)
        
        cursor.execute(query, params)
        raw_logs = cursor.fetchall()

        # Format rows
        formatted_rows = []
        import re
        
        for timestamp, roll_number, device_id, severity, confidence_score, event_raw in raw_logs:
            display_time = timestamp.replace("T", " ")[:19]
            
            # Confidence display
            if confidence_score is not None:
                conf_display = f"{float(confidence_score):.2f}"
            else:
                conf_match = re.search(r'\(Conf:\s*([\d.]+)\)', event_raw)
                conf_display = conf_match.group(1) if conf_match else "-"
            
            # Strip inline score from event code if present
            base_event = re.sub(r'\s*\(Conf:\s*[\d.]+\)', '', event_raw)
            desc = EVENT_DESCRIPTIONS.get(base_event, base_event)
            
            formatted_rows.append((
                display_time, 
                roll_number or "SYSTEM", 
                device_id or "Local", 
                severity, 
                conf_display, 
                base_event, 
                desc
            ))
            
        print("\n=== SECURITY MONITORING DASHBOARD ===")
        print(f"Database: {DB_PATH}")
        print(f"Filters Active: Roll={args.roll or 'ALL'}, Device={args.device or 'ALL'}, Severity={args.severity or 'ALL'}")
        
        headers = ["Timestamp", "Roll", "Device ID", "Severity", "Conf", "Event Code", "Description"]
        print_table(headers, formatted_rows)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
