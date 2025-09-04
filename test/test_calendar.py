"""Test Calendar.app access."""

import subprocess

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
    
    # Test 1: Basic Calendar.app access
    print("\nTest 1: Basic Calendar.app access")
    script1 = """
        tell application "Calendar"
            return name of calendars
        end tell
    """
    result1 = run_applescript(script1)
    print(f"Result: {result1}")
    
    # Test 2: Get calendar details
    print("\nTest 2: Get calendar details")
    script2 = """
        tell application "Calendar"
            set output to ""
            repeat with cal in calendars
                set output to output & "Calendar: " & name of cal & ", Color: " & color of cal & ", Enabled: " & enabled of cal & linefeed
            end repeat
            return output
        end tell
    """
    result2 = run_applescript(script2)
    print(f"Result: {result2}")
    
    # Test 3: Get today's events
    print("\nTest 3: Get today's events")
    script3 = """
        tell application "Calendar"
            set output to ""
            set today_start to (current date) - (time of (current date))
            set today_end to today_start + 1 * days
            repeat with cal in calendars
                set output to output & "Calendar: " & name of cal & linefeed
                set today_events to (every event of cal whose start date ≥ today_start and start date ≤ today_end)
                repeat with evt in today_events
                    set output to output & "  - " & summary of evt & " at " & (time string of (start date of evt)) & linefeed
                end repeat
            end repeat
            return output
        end tell
    """
    result3 = run_applescript(script3)
    print(f"Result: {result3}")

if __name__ == "__main__":
    main()
