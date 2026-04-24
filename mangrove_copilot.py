# mangrove_copilot.py
# Complete Python-based state machine using azure-ai-projects SDK

import os
from typing import Dict, Any

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool

# Agent System Instruction
AGENT_SYSTEM_INSTRUCTION = "Output exactly the provided text without adding or changing anything."

# Simulated Mangrove Database
SIMULATED_MANGROVE_DB = {
    "survey-001": {
        "Country Impact": "High",
        "Company Impact": "Medium",
        "Customer Criticality": "High",
        "RACI": {
            "Responsible": "Risk Team Lead",
            "Accountable": "CRO",
            "Consulted": "Operations",
            "Informed": "Finance"
        },
    },
    "survey-002": {
        "Country Impact": "Medium",
        "Company Impact": "High",
        "Customer Criticality": "Medium",
        "RACI": {
            "Responsible": "Compliance Manager",
            "Accountable": "COO",
            "Consulted": "Legal",
            "Informed": "HR"
        },
    },
}

def fetch_mangrove_data(survey_id: str) -> Dict[str, Any]:
    record = SIMULATED_MANGROVE_DB.get(survey_id)
    if record is None:
        raise ValueError(f"No mangrove data found for survey_id '{survey_id}'.")
    return record

def create_fetch_mangrove_data_tool() -> FunctionTool:
    return FunctionTool(
        type="function",
        name="fetch_mangrove_data",
        description=(
            "Returns Country Impact, Company Impact, Customer Criticality, and RACI data "
            "from a simulated database for the provided survey_id."
        ),
        parameters={
            "type": "object",
            "properties": {
                "survey_id": {
                    "type": "string",
                    "description": "The survey identifier used to retrieve mangrove risk data.",
                }
            },
            "required": ["survey_id"],
        },
        strict=True,
    )

def prompt_yes_no(prompt: str) -> bool:
    while True:
        answer = input(prompt + " ").strip().lower()
        if answer in {"yes", "y"}:
            return True
        if answer in {"no", "n"}:
            return False
        print("Please answer 'Yes' or 'No'.")

def prompt_choice(prompt: str, valid_choices: Dict[str, str]) -> str:
    choice_keys = "/".join(valid_choices.keys())
    while True:
        answer = input(f"{prompt} ({choice_keys}) ").strip().upper()
        if answer in valid_choices:
            return answer
        print(f"Please choose one of: {', '.join(valid_choices.keys())}.")

def get_agent_response(openai_client, prompt_text: str, tools=None, tool_choice=None):
    extra_body = {
        "agent_reference": {"name": "Decision-Tree-Redundancy", "version": "3", "type": "agent_reference"}
    }
    full_prompt = f"{AGENT_SYSTEM_INSTRUCTION} {prompt_text}"
    kwargs = {}
    if tools:
        kwargs['tools'] = tools
    if tool_choice:
        kwargs['tool_choice'] = tool_choice
    response = openai_client.responses.create(
        input=[{"role": "user", "content": full_prompt}],
        extra_body=extra_body,
        **kwargs
    )
    return response.output_text

def main(survey_id: str = "survey-001"):
    endpoint = "https://info-6762-resource.services.ai.azure.com/api/projects/info-6762"
    project_client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )
    openai_client = project_client.get_openai_client()

    fetch_tool = create_fetch_mangrove_data_tool()

    print(f"Agent System Instruction: {AGENT_SYSTEM_INSTRUCTION}")
    print(f"Initialized AIProjectClient for endpoint: {endpoint}")
    print(f"Survey ID: {survey_id}")
    print()

    current_node = 1
    connected_to_workflow = False
    mangrove_data = None

    while current_node != 0:
        if current_node == 1:
            prompt = "Do you want to address this redundancy?"
            agent_response = get_agent_response(openai_client, prompt)
            print(f"Agent: {agent_response}")
            if prompt_yes_no("Answer:"):
                current_node = 2
            else:
                print("Exiting flow.")
                current_node = 0

        elif current_node == 2:
            prompt = "Could we connect this redundancy to an active workflow?"
            agent_response = get_agent_response(openai_client, prompt)
            print(f"Agent: {agent_response}")
            if prompt_yes_no("Answer:"):
                connected_to_workflow = True
                print("This redundancy is flagged as connected to an active workflow. Exiting flow.")
                current_node = 0
            else:
                choice = prompt_choice(
                    "Force choice: (A) Monitor or (C) Do Nothing.",
                    {"A": "Monitor", "C": "Do Nothing"},
                )
                print(f"Choice selected: {choice}")
                current_node = 3

        elif current_node == 3:
            prompt = f"Call fetch_mangrove_data for survey_id '{survey_id}'. Explain the Country Impact, Company Impact, Customer Criticality. Ask if the user has reviewed this assessment and is ready to proceed."
            agent_response = get_agent_response(
                openai_client,
                prompt,
                tools=[fetch_tool],
                tool_choice={'type': 'function', 'function': {'name': 'fetch_mangrove_data'}}
            )
            print(f"Agent: {agent_response}")
            mangrove_data = fetch_mangrove_data(survey_id)  # Assuming agent calls it, but we fetch locally for logic
            if prompt_yes_no("Answer:"):
                current_node = 4
            else:
                print("Closing flow.")
                current_node = 0

        elif current_node == 4:
            responsible = mangrove_data["RACI"]["Responsible"]
            prompt = f"Displaying RACI data. This risk is assigned to {responsible}. Are these stakeholders correct?"
            agent_response = get_agent_response(openai_client, prompt)
            print(f"Agent: {agent_response}")
            decision = prompt_choice(
                "Decision:",
                {"A": "Monitor", "B": "Address"},
            )
            if decision == "A":
                current_node = 5
            else:
                current_node = 7

        elif current_node == 5:
            frequency = prompt_choice(
                "Choose the monitoring frequency:",
                {"3": "3 months", "6": "6 months", "12": "12 months"},
            )
            print(f"Monitoring set for every {frequency} months.")
            print("Exiting flow.")
            current_node = 0

        elif current_node == 7:
            prompt = "Based on the criticality and stakeholder review, which intervention is most appropriate? (A) Mitigate, (B) Transfer, (C) Avoid, (D) Accept."
            agent_response = get_agent_response(openai_client, prompt)
            print(f"Agent: {agent_response}")
            decision = prompt_choice(
                "Choose intervention:",
                {"A": "Mitigate", "B": "Transfer", "C": "Avoid", "D": "Accept"},
            )
            if decision == "A":
                current_node = 8
            elif decision == "B":
                current_node = 9
            elif decision == "C":
                current_node = 10
            else:
                print("Acceptance selected. Exiting flow.")
                current_node = 0

        elif current_node == 8:
            action_item = input("Enter one clear action item to prevent decay: ").strip()
            print(f"Mitigation action item recorded: {action_item}")
            print("Updating Audit Log and Investor Dashboard.")
            current_node = 0

        elif current_node == 9:
            entity = input("Enter the entity (Insurance/Vendor) taking the risk: ").strip()
            print(f"Transfer entity recorded: {entity}")
            print("Updating Audit Log and Investor Dashboard.")
            current_node = 0

        elif current_node == 10:
            print("Confirm: Is the decommissioning 100% complete?")
            if prompt_yes_no("Answer:"):
                current_node = 11
            else:
                current_node = 5

        elif current_node == 11:
            print("Updating Audit Log and Investor Dashboard.")
            print("Finalize complete. Exiting flow.")
            current_node = 0

    if connected_to_workflow:
        print("Workflow connection flag is set.")

if __name__ == "__main__":
    import sys
    survey_id = sys.argv[1] if len(sys.argv) > 1 else "survey-001"
    main(survey_id)