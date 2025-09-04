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
    
    # Test 1: List calendars (simpler syntax)
    print("\nTest 1: List calendars")
    script1 = """
        tell application "Calendar"
            set output to ""
            repeat with cal in calendars
                set output to output & name of cal & linefeed
            end repeat
            return output
        end tell
    """
    result1 = run_applescript(script1)
    print(f"Result:\n{result1}")
    
    # Test 2: Get events from Calendar (simpler syntax)
    print("\nTest 2: Get events from Calendar")
    script2 = """
        tell application "Calendar"
            set output to ""
            set cal to first calendar whose name is "Calendar"
            set today_start to (current date) - (time of (current date))
            set today_end to today_start + 7 * days
            
            repeat with evt in (every event of cal whose start date ≥ today_start and start date ≤ today_end)
                set output to output & summary of evt & " at " & ((time string of (start date of evt)) as string) & linefeed
            end repeat
            
            return output
        end tell
    """
    result2 = run_applescript(script2)
    print(f"Result:\n{result2}")
    
    # Test 3: Get events from all selected calendars
    print("\nTest 3: Get events from selected calendars")
    selected_calendars = ["Calendar", "Personal", "Apple", "MD AI/ML COE", "Siri Suggestions"]
    script3 = """
        tell application "Calendar"
            set output to ""
            set today_start to (current date) - (time of (current date))
            set today_end to today_start + 7 * days
            
            repeat with cal_name in {""" + ", ".join(f'"{cal}"' for cal in selected_calendars) + """}
                try
                    set cal to first calendar whose name is cal_name
                    set output to output & "Calendar: " & cal_name & linefeed
                    
                    repeat with evt in (every event of cal whose start date ≥ today_start and start date ≤ today_end)
                        set output to output & "  - " & summary of evt & " at " & ((time string of (start date of evt)) as string) & linefeed
                    end repeat
                on error errMsg
                    set output to output & "Error accessing calendar " & cal_name & ": " & errMsg & linefeed
                end try
            end repeat
            
            return output
        end tell
    """
    result3 = run_applescript(script3)
    print(f"Result:\n{result3}")

if __name__ == "__main__":
    main()