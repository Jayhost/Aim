# File: api_server.py

import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Import your existing agent creator
from agent import create_agent_executor

# Initialize the agent executor once on startup
agent_executor = create_agent_executor()

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
    async for event in agent_executor.astream_events(
        {"input": chat_request.input},
        version="v1",
    ):
        kind = event["event"]
        data_payload = {}

        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                data_payload = {"type": "token", "content": content}
        
        elif kind == "on_tool_start":
            data_payload = {
                "type": "tool_start", 
                "name": event['name'],
                "input": event['data'].get('input')
            }

        elif kind == "on_tool_end":
            data_payload = {
                "type": "tool_end",
                "name": event['name'],
                "output": event['data'].get('output', '')
            }
        
        # Yield the event if it has content
        if data_payload:
            yield {
                "event": "message",
                "data": json.dumps(data_payload)
            }

# --- API Endpoint ---
@app.post("/agent-chat")
async def chat_endpoint(chat_request: ChatRequest):
    """
    The main chat endpoint that Blazor will call.
    """
    return EventSourceResponse(stream_agent_response(chat_request))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)