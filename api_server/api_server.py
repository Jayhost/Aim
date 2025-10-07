# File: api_server.py

import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import logging

# Set up logging
# logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("api_server")

# Import your existing agent creator
from agent import create_agent_executor

def ultra_fast_response(query: str) -> str | None:
    """Ultra-fast responses for common queries without any agent overhead."""
    query_lower = query.lower().strip()
    
    # Direct cached responses for super common queries
    instant_responses = {
        "hello": "Hello! How can I help you today?",
        "hi": "Hi there! What can I assist you with?",
        "how are you": "I'm doing well, thank you! How can I help you?",
        "what is your name": "I'm Privy, your AI assistant!",
        "who are you": "I'm Privy, an AI assistant designed to help you find information.",
    }
    
    if query_lower in instant_responses:
        return instant_responses[query_lower]
    
    # For search queries, don't return ultra-fast responses - let the agent handle them
    # This prevents bypassing the search tool
    return None

# Initialize the agent executor once on startup
# logger.debug("🔄 Initializing agent executor...")
agent_executor = create_agent_executor()
# logger.debug("✅ Agent executor initialized")

# --- FastAPI App Setup ---
app = FastAPI()

# Configure CORS to allow your Blazor app to connect
# IMPORTANT: In production, you should restrict the origins.
origins = [
    "http://localhost:5000", # Example Blazor dev server port
    "https://localhost:5001",
    "http://localhost:5199", # Another common Blazor port
    "https://localhost:7155"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the request model to match what Blazor will send
class ChatRequest(BaseModel):
    input: str

# --- Streaming Event Generator ---
async def stream_agent_response(chat_request: ChatRequest):
    """
    Calls the agent's astream_events and yields formatted Server-Sent Events.
    """
    # logger.debug(f"🎯 Starting stream for query: '{chat_request.input}'")
    
    # ULTRA-FAST PRE-CHECK
    fast_response = ultra_fast_response(chat_request.input)
    if fast_response:
        logger.debug(f"🚀 ULTRA-FAST response for: '{chat_request.input}'")
        # Yield the fast response immediately
        yield {
            "event": "message",
            "data": json.dumps({"type": "token", "content": fast_response})
        }
        return


    event_count = 0
    try:
        async for event in agent_executor.astream_events(
            {"input": chat_request.input},
            version="v1",
        ):
            event_count += 1
            kind = event["event"]
            data_payload = {}
            
            # logger.debug(f"🔄 Event {event_count}: {kind}")

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    data_payload = {"type": "token", "content": content}
                    # logger.debug(f"💬 Token: {content[:50]}...")
            
            elif kind == "on_tool_start":
                tool_name = event['name']
                tool_input = event['data'].get('input')
                data_payload = {
                    "type": "tool_start", 
                    "name": tool_name,
                    "input": tool_input
                }
                # logger.debug(f"🛠️ Tool START: {tool_name} with input: {str(tool_input)[:100]}...")
        
            elif kind == "on_tool_end":
                tool_name = event['name']
                tool_output = event['data'].get('output', '')
                data_payload = {
                    "type": "tool_end",
                    "name": tool_name,
                    "output": tool_output
                }
                # logger.debug(f"🛠️ Tool END: {tool_name} with output length: {len(str(tool_output))}")
                # logger.debug(f"🛠️ Tool output sample: {str(tool_output)[:200]}...")

            elif kind == "on_chain_start":
                chain_name = event["name"]
                # logger.debug(f"⛓️ Chain START: {chain_name}")

            elif kind == "on_chain_end":
                chain_name = event["name"]
                # logger.debug(f"⛓️ Chain END: {chain_name}")
                if chain_name == "AgentExecutor":
                    output_data = event['data'].get('output', {})
                    # logger.debug(f"🏁 AgentExecutor finished with output: {str(output_data)[:200]}...")
            
            # Yield the event if it has content
            if data_payload:
                yield {
                    "event": "message",
                    "data": json.dumps(data_payload)
                }
                
        # logger.debug(f"✅ Stream completed. Total events: {event_count}")

    except Exception as e:
        # logger.error(f"❌ Error in stream_agent_response: {e}")
        import traceback
        # logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        # Yield an error event to the client
        error_payload = {
            "type": "error",
            "content": f"An error occurred: {str(e)}"
        }
        yield {
            "event": "message",
            "data": json.dumps(error_payload)
        }

# --- API Endpoint ---
@app.post("/agent-chat")
async def chat_endpoint(chat_request: ChatRequest):
    """
    The main chat endpoint that Blazor will call.
    """
    # logger.debug(f"📥 Received chat request: '{chat_request.input}'")
    return EventSourceResponse(stream_agent_response(chat_request))

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "service": "cluj-ai-api"}

@app.get("/tools")
async def list_tools():
    """Debug endpoint to list available tools."""
    try:
        from tools import ALL_TOOLS
        tools_info = []
        for tool in ALL_TOOLS:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "args": str(tool.args)
            })
        return {"tools": tools_info}
    except Exception as e:
        return {"error": str(e)}

@app.get("/test-search")
async def test_search():
    """Test the search tool directly"""
    try:
        from tools import search_tool
        result = search_tool("current president of the United States")
        return {
            "status": "search_tool test completed",
            "result_length": len(result),
            "result_preview": result[:500] + "..." if len(result) > 500 else result
        }
    except Exception as e:
        return {"status": "search_tool test failed", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    # logger.info("🚀 Starting API server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="debug")