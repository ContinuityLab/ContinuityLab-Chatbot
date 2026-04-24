import sys

# --- THE DB ENGINE (Simulated real-time updates) ---
def update_database(survey_id, key, value, SIMULATED_DB):
    """Physically updates the library record."""
    if survey_id in SIMULATED_DB:
        SIMULATED_DB[survey_id][key] = value
        print(f"SYSTEM ACTION: Database Updated. {key} is now '{value}'.")

# --- THE SCORING ENGINE (Weighted Logic) ---
def calculate_resilience_score(d):
    score = 0
    time_map = {
        "Immediately": 20,
        "0-1 Hr": 20,
        "1-3 Hrs": 20,
        "3-6 Hrs": 10,
        "6-12 Hrs": 8,
        "12-18 Hrs": 6,
        "18-24 Hrs": 4,
    }
    score += time_map.get(d.get("Recovery_Time"), 0)
    if d.get("Country_Impact") == "Yes":
        score += 12
    if d.get("Company_Critical") == "Yes":
        score += 12
    if d.get("Customer_Time_Critical") == "Yes":
        score += 12
    if d.get("Customer_Data") == "Yes":
        score += 15
    if d.get("Employee_Data") == "Yes":
        score += 15
    if d.get("Proprietary_Info") == "Yes":
        score += 8
    if d.get("Financial_Data") == "Yes":
        score += 4
    if d.get("Backed_Up") == "Yes":
        score += 2
    return score

# --- THE LIBRARY ---
SIMULATED_DB = {
    "survey-001": {
        "Name": "AWS Multi-AZ Backup",
        "Recovery_Time": "3-6 Hrs",
        "Country_Impact": "Yes",
        "Company_Critical": "Yes",
        "Customer_Time_Critical": "Yes",
        "Customer_Data": "Yes",
        "Employee_Data": "Yes",
        "Proprietary_Info": "Yes",
        "Financial_Data": "Yes",
        "Backed_Up": "Yes",
        "RACI": {"Responsible": "Eddy Mangrove"},
        "Workflow": None,
    }
}

def main(survey_id="survey-001"):
    current_node = 1
    db = SIMULATED_DB  # Reference to our live data

    print(f"\n=== MANGROVE SYSTEM START ===")

    while current_node != 0:
        data = db.get(survey_id)
        score = calculate_resilience_score(data)

        # PHASE 1: IDENTIFICATION & CONNECTION
        if current_node == 1:
            ans = input("\nNode 1: 'Do you want to address this redundancy?' (Yes/No): ").strip().lower()
            current_node = 2 if "y" in ans else 0

        elif current_node == 2:
            ans = input("Node 2: 'Could we connect this redundancy to an active workflow?' (Yes/No): ").strip().lower()
            if "y" in ans:
                workflow_name = input("SYSTEM: What is the name of the active workflow? ").strip()
                update_database(survey_id, "Workflow", workflow_name, db)
                print(f"ACTION: {data['Name']} is now connected to {workflow_name}. Removing from analytics view.")
                current_node = 0
            else:
                choice = input("User Choice: (A) Monitor or (B) Proceed to Review: ").strip().upper()
                current_node = 5 if choice == "A" else 3

        # PHASE 2: VALIDATION (WITH UPDATE LOGIC)
        elif current_node == 3:
            print(f"\nNode 3: DATA REVIEW (Current Score: {score}/100)")
            print(f"Impact: Country({data['Country_Impact']}), Company({data['Company_Critical']})")
            ans = input("Prompt: 'Is this information correct?' (Yes/No): ").strip().lower()
            if "n" in ans:
                field = input("Which field is incorrect? (Recovery_Time/Country_Impact/Company_Critical): ").strip()
                new_val = input(f"Enter the correct value for {field}: ").strip()
                update_database(survey_id, field, new_val, db)
                print("RE-CALCULATING...")
                current_node = 3
            else:
                current_node = 4

        elif current_node == 4:
            print(f"\nNode 4: RACI REVIEW (Responsible: {data['RACI']['Responsible']})")
            ans = input("Prompt: 'Are these stakeholders correct?' (Yes/No): ").strip().lower()
            if "n" in ans:
                new_raci = input("Enter the correct Responsible stakeholder name: ").strip()
                update_database(survey_id, "RACI", {"Responsible": new_raci}, db)
                current_node = 4
            else:
                choice = input("Path: (A) Monitor or (B) Address: ").strip().upper()
                current_node = 5 if choice == "A" else 7

        # PHASE 3 & 4: MONITORING & INTERVENTION
        elif current_node == 5:
            freq = input("\nNode 5: Frequency (3, 6, 12 months): ").strip()
            print(f"Node 6: Completed. Risk assigned to {data['RACI']['Responsible']} for {freq} months.")
            print("SYSTEM: Updating Audit Log and Investor Dashboard.")
            current_node = 0

        elif current_node == 7:
            print("\nNode 7: Intervention Strategy (A:Mitigate B:Transfer C:Avoid D:Accept)")
            choice = input("Select: ").upper()
            mapping = {"A": 8, "B": 9, "C": 10, "D": 5}
            current_node = mapping.get(choice, 7)

        # PHASE 5: ACTION PLANNING
        elif current_node == 8:
            print("\nNode 8: MITIGATE (Rationale: Fix impacts, risk remains)")
            action = input("What is the single highest-impact action to prevent decay? ")
            update_database(survey_id, "Action_Plan", action, db)
            current_node = 11

        elif current_node == 10:
            print("\nNode 10: AVOID (Decommissioning)")
            ans = input("Is the decommissioning 100% complete? (Yes/No): ").strip().lower()
            if "y" in ans:
                current_node = 11
            else:
                print("Transitioning to Monitoring path for pending action.")
                current_node = 5

        elif current_node == 11:
            print(f"\nNode 11: ARCHIVE. Interventions logged for {data['Name']}. Exit.")
            current_node = 0

    print("\n=== SESSION COMPLETE ===")

if __name__ == "__main__":
    main()
