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
    ("system", """You are an intelligent and friendly study assistant for students.
Your job is to:
- Explain concepts clearly and simply
- Quiz students when asked
- Summarize notes and textbook content
- Solve problems step by step
- Keep the student motivated

Always be encouraging, patient, and use simple language.
If a topic is complex, break it into smaller parts.
Keep responses concise — this is WhatsApp, not an essay!
Remember details the student shares like their name and subjects."""),
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