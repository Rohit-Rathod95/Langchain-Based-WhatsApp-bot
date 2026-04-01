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

# 1. LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)

# 2. All 7 tools
tools = [
    get_current_datetime,
    calculator,
    search_wikipedia,
    quiz_generator,
    study_planner,
    flashcard_maker,
    concept_simplifier
]

# 3. System prompt
SYSTEM_PROMPT = """You are an intelligent and friendly study assistant for students.

You have access to these special tools — use them smartly:
- 📝 quiz_generator → when student wants to be quizzed on a topic
- 🗓️ study_planner → when student wants a study schedule
- 🔤 flashcard_maker → when student wants flashcards to memorize
- 💡 concept_simplifier → when student finds something confusing
- 🔍 search_wikipedia → for factual topic information
- 🔢 calculator → for any math calculation
- 📅 get_current_datetime → for current date/time

Rules:
- Always pick the RIGHT tool for the right question
- Keep responses concise — this is WhatsApp!
- Be encouraging, warm and motivating
- Remember the student's name and subjects throughout
- Never say you can't help — always try your best!"""

# 4. Create Agent
agent = create_react_agent(llm, tools)

# 5. Per-user memory store
memory_store = {}

def get_bot_response(message: str, user_id: str) -> str:
    chat_history = memory_store.get(user_id, [])

    messages = [SystemMessage(content=SYSTEM_PROMPT)] + chat_history + [HumanMessage(content=message)]

    result = agent.invoke({"messages": messages})
    response = result["messages"][-1].content

    chat_history.append(HumanMessage(content=message))
    chat_history.append(AIMessage(content=response))
    memory_store[user_id] = chat_history

    return response