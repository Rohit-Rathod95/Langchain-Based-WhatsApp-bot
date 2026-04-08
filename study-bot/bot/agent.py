# bot/agent.py
import os
import importlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Dict, Tuple

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from bot.tools import (
    get_current_datetime,
    calculator,
    search_wikipedia,
    quiz_generator,
    study_planner,
    flashcard_maker,
    concept_simplifier,
    web_search,
    exam_strategy_coach,
    story_based_learning,
    study_break_coach,
    progress_tracker,
    image_explainer,
)

# ─────────────────────────────────────────
# 1. LLM
# ─────────────────────────────────────────
def build_llm():
    provider = os.getenv("BOT_LLM_PROVIDER", "auto").strip().lower()
    gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if provider == "auto":
        if gemini_api_key:
            provider = "google"
        elif groq_api_key:
            provider = "groq"
        else:
            provider = "groq"

    if provider == "groq":
        if not groq_api_key:
            raise RuntimeError(
                "Groq API key not found. Set GROQ_API_KEY in your .env file."
            )

        try:
            groq_module = importlib.import_module("langchain_groq")
            chat_groq_class = getattr(groq_module, "ChatGroq")
        except Exception as exc:
            raise RuntimeError(
                "BOT_LLM_PROVIDER=groq set, but langchain-groq is not installed. "
                "Install it with: pip install langchain-groq"
            ) from exc

        return chat_groq_class(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            groq_api_key=groq_api_key,
            temperature=0.4,
        )

    if provider == "ollama":
        try:
            ollama_module = importlib.import_module("langchain_ollama")
            chat_ollama_class = getattr(ollama_module, "ChatOllama")
        except Exception as exc:
            raise RuntimeError(
                "BOT_LLM_PROVIDER=ollama set, but langchain-ollama is not installed. "
                "Install it with: pip install langchain-ollama"
            ) from exc

        return chat_ollama_class(
            model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
            temperature=0.4,
        )

    if provider == "google" and not gemini_api_key:
        raise RuntimeError(
            "Gemini API key not found. Set GEMINI_API_KEY/GOOGLE_API_KEY, "
            "or use BOT_LLM_PROVIDER=groq with GROQ_API_KEY."
        )

    try:
        google_module = importlib.import_module("langchain_google_genai")
        chat_google_class = getattr(google_module, "ChatGoogleGenerativeAI")
    except Exception as exc:
        raise RuntimeError(
            "BOT_LLM_PROVIDER=google set, but langchain-google-genai is not installed. "
            "Install it with: pip install langchain-google-genai"
        ) from exc

    return chat_google_class(
        model=os.getenv("GOOGLE_MODEL", "gemini-2.5-flash"),
        google_api_key=gemini_api_key,
        temperature=0.7,
    )


_llm = None


def get_llm():
    global _llm
    if _llm is None:
        _llm = build_llm()
    return _llm

# ─────────────────────────────────────────
# 2. Config
# ─────────────────────────────────────────
HISTORY_WINDOW = 6
MAX_INPUT_LENGTH = 500
AGENT_TIMEOUT_SECONDS = 30
AGENT_RECURSION_LIMIT = 6
RATE_LIMIT_FALLBACK_MESSAGE = (
    "I'm getting too many requests right now. Please wait about 30-60 seconds and try again."
)
TIMEOUT_FALLBACK_MESSAGE = (
    "I'm taking too long to respond right now. Please try again in a few seconds."
)

# ─────────────────────────────────────────
# 3. Short System Prompt
# ─────────────────────────────────────────
SYSTEM_PROMPT = """You are a friendly study assistant for students.
Use the right tool for each request:
- quiz_generator → for quizzes and MCQs
- study_planner → for study schedules
- flashcard_maker → for flashcards
- concept_simplifier → explain simply
- search_wikipedia → for factual topic info
- web_search → for latest/current information
- exam_strategy_coach → for exam prep strategy
- story_based_learning → teach through stories
- study_break_coach → when student needs a break
- progress_tracker → track completed topics and revision needs
- image_explainer → analyze notes/diagrams/circuits from image URLs
- calculator → for maths
- get_current_datetime → for date/time
Be concise, encouraging. This is WhatsApp — keep replies short!"""

# ─────────────────────────────────────────
# 4. Smart Tool Router
# Sends ONLY relevant tools → saves ~80% tokens!
# ─────────────────────────────────────────
def get_relevant_tools(message: str):
    msg = message.lower()

    # Always included — lightweight, always useful
    selected = [get_current_datetime, calculator]

    # Image detection — highest priority
    if msg.startswith("image:"):
        return [image_explainer]

    # Progress tracking
    if any(w in msg for w in ["completed", "finished", "done", "progress", "track", "weak", "revise", "studied"]):
        selected.append(progress_tracker)

    # Web & Wikipedia search
    if any(w in msg for w in ["search", "latest", "news", "recent", "find", "current"]):
        selected.append(web_search)
    if any(w in msg for w in ["wiki", "who is", "what is", "history", "about", "tell me about"]):
        selected.append(search_wikipedia)

    # Quiz
    if any(w in msg for w in ["quiz", "test", "mcq", "question", "ask me"]):
        selected.append(quiz_generator)

    # Study planner
    if any(w in msg for w in ["plan", "schedule", "timetable", "routine", "organise", "organize"]):
        selected.append(study_planner)

    # Flashcards
    if any(w in msg for w in ["flashcard", "card", "memorize", "memorise", "revise", "revision"]):
        selected.append(flashcard_maker)

    # Concept simplifier
    if any(w in msg for w in ["explain", "simple", "simply", "understand", "confusing", "easy", "eli5"]):
        selected.append(concept_simplifier)

    # Story learning
    if any(w in msg for w in ["story", "teach", "narrative", "fun way", "creative"]):
        selected.append(story_based_learning)

    # Exam strategy
    if any(w in msg for w in ["exam", "strategy", "prepare", "syllabus", "days left", "test tomorrow"]):
        selected.append(exam_strategy_coach)

    # Break coach
    if any(w in msg for w in ["break", "tired", "rest", "relax", "exhausted", "stop", "pause"]):
        selected.append(study_break_coach)

    # Fallback — if no keyword matched, send core tools + wikipedia + web
    if len(selected) == 2:
        selected.extend([search_wikipedia, web_search, concept_simplifier])

    return selected


def is_story_style_request(message: str) -> bool:
    msg = message.lower()
    return any(w in msg for w in ["story", "like a story", "narrative", "story way"])


# ─────────────────────────────────────────
# 5. Per-user memory store
# ─────────────────────────────────────────
memory_store = {}
response_cache: Dict[Tuple[str, str], str] = {}


# ─────────────────────────────────────────
# 6. Main Response Function
# ─────────────────────────────────────────
def get_bot_response(message: str, user_id: str) -> str:

    # Direct image handling avoids agent tool-loop delays.
    if message.lower().startswith("image:"):
        response = image_explainer.invoke(message)
        response = str(response).strip()
        if response:
            full_history = memory_store.get(user_id, [])
            full_history.append(HumanMessage(content=message))
            full_history.append(AIMessage(content=response))
            memory_store[user_id] = full_history
            return response

    # Inject user id context for progress tool.
    if any(w in message.lower() for w in ["completed", "finished", "done", "progress", "track", "weak", "revise", "studied"]):
        message = f"{message} [user_id:{user_id}]"

    # Trim very long inputs
    if len(message) > MAX_INPUT_LENGTH:
        message = message[:MAX_INPUT_LENGTH] + "... [trimmed]"

    # Reuse recent identical prompts per user to avoid extra model calls.
    normalized_message = " ".join(message.lower().split())
    cache_key = (user_id, normalized_message)
    if cache_key in response_cache:
        return response_cache[cache_key]

    # Get windowed history
    full_history = memory_store.get(user_id, [])
    recent_history = full_history[-HISTORY_WINDOW:]

    # For story-style requests, avoid multi-tool loops and generate directly.
    if is_story_style_request(message):
        direct_prompt = (
            "Explain this as a fun short story for a student in simple English: "
            f"{message}\n\n"
            "Use this structure exactly:\n"
            "1) Title\n"
            "2) Story (120-180 words, Indian context if possible)\n"
            "3) What we learned (3 bullet points)\n"
            "4) Exam link (2 lines)\n"
            "Keep it clear and engaging."
        )
        direct_messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=direct_prompt)]
        try:
            direct_result = get_llm().invoke(direct_messages)
            response = str(getattr(direct_result, "content", "")).strip()
            if response:
                full_history.append(HumanMessage(content=message))
                full_history.append(AIMessage(content=response))
                memory_store[user_id] = full_history
                response_cache[cache_key] = response
                return response
        except Exception:
            # Fall back to agent flow if direct generation fails.
            pass

    # ✅ Smart routing — only relevant tools loaded
    relevant_tools = get_relevant_tools(message)

    print(f"🛠️  Tools loaded: {[t.name for t in relevant_tools]}")  # helpful debug log

    # Create agent with only relevant tools
    dynamic_agent = create_react_agent(get_llm(), relevant_tools)

    # Build messages
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + recent_history + [HumanMessage(content=message)]

    # Run agent
    print("Starting agent invoke...")
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                dynamic_agent.invoke,
                {"messages": messages},
                {"recursion_limit": AGENT_RECURSION_LIMIT},
            )
            result = future.result(timeout=AGENT_TIMEOUT_SECONDS)
        print("Agent invoke completed.")
    except FutureTimeoutError:
        print("Agent invoke timed out.")
        return TIMEOUT_FALLBACK_MESSAGE
    except Exception as exc:
        error_text = str(exc).lower()
        is_rate_limited = any(
            token in error_text
            for token in ["rate limit", "too many requests", "quota", "429", "resource exhausted"]
        )
        if is_rate_limited:
            return RATE_LIMIT_FALLBACK_MESSAGE
        raise

    raw = result["messages"][-1].content
    if isinstance(raw, list):
      response = " ".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in raw
    ).strip()
    else:
      response = str(raw).strip()
 

    # Save to full history
    full_history.append(HumanMessage(content=message))
    full_history.append(AIMessage(content=response))
    memory_store[user_id] = full_history
    response_cache[cache_key] = response

    return response