import os
import sys
from typing import Dict, Any
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool

# --- DATABASE & SCORING ENGINES ---
def update_database(survey_id, key, value, db):
    if survey_id in db:
        db[survey_id][key] = value
        print(f"\n[SYSTEM]: Database Updated. {key} committed to record.")


def calculate_resilience_score(d):
    score = 0
    time_map = {
        "Immediately": 20,
        "0-1 Hr": 20,
        "1-3 Hrs": 20,
        "3-6 Hrs": 10,
        "6-12 Hrs": 8,
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
        "Action_Plan": None,
    }
}


def fetch_mangrove_data(survey_id: str) -> Dict[str, Any]:
    return SIMULATED_DB.get(survey_id)


def create_fetch_mangrove_data_tool() -> FunctionTool:
    return FunctionTool(
        name="fetch_mangrove_data",
        description="Retrieves full technical risk and RACI data for a survey_id.",
        func=fetch_mangrove_data,
    )


# --- THE INTEGRATED ORCHESTRATOR ---
def main(survey_id="survey-001"):
    endpoint = "https://info-6762-resource.services.ai.azure.com/api/projects/info-6762"
    project_client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    openai_client = project_client.get_openai_client()
    fetch_tool = create_fetch_mangrove_data_tool()

    current_node = 1
    db = SIMULATED_DB

    print(f"\n--- MANGROVE AZURE CO-PILOT SESSION: {survey_id} ---")

    while current_node != 0:
        data = db.get(survey_id)
        score = calculate_resilience_score(data)

        if current_node == 1:
            print("\n[Node 1: Intent]")
            ans = input("Agent: 'I've identified a redundancy. Would you like to address this now?' (Yes/No): ").strip().lower()
            current_node = 2 if "y" in ans else 0

        elif current_node == 2:
            print("\n[Node 2: Workflow]")
            ans = input("Agent: 'Is this redundancy already tied to a workflow?' (Yes/No): ").strip().lower()
            if "y" in ans:
                wf = input("Agent: 'What is the name of the workflow?' ")
                update_database(survey_id, "Workflow", wf, db)
                print(f"Agent: 'Linked to {wf}. Workflow connection flag set.'")
                current_node = 0
            else:
                print("\nAgent: 'Understood. (A) Monitor this for now, (B) Review the data, or (C) Do Nothing.'")
                choice = input("Your Choice (A/B/C): ").strip().upper()
                if choice == "A":
                    current_node = 5
                elif choice == "C":
                    current_node = 0
                else:
                    current_node = 3

        elif current_node == 3:
            print(f"\n[Node 3: Review - Resilience Score: {score}/100]")
            print(f"Current Recovery Window: {data['Recovery_Time']}")
            ans = input("Agent: 'Does this assessment feel accurate?' (Yes/No): ").strip().lower()
            if "n" in ans:
                print("Options: [Recovery_Time, Country_Impact, Company_Critical]")
                field = input("Which field needs correction? ")
                val = input(f"New value for {field}? ")
                update_database(survey_id, field, val, db)
                current_node = 3
            else:
                current_node = 4

        elif current_node == 4:
            raci = data['RACI']['Responsible']
            print("\n[Node 4: RACI Review]")
            print(f"Agent: 'This risk is currently assigned to {raci}.'")
            ans = input("Agent: 'Are these stakeholders correct?' (Yes/No): ").strip().lower()
            if "n" in ans:
                name = input("Agent: 'Correct Responsible Name? '")
                update_database(survey_id, "RACI", {"Responsible": name}, db)
                current_node = 4
            else:
                print("Agent: 'Choice: (A) Monitor, (B) Address, or (C) Do Nothing.'")
                choice = input("Selection: ").strip().upper()
                if choice == "A":
                    current_node = 5
                elif choice == "B":
                    current_node = 7
                else:
                    print("Agent: 'Closing session without changes.'")
                    current_node = 0

        elif current_node == 5:
            print("\n[Node 5: Frequency Selection]")
            freq = input("Options: 3 months, 6 months, 12 months. Select: ").strip()
            print("Agent: 'This item will appear in unfinished business.'")
            current_node = 6

        elif current_node == 6:
            raci = data['RACI']['Responsible']
            print("\n[Node 6: Monitoring Recap]")
            print(f"Agent: 'Monitoring will be assigned to {raci}.'")
            print(f"Agent: 'They will receive reminders every {freq}.'")
            print("SYSTEM ACTION: Update Audit Log, Database, and Investor Dashboard.")
            current_node = 0

        elif current_node == 7:
            print("\n[Node 7: Intervention Strategy]")
            print("Agent: 'Decide your intervention. Here is the breakdown:'")
            print("(A) Mitigate: Fix impacts, risk remains but lower.")
            print("(B) Transfer: Shift financial impact to Insurance/SLA.")
            print("(C) Avoid: Decommission the asset entirely.")
            print("(D) Accept & Monitor: Document and watch.")
            choice = input("\nAgent: 'Which strategy fits best?' (A/B/C/D): ").strip().upper()
            mapping = {"A": 8, "B": 9, "C": 10, "D": 5}
            current_node = mapping.get(choice, 7)

        elif current_node == 8:
            print("\n[Node 8: Mitigate Action Plan]")
            print("GUIDANCE: Essential backups risk 'DECAY'. Mitigation means updates to guarantee readiness.")
            action = input("User Input (Action Item): ")
            update_database(survey_id, "Action_Plan", action, db)
            current_node = 11

        elif current_node == 9:
            print("\n[Node 9: Transfer Action Plan]")
            print("GUIDANCE: Shift responsibility to Insurance (Cyber/Key Person), SLAs, or Outsourcing.")
            action = input("User Input (Entity/Method): ")
            update_database(survey_id, "Action_Plan", action, db)
            current_node = 11

        elif current_node == 10:
            print("\n[Node 10: Avoid]")
            ans = input("Agent: 'Is decommissioning 100% complete?' (Yes/No): ").strip().lower()
            if "y" in ans:
                current_node = 11
            else:
                print("Agent: 'Moving to Monitoring Path until complete.'")
                current_node = 5

        elif current_node == 11:
            print("\n[Node 11: Archive]")
            print("SYSTEM: Updating Audit Log, Database, and Investor Dashboard.")
            current_node = 0

    print("\n--- INTEGRATED SESSION COMPLETE ---")


if __name__ == "__main__":
    main()
