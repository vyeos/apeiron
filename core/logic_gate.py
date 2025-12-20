from z3 import *
import json
import re


def sanitize_json_input(json_str):
    """
    Fixes common LLM JSON mistakes before parsing.
    1. Removes leading zeros from integers (e.g., 0900 -> 900).
    """
    # Regex to find numbers with leading zeros (that aren't just "0")
    # Matches a digit 0, followed by other digits, that isn't inside quotes
    json_str = re.sub(r'(?<!")\b0+(\d+)', r"\1", json_str)
    return json_str


def validate_schedule_logic(json_plan):
    """
    Uses Z3 Theorem Prover to verify if a proposed schedule is logically possible.
    Constraint: End Time must be strictly greater than Start Time.
    """
    try:
        # 1. Sanitize (Fix the leading zero bug)
        clean_json = sanitize_json_input(json_plan)

        # 2. Parse
        data = json.loads(clean_json)

        # 3. Initialize the Solver
        s = Solver()

        # 4. Define Variables (Symbolic Integers)
        start = Int("start_time")
        end = Int("end_time")

        # 5. Add Constraints (The "Laws")
        # Law A: The plan's values must match the variables
        s.add(start == data["start_time"])
        s.add(end == data["end_time"])

        # Law B: Logic Constraints (Time flows forward)
        s.add(end > start)

        # Law C: Valid 24h clock
        s.add(start >= 0, start <= 2400)
        s.add(end >= 0, end <= 2400)

        # 6. Prove it
        result = s.check()

        if result == sat:
            return True, "Logic Validated: Plan is physically possible."
        else:
            return False, "Logic Violation: Time paradox detected (End <= Start)."

    except Exception as e:
        return False, f"Syntax Error: {str(e)}"


# --- TEST HARNESS ---
if __name__ == "__main__":
    # Test a bad plan (Logically impossible)
    bad_logic = '{"task": "Deploy", "start_time": 1800, "end_time": 900}'
    print(f"Testing Paradox Plan: {validate_schedule_logic(bad_logic)}")
    # Test a bad format (Leading zeros - mimicking the error you saw)
    bad_format = '{"task": "Wake", "start_time": 0800, "end_time": 0900}'
    # Our new sanitize function should fix this automatically now
    print(f"Testing Leading Zero Plan: {validate_schedule_logic(bad_format)}")

    # Test a good plan
    good_plan = '{"task": "Work", "start_time": 900, "end_time": 1700}'
    print(f"Testing Good Plan: {validate_schedule_logic(good_plan)}`")
