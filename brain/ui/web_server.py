"""
Web UI for the Brain agent - provides HTTP interface for chat
"""
import os
import sys
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import json
import httpx

# Add parent directory to path to import agent functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    client, TOOL_URL, fetch_tools, build_tool_registry, 
    process_tool_call
)

app = FastAPI()

# State management
class ConversationState:
    def __init__(self):
        self.messages = []
        self.tools = []
        self.tool_registry = {}
        self.claude_tools = []
        self.initialized = False
    
    def initialize(self):
        """Initialize tools on first use"""
        if not self.initialized:
            print("🔍 Initializing agent tools...")
            self.tools = fetch_tools()
            self.tool_registry = build_tool_registry(self.tools)
            
            # Extract Claude-compatible tool definitions
            self.claude_tools = []
            for tool in self.tools:
                self.claude_tools.append({
                    "name": tool["name"],
                    "description": tool["description"],
                    "input_schema": tool["input_schema"]
                })
            self.initialized = True
            print(f"✓ Agent ready with {len(self.claude_tools)} tools")

state = ConversationState()

class ChatMessage(BaseModel):
    content: str

class ChatResponse(BaseModel):
    response: str
    error: str = None

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    try:
        with httpx.Client() as c:
            response = c.get(f"{TOOL_URL}/health")
            if response.status_code == 200:
                print("✓ Tool Server is READY")
    except Exception as e:
        print(f"⚠️  Tool Server not ready on startup: {e}")

@app.post("/api/chat")
async def chat(message: ChatMessage):
    """Send a message to the agent and get response"""
    try:
        state.initialize()
        
        # Add user message
        state.messages.append({
            "role": "user",
            "content": message.content
        })
        
        system_prompt = "You are a Ross MBA assistant. Before claiming what tools you have available, always reference the actual tools you've been given. You have access to a dynamic set of tools - describe and use only what's in your tool list. Use the available tools to assist with analysis and information."
        
        # Agentic loop with tool use
        current_messages = list(state.messages)
        while True:
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=system_prompt,
                tools=state.claude_tools,
                messages=current_messages
            )
            
            if response.stop_reason == "tool_use":
                assistant_content = []
                tool_results = []

                for block in response.content:
                    assistant_content.append(block)
                    if block.type == "tool_use":
                        # Execute the tool; process_tool_call returns a dict or error dict.
                        raw_result = process_tool_call(
                            block.name, block.input, state.tool_registry
                        )

                        # Build the required tool_result block expected by the LLM
                        # The LLM API expects `tool_result` content to be a string
                        # or a list of content blocks. Send the raw result as a
                        # compact JSON string so the model can interpret it, and
                        # avoid mutating persisted history.
                        try:
                            payload = json.dumps(raw_result, ensure_ascii=False)
                        except Exception:
                            payload = str(raw_result)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": payload
                        })

                # Do NOT persist these temporary messages; instead extend
                # the local `current_messages` list for the next model call.
                assistant_msg = {"role": "assistant", "content": assistant_content}
                tool_result_msg = {"role": "user", "content": tool_results}
                current_messages = current_messages + [assistant_msg, tool_result_msg]
            else:
                # Extract final text response
                final_response = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_response += block.text
                
                # Add assistant final response to persisted history
                state.messages.append({"role": "assistant", "content": final_response})

                # Return only the LLM's final text to the UI. Tool execution
                # details are kept in server/container logs and are not exposed.
                return ChatResponse(response=final_response)
    
    except Exception as e:
        return ChatResponse(response="", error=str(e))

@app.get("/api/history")
async def get_history():
    """Get conversation history"""
    state.initialize()
    return {"messages": state.messages}

@app.post("/api/reset")
async def reset_conversation():
    """Reset conversation history"""
    state.messages = []
    return {"status": "reset"}

@app.get("/")
async def get_index():
    """Serve the web UI"""
    ui_dir = os.path.dirname(os.path.abspath(__file__))
    return FileResponse(os.path.join(ui_dir, "index.html"))

# Serve static files
ui_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(ui_dir, "static")), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
