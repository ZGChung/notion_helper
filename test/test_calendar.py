"""Test Calendar.app access."""

import subprocess
from datetime import datetime, timedelta

def run_applescript(script: str) -> str:
    """Run AppleScript and return its output."""
    try:
        process = subprocess.Popen(
            ['osascript', '-e', script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print(f"AppleScript error: {stderr}")
            return ""
            
        return stdout.strip()
        
    except Exception as e:
        print(f"Error running AppleScript: {e}")
        return ""

def main():
    print("\nTesting Calendar.app access...")
    
    # Test 1: List calendars
    print("\nTest 1: List calendars")
    script1 = """
        tell application "Calendar"
            set calNames to {}
            repeat with cal in calendars
                copy (name of cal) to the end of calNames
            end repeat
            return calNames
        end tell
    """
    result1 = run_applescript(script1)
    print(f"Result: {result1}")
    
    # Test 2: Get events from a specific calendar
    print("\nTest 2: Get events from Calendar")
    script2 = """
        tell application "Calendar"
            set targetCalName to "Calendar"
            set targetCal to first calendar whose name is targetCalName
            
            set startDate to current date
            set endDate to startDate + (7 * days)
            
            set eventList to {}
            set theEvents to (every event of targetCal whose start date ≥ startDate and start date ≤ endDate)
            
            repeat with evt in theEvents
                set eventInfo to {summary of evt, start date of evt}
                copy eventInfo to the end of eventList
            end repeat
            
            return eventList
        end tell
    """
    result2 = run_applescript(script2)
    print(f"Result: {result2}")
    
    # Test 3: Get events from all calendars
    print("\nTest 3: Get events from all calendars")
    script3 = """
        tell application "Calendar"
            set startDate to current date
            set endDate to startDate + (7 * days)
            set allEvents to {}
            
            repeat with cal in calendars
                set calName to name of cal
                set theEvents to (every event of cal whose start date ≥ startDate and start date ≤ endDate)
                
                repeat with evt in theEvents
                    set eventInfo to {calName, summary of evt}
                    copy eventInfo to the end of allEvents
                end repeat
            end repeat
            
            return allEvents
        end tell
    """
    result3 = run_applescript(script3)
    print(f"Result: {result3}")

if __name__ == "__main__":
    main()