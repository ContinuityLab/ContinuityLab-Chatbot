import sys

# THE LIBRARY
SIMULATED_DB = {
    "survey-001": {"Name": "AWS Backup", "Impact": "High", "RACI": "Eddy Mangrove"},
    "survey-002": {"Name": "Cloud Storage", "Impact": "Medium", "RACI": "Compliance Manager"}
}

def main(survey_id="survey-001"):
    current_node = 1
    # We do NOT load the data yet. The data is locked in a box.
    
    print(f"\n=== MANGROVE SYSTEM START ===")

    while current_node != 0:
        if current_node == 1:
            print("\n[STATION 1: INTENT GATE]")
            # The code stops here. It will not look at Azure or the DB yet.
            ans = input("CONFIRM: Do you want to address this redundancy? (yes/no): ").strip().lower()
            if ans == "yes":
                current_node = 2
            else:
                print("Closing session.")
                current_node = 0

        elif current_node == 2:
            print("\n[STATION 2: WORKFLOW GATE]")
            ans = input("CONFIRM: Is this connected to an active workflow? (yes/no): ").strip().lower()
            if ans == "no":
                current_node = 3  # Only now do we unlock the data
            else:
                print("Flagged as connected. System Exit.")
                current_node = 0

        elif current_node == 3:
            print("\n[STATION 3: THE DATA UNLOCK]")
            # THE MOMENT OF TRUTH: We only fetch now.
            data = SIMULATED_DB.get(survey_id)
            print(f"FETCHING IDENTITY CARD FOR: {survey_id}")
            print(f"--- DATA UNLOCKED ---")
            print(f"Resource: {data['Name']}")
            print(f"Impact: {data['Impact']}")
            print(f"Owner: {data['RACI']}")
            
            ans = input("\nData retrieved. Is this the correct record to review? (yes/no): ").strip().lower()
            current_node = 4 if ans == "yes" else 0

        elif current_node == 4:
            print(f"\n[STATION 4: FINAL ACTION]")
            print("Action required: (A) Monitor (B) Resolve")
            ans = input("Select A or B: ").strip().upper()
            print(f"Action '{ans}' has been logged to the dashboard.")
            current_node = 0

    print("\n=== TRACK ENDED ===")

if __name__ == "__main__":
    # If you want to test survey-002, change this to "survey-002"
    main("survey-001")
