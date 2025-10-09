# --- Agent Executor (agent.py) ---
# File: agent.py

from langchain.agents import create_tool_calling_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config import MODEL_NAME
from tools import ALL_TOOLS
from datetime import datetime

# Caching to prevent repeated agent creation
_cached_llm = None
_cached_agent = None
_cached_executor = None

def create_agent_executor():
    """Create agent that uses fast tool routing."""
    global _cached_llm, _cached_agent, _cached_executor

    if _cached_executor is not None:
        return _cached_executor

    if _cached_llm is None:
        _cached_llm = ChatOpenAI(
            base_url="http://localhost:8080/v1",
            api_key="sk-no-key-required",
            model=MODEL_NAME,
            streaming=True,
            temperature=0,
        )

    # Import the fast routing function
    from tools import route_to_tool_directly

    # SIMPLE system prompt that forces tool usage
    system_prompt = f"""You are a helpful assistant. Current date: {datetime.now().strftime("%A, %B %d, %Y")}.

**RULES:**
- ALWAYS use tools for information requests
- NEVER answer factual questions directly
- Use search_tool for: who, what, when, news, current information
- Use weather_tool for: weather queries  
- Use dad_joke_tool for: jokes

**EXAMPLES:**
"who is president" → search_tool
"weather london" → weather_tool
"tell me a joke" → dad_joke_tool

Just use the appropriate tool immediately."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    _cached_agent = create_tool_calling_agent(
        llm=_cached_llm,
        tools=ALL_TOOLS,
        prompt=prompt
    )

    # Create a custom executor that uses fast routing
    class FastAgentExecutor(AgentExecutor):
        async def ainvoke(self, input, *args, **kwargs):
            # Fast pre-routing before agent reasoning
            from tools import route_to_tool_directly
            fast_tool = route_to_tool_directly(input.get('input', ''))
            
            if fast_tool and fast_tool == 'search_tool':
                print(f"🚀 FAST ROUTING to search_tool for: {input['input']}")
                # Force search tool usage
                from tools import search_tool
                result = search_tool.invoke({"query": input['input']})
                return {"output": result, "intermediate_steps": []}
            
            # Fall back to normal agent for other cases
            return await super().ainvoke(input, *args, **kwargs)

    _cached_executor = FastAgentExecutor(
        agent=_cached_agent,
        tools=ALL_TOOLS,
        verbose=True,  # Keep verbose to see what's happening
        handle_parsing_errors=True,
        max_iterations=2,
        early_stopping_method="generate",
    )

    return _cached_executor