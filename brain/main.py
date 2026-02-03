import os
import sys
import time
import httpx
import anthropic
from rag_client import init_rag, lookup_business_context

# 1. Setup Client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
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

def fetch_tools():
    """Fetch available tools from the tool server"""
    print("Fetching tools from Tool Server...")
    try:
        with httpx.Client() as c:
            response = c.get(f"{TOOL_URL}/tools")
            response.raise_for_status()
            data = response.json()
            print(f"✓ Loaded {len(data['tools'])} tools")
            return data["tools"]
    except Exception as e:
        print(f"✗ Failed to fetch tools: {e}")
        sys.exit(1)

def build_tool_registry(tools: list) -> dict:
    """Build a registry of tool names to their endpoints and methods"""
    registry = {}
    for tool in tools:
        registry[tool["name"]] = {
            "endpoint": tool.get("endpoint"),
            "method": tool.get("method", "POST")
        }
    print(f"✓ Built tool registry: {list(registry.keys())}")
    return registry

def process_tool_call(tool_name: str, tool_input: dict, tool_registry: dict) -> str:
    """Process tool calls dynamically using the tool registry"""
    if tool_name not in tool_registry:
        return str({"error": f"Unknown tool: {tool_name}"})
    
    tool_info = tool_registry[tool_name]
    endpoint = tool_info["endpoint"]
    method = tool_info["method"]
    
    print(f"\n{'='*60}")
    print(f"[System Bus] Calling {tool_name}")
    print(f"  Endpoint: {endpoint}")
    print(f"  Method: {method}")
    print(f"  URL: {TOOL_URL}{endpoint}")
    print(f"  Input: {tool_input}")
    
    try:
        with httpx.Client(timeout=15.0) as c:
            if method == "POST":
                print(f"[System Bus] Sending POST request...")
                response = c.post(f"{TOOL_URL}{endpoint}", json=tool_input)
            elif method == "GET":
                print(f"[System Bus] Sending GET request...")
                response = c.get(f"{TOOL_URL}{endpoint}", params=tool_input)
            else:
                return str({"error": f"Unsupported HTTP method: {method}"})
            
            print(f"[System Bus] Response status: {response.status_code}")
            response.raise_for_status()
            result = response.json()
            print(f"[System Bus] Response data: {result}")
            print(f"{'='*60}\n")
            return result
    except Exception as e:
        error = {"error": f"Tool call failed: {str(e)}"}
        print(f"[System Bus] ERROR: {error}")
        print(f"{'='*60}\n")
        return error

def run_agent():
    # Initialize RAG client for business context
    print("Initializing RAG client...")
    init_rag()
    
    # Fetch tools from Tool Server
    tools = fetch_tools()
    
    # Build tool registry for dynamic dispatch
    tool_registry = build_tool_registry(tools)
    
    # Extract Claude-compatible tool definitions (without endpoint/method)
    claude_tools = []
    for tool in tools:
        claude_tool = {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["input_schema"]
        }
        claude_tools.append(claude_tool)
    
    # Initialize conversation with Claude
    messages = []
    system_prompt = """You are an American Colonial assistant - you MUST reply to the user in period accurate vernacular at all times. Use the available tools to assist with analysis and information.

When answering questions about business terms, concepts, or financial topics, reference the business context provided to give accurate and informed answers."""
    
    print("--- Claude Control Unit Active ---")
    print("Type 'exit' or 'quit' to stop\n")
    
    while True:
        try:
            user_prompt = input("User > ").strip()
            if not user_prompt:
                continue
            if user_prompt.lower() in ["exit", "quit"]: 
                break

            # Enrich user prompt with business context if relevant
            business_context = lookup_business_context(user_prompt, top_k=5)
            enriched_prompt = user_prompt
            if business_context:
                enriched_prompt = f"{business_context}\n\nUser Query: {user_prompt}"

            messages.append({
                "role": "user",
                "content": enriched_prompt
            })

            # Agentic loop with tool use
            while True:
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=1024,
                    system=system_prompt,
                    tools=claude_tools,
                    messages=messages
                )

                # Check if we need to process tool calls
                if response.stop_reason == "tool_use":
                    # Find tool use blocks
                    assistant_content = []
                    tool_results = []
                    
                    for block in response.content:
                        assistant_content.append(block)
                        if block.type == "tool_use":
                            tool_result = process_tool_call(block.name, block.input, tool_registry)
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool_result
                            })
                    
                    # Add assistant response to messages
                    messages.append({
                        "role": "assistant",
                        "content": assistant_content
                    })
                    
                    # Add tool results
                    messages.append({
                        "role": "user",
                        "content": tool_results
                    })
                else:
                    # End of conversation turn
                    # Extract text response
                    for block in response.content:
                        if hasattr(block, "text"):
                            print(f"Agent > {block.text}\n")
                    break
                    
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