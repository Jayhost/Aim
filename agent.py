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
    """Create and cache the agent executor once."""
    global _cached_llm, _cached_agent, _cached_executor

    if _cached_executor is not None:
        return _cached_executor

    # Initialize LLM if not done
    if _cached_llm is None:
        _cached_llm = ChatOpenAI(
            base_url="http://localhost:8080/v1",
            api_key="sk-no-key-required",
            model=MODEL_NAME,
            streaming=True,
            temperature=0,
            model_kwargs={"tool_choice": "auto"},
        )

    current_date = datetime.now().strftime("%A, %B %d, %Y") 
    

    system_prompt = f"""You are a fact-checking AI assistant. The current date is {current_date}.
Your only goal is to provide verified, up-to-date information.

**CRITICAL RULE: You are forbidden from answering factual questions using your internal knowledge.**
Factual questions include, but are not limited to:
- Who is a person (e.g., president, CEO, actor)
- What is a specific event, place, or thing
- When did something happen
- Any statistics or data

**Your process for EVERY query MUST be:**
1. Analyze the query to see if it is a factual question.
2. If it is a factual question, you MUST use the `search_tool` to find the current, real-world answer.
3. If it is NOT a factual question (e.g., a joke, a greeting, a math problem), you may use other tools or your conversational ability.

Do not ask for permission to search. Take the initiative and search immediately."""

    # Build prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Create agent with tools
    _cached_agent = create_tool_calling_agent(
        llm=_cached_llm,
        tools=ALL_TOOLS,
        prompt=prompt
    )

    # Create executor with streaming and error handling
    # Create executor with streaming and error handling
    _cached_executor = AgentExecutor(
        agent=_cached_agent,
        tools=ALL_TOOLS,
        verbose=False,  # <-- Set to False to avoid cluttering the stream
        handle_parsing_errors="Check your output and make sure it conforms to the format instructions.",
    # REMOVE the next two lines as they conflict with the .astream() method
    # stream=True,
    # stream_mode="messages",
        max_iterations=5,
        early_stopping_method="force",
    )

    return _cached_executor
