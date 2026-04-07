# bot/agent.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from bot.tools import (
    get_current_datetime,
    calculator,
    search_wikipedia,
    quiz_generator,
    study_planner,
    flashcard_maker,
    concept_simplifier
)

# 1. LLM — use lite model (higher free quota)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",   # ← lighter = more free quota
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)

# 2. Tools
tools = [
    get_current_datetime,
    calculator,
    search_wikipedia,
    quiz_generator,
    study_planner,
    flashcard_maker,
    concept_simplifier
]

# 3. Shorter system prompt — fewer tokens!
SYSTEM_PROMPT = """You are a friendly study assistant for students.
Use the right tool for each request:
- quiz_generator → for quizzes
- study_planner → for study schedules
- flashcard_maker → for flashcards
- concept_simplifier → for simple explanations
- search_wikipedia → for facts
- calculator → for maths
- get_current_datetime → for date/time
Be concise, encouraging, and warm. This is WhatsApp — keep replies short!"""

# 4. Config
HISTORY_WINDOW = 6    # ← only last 6 messages sent to Gemini
MAX_INPUT_LENGTH = 500  # ← cap incoming message length

# 5. Create Agent
agent = create_react_agent(llm, tools)

# 6. Per-user memory store
memory_store = {}

def get_bot_response(message: str, user_id: str) -> str:
    chat_history = memory_store.get(user_id, [])

    # ✅ QUOTA SAVER — keep only last 6 messages (3 exchanges)
    # Just like RAG chunking — send only relevant recent context!
    chat_history = chat_history[-6:]

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + chat_history + [HumanMessage(content=message)]

    result = agent.invoke({"messages": messages})
    response = result["messages"][-1].content

    # Save full history but only send recent chunk
    full_history = memory_store.get(user_id, [])
    full_history.append(HumanMessage(content=message))
    full_history.append(AIMessage(content=response))
    memory_store[user_id] = full_history

    return response