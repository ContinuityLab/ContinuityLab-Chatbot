import sys

# --- DATABASE & SCORING ENGINES ---
def update_database(survey_id, key, value, db):
    if survey_id in db:
        db[survey_id][key] = value
        print(f"\n[SYSTEM]: Database Updated. {key} committed to record.")

def calculate_resilience_score(d):
    score = 0
    time_map = {
        "Immediately": 20, "0-1 Hr": 20, "1-3 Hrs": 20, "3-6 Hrs": 10, 
        "6-12 Hrs": 8, "12-18 Hrs": 6, "18-24 Hrs": 4, "24-72 Hrs": 0, 
        "3-7 Days": 0, "> 1 Week": 0
    }
    score += time_map.get(d.get("Recovery_Time"), 0)
    if d.get("Country_Impact") == "Yes": score += 12
    if d.get("Company_Critical") == "Yes": score += 12
    if d.get("Customer_Time_Critical") == "Yes": score += 12
    if d.get("Customer_Data") == "Yes": score += 15
    if d.get("Employee_Data") == "Yes": score += 15
    if d.get("Proprietary_Info") == "Yes": score += 8
    if d.get("Financial_Data") == "Yes": score += 4
    if d.get("Backed_Up") == "Yes": score += 2
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
        "Action_Plan": None
    }
}

def main(survey_id="survey-001"):
    current_node = 1
    db = SIMULATED_DB
    
    while current_node != 0:
        data = db.get(survey_id)
        score = calculate_resilience_score(data)

        # --- PHASE 1: IDENTIFICATION & CONNECTION ---
        if current_node == 1:
            print("\n[NODE 1: INTENT]")
            ans = input("Prompt: 'Do you want to address this redundancy?' (Yes/No): ").strip().lower()
            current_node = 2 if "y" in ans else 0

        elif current_node == 2:
            print("\n[NODE 2: WORKFLOW CONNECTION]")
            ans = input("Prompt: 'Could we connect this redundancy to an active workflow?' (Yes/No): ").strip().lower()
            if "y" in ans:
                wf = input("SYSTEM: Select workflow name: ")
                update_database(survey_id, "Workflow", wf, db)
                print(f"ACTION: {data['Name']} flagged as connected and removed from analytics dashboard.")
                current_node = 0
            else:
                print("User Choice: (A) Monitor or (C) Do Nothing")
                choice = input("Selection: ").strip().upper()
                if choice == "A": current_node = 5
                elif choice == "C": 
                    print("Exiting flow. No changes made.")
                    current_node = 0
                else: current_node = 3 # Logic safety to Phase 2

        # --- PHASE 2: VALIDATION & STAKEHOLDERS ---
        elif current_node == 3:
            print(f"\n[NODE 3: DATA REVIEW] Resilience Score: {score}/100")
            ans = input("Prompt: 'Have you reviewed this assessment and are you ready to proceed?' (Yes/No): ").strip().lower()
            if "n" in ans:
                print("GUARDRAIL: Return to survey, update data, and re-submit. Flow Closes.")
                current_node = 0
            else:
                # Explicit check for data correctness
                correct = input("Is the retrieved data correct? (Yes/No): ").strip().lower()
                if "n" in correct:
                    field = input("Which field is incorrect? ")
                    val = input(f"New value for {field}? ")
                    update_database(survey_id, field, val, db); current_node = 3
                else: current_node = 4

        elif current_node == 4:
            raci = data['RACI']['Responsible']
            print(f"\n[NODE 4: RACI REVIEW]")
            print(f"ACTION: Displaying RACI data. This risk is assigned to: {raci}")
            ans = input("Prompt: 'Are these stakeholders correct?' (Yes/No): ").strip().lower()
            if "n" in ans:
                name = input("Correct Responsible Name? ")
                update_database(survey_id, "RACI", {"Responsible": name}, db); current_node = 4
            else:
                print("DECISION PATH: (A) Monitor, (B) Address, or (C) Do Nothing")
                choice = input("Selection: ").strip().upper()
                if choice == "A": current_node = 5
                elif choice == "B": current_node = 7
                else: 
                    print("Exiting flow."); current_node = 0

        # --- PHASE 3: MONITORING FLOW ---
        elif current_node == 5:
            print("\n[NODE 5: FREQUENCY SELECTION]")
            freq = input("Options: 3 months, 6 months, 12 months. Select: ").strip()
            print("ACTION: Survey will show up in unfinished business table.")
            current_node = 6

        elif current_node == 6:
            raci = data['RACI']['Responsible']
            print(f"\n[NODE 6: MONITORING RECAP]")
            print(f"EXPLAIN: You have completed the monitoring flow. We are now assigning risk to {raci}.")
            print(f"They will be reminded of this risk at {freq} intervals.")
            print("SYSTEM ACTION: Update Audit Log, Database, and Investor Dashboard.")
            current_node = 0

        # --- PHASE 4: INTERVENTION STRATEGIES ---
        elif current_node == 7:
            print("\n[NODE 7: INTERVENTION SELECTION]")
            print("It is time to decide which intervention is most appropriate. This action will be tracked.")
            print("\n(A) Mitigate - Rationale: Simple fix to reduce impacts. Redundancy still needed.")
            print("(B) Transfer - Rationale: Best for vendors/tech. Pay 3rd party to take risk.")
            print("(C) Avoid - Rationale: Decommission core-assets/halt duplicate work.")
            print("(D) Accept and Monitor - Rationale: Cost of mitigation higher than potential loss.")
            
            choice = input("\nSelect A, B, C, or D: ").strip().upper()
            mapping = {"A": 8, "B": 9, "C": 10, "D": 5}
            current_node = mapping.get(choice, 7)

        # --- PHASE 5: ACTION PLANNING ---
        elif current_node == 8:
            print("\n[NODE 8: MITIGATE ACTION PLAN]")
            print("GUIDANCE: Essential backups risk 'DECAY'. Mitigation means updates to guarantee readiness.")
            print("USER PROMPT: What is the single, easiest, and highest-impact action you can take to keep it sharp?")
            action = input("User Input (Action Item): ")
            update_database(survey_id, "Action_Plan", action, db)
            current_node = 11

        elif current_node == 9:
            print("\n[NODE 9: TRANSFER ACTION PLAN]")
            print("GUIDANCE: Shift responsibility to Insurance (Cyber/Key Person), SLAs, or Outsourcing.")
            print("USER PROMPT: Who is better positioned than you to absorb this redundancy?")
            action = input("User Input (Entity/Method): ")
            update_database(survey_id, "Action_Plan", action, db)
            current_node = 11

        elif current_node == 10:
            print("\n[NODE 10: AVOID ACTION PLAN]")
            print("GUIDANCE: Decommissioning is permanently retiring the component.")
            print("PROMPT: Confirm action plan and if decommissioning is 100% complete?")
            print("✅ Yes (Resolved/Archive) | ❌ No (Monitor Action First)")
            ans = input("Answer (Yes/No): ").strip().lower()
            if "y" in ans: current_node = 11
            else:
                print("Updating record to 'Monitoring: Action Pending'...")
                current_node = 5

        # --- PHASE 6: FINALIZATION ---
        elif current_node == 11:
            print("\n[NODE 11: ARCHIVE THE REDUNDANCY]")
            print("EXPLAIN: You have just completed and addressed the redundancy.")
            print("SYSTEM: Interaction added to Audit Log. Database committed. Investor Dashboard Updated.")
            current_node = 0

    print("\n=== TRAIN AT END OF TRACK ===")

if __name__ == "__main__":
    main()