import sys
from typing import Dict, Any
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import FunctionTool

# --- THE DATA ---
SIMULATED_DB = {
    "survey-002": {
        "Responsible": "Compliance Manager",
        "Impact": "High Company Impact",
        "Criticality": "Medium"
    }
}

def fetch_mangrove_data(survey_id: str) -> Dict[str, Any]:
    return SIMULATED_DB.get(survey_id, {"error": "Survey not found"})

def create_fetch_mangrove_data_tool() -> FunctionTool:
    return FunctionTool(
        type="function",
        name="fetch_mangrove_data",
        description="Fetches impact and RACI data for a survey ID.",
        parameters={
            "type": "object",
            "properties": {
                "survey_id": {
                    "type": "string",
                    "description": "The survey identifier.",
                }
            },
            "required": ["survey_id"],
        },
        strict=True,
    )

def get_agent_response(openai_client, prompt_text: str, tools=None, tool_choice=None):
    extra_body = {
        "agent_reference": {"name": "Decision-Tree-Redundancy", "version": "3", "type": "agent_reference"}
    }
    full_prompt = f"Output exactly the provided text without adding or changing anything. {prompt_text}"
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

def main(survey_id="survey-002"):
    endpoint = "https://info-6762-resource.services.ai.azure.com/api/projects/info-6762"
    client = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    openai_client = client.get_openai_client()
    fetch_tool = create_fetch_mangrove_data_tool()
    
    # We use the prompt strictly to force the Agent's mouth to move
    # but the Python code holds the steering wheel.
    current_node = 1
    
    while current_node != 0:
        if current_node == 1:
            print("\n--- STATION 1: INTENT ---")
            print("Target Prompt: Do you want to address this redundancy?")
            # This is the line where YOU must type
            user_choice = input("Type 'yes' to proceed or 'no' to exit: ").strip().lower()
            
            if user_choice == 'yes':
                current_node = 2
            else:
                print("Exit signal received.")
                current_node = 0

        elif current_node == 2:
            print("\n--- STATION 2: WORKFLOW ---")
            print("Target Prompt: Could we connect this to an active workflow?")
            user_choice = input("Type 'yes' or 'no': ").strip().lower()
            
            if user_choice == 'yes':
                print("ACTION: Flagged as Connected. Removed from View.")
                current_node = 0
            else:
                # Per your logic, if NO, they must choose Monitor (3)
                current_node = 3

        elif current_node == 3:
            print("\n--- STATION 3: THE TRUTH (DATA FETCH) ---")
            data = fetch_mangrove_data(survey_id)
            print(f"DATABASE FETCH SUCCESS: {data['Impact']} | {data['Responsible']}")
            # NOW we call the Agent to explain this data
            print("Agent is explaining the data...")
            prompt = f"Explain the retrieved data: Impact is {data['Impact']}, Responsible is {data['Responsible']}, Criticality is {data['Criticality']}. Ask if the user has reviewed and is ready to proceed."
            agent_response = get_agent_response(openai_client, prompt, tools=[fetch_tool], tool_choice={'type': 'function', 'function': {'name': 'fetch_mangrove_data'}})
            print(f"Agent: {agent_response}")
            
            user_choice = input("Ready to proceed to RACI review? (yes/no): ").strip().lower()
            current_node = 4 if user_choice == 'yes' else 0
            
        elif current_node == 11:
            print("Updating Dashboard... Done.")
            current_node = 0
            
    print("\n--- TRAIN HAS REACHED THE END OF THE TRACK ---")

if __name__ == "__main__":
    main()