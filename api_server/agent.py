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

def never_early_stop(intermediate_steps):
    return False

def create_agent_executor():
    """Create agent that uses fast tool routing."""
    global _cached_llm, _cached_agent, _cached_executor

    if _cached_executor is not None:
        return _cached_executor

    if _cached_llm is None:
        _cached_llm = ChatOpenAI(
            base_url="http://localhost:8080/v1",#llama for docker
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
1. ALWAYS use tools for information requests
2. NEVER answer factual questions directly  
3. Use search_tool for: who, what, when, news, current information
4. Use weather_tool for: weather queries  
5. Use dad_joke_tool for: jokes

**CRITICAL: After using search_tool:**
- READ the search results carefully
- SUMMARIZE the key information from the results
- NEVER search the same query twice
- If results are relevant, provide a summary answer
- If results aren't helpful, try a DIFFERENT search query

**EXAMPLES:**
"who is president" → search_tool → read results → summarize answer
"weather london" → weather_tool → provide weather info
"tell me a joke" → dad_joke_tool → tell the joke

Just use the appropriate tool immediately and then provide the answer."""


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
        max_iterations=5,
        early_stopping_method="None",
    )
    

    # _cached_executor._should_early_stop = never_early_stop
    _cached_executor.max_iterations = 10  # Increase further

    return _cached_executor


    # Create a custom executor that disables stop conditions


    return _cached_executor

# --- At the bottom of agent.py ---

def get_llm():
    """Get the cached LLM instance, creating it if needed."""
    global _cached_llm
    
    if _cached_llm is None:
        _cached_llm = ChatOpenAI(
            base_url="http://localhost:8080/v1",
            api_key="sk-no-key-required",
            model=MODEL_NAME,
            streaming=True,
            temperature=0,
        )
    
    return _cached_llm

# Export the function, not the None variable
__all__ = ['create_agent_executor', 'get_llm']