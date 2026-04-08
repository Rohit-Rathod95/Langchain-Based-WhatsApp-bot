# bot/chain.py

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage

# 1. The LLM — Gemini
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.7
)

# 2. Prompt now includes chat_history placeholder
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a friendly study assistant for students.
Use the right tool for each request:
- quiz_generator → for quizzes and MCQs
- study_planner → for study schedules
- flashcard_maker → for flashcards
- concept_simplifier → explain simply like age 10
- search_wikipedia → for factual topic info
- web_search → for latest/current information
- exam_strategy_coach → for exam prep strategy
- story_based_learning → teach through stories
- study_break_coach → when student needs a break
- calculator → for maths calculations
- get_current_datetime → for date/time

Be concise, encouraging, and warm. This is WhatsApp — keep replies short!"""),
    MessagesPlaceholder(variable_name="chat_history"),  # ← memory goes here
    ("human", "{student_message}")
])



# 3. Output Parser
parser = StrOutputParser()

# 4. Chain
chain = prompt | llm | parser

# 5. In-memory store — per user chat history
# Key = phone number, Value = list of messages
memory_store = {}

def get_bot_response(message: str, user_id: str) -> str:
    # Get this user's history (empty list if first time)
    chat_history = memory_store.get(user_id, [])

    # Run the chain with history
    response = chain.invoke({
        "chat_history": chat_history,
        "student_message": message
    })

    # Update memory with latest exchange
    chat_history.append(HumanMessage(content=message))
    chat_history.append(AIMessage(content=response))

    # Save back to store
    memory_store[user_id] = chat_history

    return response