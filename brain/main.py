import os
import sys
import time
import httpx
from google import genai
from google.genai import types

# 1. Setup Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
TOOL_URL = os.getenv("TOOL_SERVER_URL", "http://tools:8000")

def wait_for_tools(retries=30):
    """Wait for tools service to be ready"""
    print("Waiting for Tool Server to be ready...")
    for i in range(retries):
        try:
            response = httpx.get(f"{TOOL_URL}/health")
            if response.status_code == 200:
                print("✓ Tool Server is READY")
                return True
        except httpx.RequestError:
            print(f"  Attempt {i+1}/{retries}... (waiting for Tool Server)")
            time.sleep(1)
    print("✗ Tool Server failed to start")
    return False

# 2. Define the "Body" Wrapper
# Gemini uses the docstring and type hints to understand the tool!
def calculate_margin(revenue: float, cost: float) -> dict:
    """Calculates the profit margin for a project given revenue and cost."""
    print(f"--- [System Bus] Calling Tool Server for Margin ---")
    with httpx.Client() as c:
        response = c.post(f"{TOOL_URL}/calculate_margin", json={"revenue": revenue, "cost": cost})
        return response.json()

def run_agent():
    # 3. Initialize Chat with Tools
    chat = client.chats.create(
        model="gemini-flash-latest", # High speed/low cost for agents
        config=types.GenerateContentConfig(
            tools=[calculate_margin],
            system_instruction="You are a Ross MBA assistant. Use the margin tool for all financial analysis."
        )
    )

    print("--- Gemini Control Unit Active ---")
    print("Type 'exit' or 'quit' to stop\n")
    
    while True:
        try:
            user_prompt = input("User > ").strip()
            if not user_prompt:
                continue
            if user_prompt.lower() in ["exit", "quit"]: 
                break

            # automatic_function_calling=True handles the internal loop for you
            response = chat.send_message(
                user_prompt,
                config=types.GenerateContentConfig(
                    automatic_function_calling={"disable": False}
                )
            )
            print(f"Agent > {response.text}\n")
        except EOFError:
            # Handle when stdin is closed (common in containers)
            print("\nNo input available. Shutting down gracefully.")
            break
        except KeyboardInterrupt:
            print("\n\nShutting down...")
            break

if __name__ == "__main__":
    if not wait_for_tools():
        print("CRITICAL: Tool Server is not available")
        sys.exit(1)
    
    run_agent()