# bot/tools.py

from langchain_core.tools import tool
from datetime import datetime
import os
import re
import importlib
import base64
import wikipedia
import ast
import operator
import requests

# ─────────────────────────────────────────
# TOOL 1: DateTime
# ─────────────────────────────────────────
@tool
def get_current_datetime(query: str) -> str:
    """Use this when the student asks about
    current date, time, or day of the week."""
    now = datetime.now()
    return now.strftime("Today is %A, %d %B %Y. Current time is %I:%M %p.")


# ─────────────────────────────────────────
# TOOL 2: Calculator
# ─────────────────────────────────────────
@tool
def calculator(expression: str) -> str:
    """Use this to solve any mathematical
    calculation or equation. Input must be a
    valid math expression like '234 * 56'."""
    try:
        allowed_operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.Mod: operator.mod,
        }
        def eval_expr(node):
            if isinstance(node, ast.Constant):
                return node.n
            elif isinstance(node, ast.BinOp):
                return allowed_operators[type(node.op)](
                    eval_expr(node.left),
                    eval_expr(node.right)
                )
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
                return -eval_expr(node.operand)
            else:
                raise ValueError("Unsupported operation")
        tree = ast.parse(expression, mode='eval')
        result = eval_expr(tree.body)
        return f"The result of {expression} = {result}"
    except Exception as e:
        return f"Could not calculate: {str(e)}"


# ─────────────────────────────────────────
# TOOL 3: Wikipedia Search
# ─────────────────────────────────────────
@tool
def search_wikipedia(query: str) -> str:
    """Use this to look up factual information
    about any topic, person, event, or concept
    for study purposes."""
    try:
        summary = wikipedia.summary(query, sentences=4)
        return summary
    except wikipedia.DisambiguationError as e:
        return f"Too broad — try being more specific. Options: {e.options[:3]}"
    except wikipedia.PageError:
        return f"No Wikipedia page found for '{query}'."
    except Exception as e:
        return f"Search failed: {str(e)}"


# ─────────────────────────────────────────
# TOOL 4: Quiz Generator 📝
# ─────────────────────────────────────────
@tool
def quiz_generator(topic: str) -> str:
    """Use this when the student asks to be
    quizzed or wants MCQ questions on any topic.
    Input is the topic name."""
    return f"""GENERATE_QUIZ:{topic}
    
Generate 5 multiple choice questions (MCQs) on the topic: {topic}

Format each question EXACTLY like this:
Q1. [Question here]
A) [Option]
B) [Option]
C) [Option]
D) [Option]
✅ Answer: [Correct option letter]

Make questions progressively harder from Q1 to Q5.
Be encouraging and add a motivating message at the end!"""


# ─────────────────────────────────────────
# TOOL 5: Study Planner 🗓️
# ─────────────────────────────────────────
@tool
def study_planner(details: str) -> str:
    """Use this when the student wants a study
    schedule or study plan. Input should include
    subjects and available days/hours."""
    return f"""GENERATE_PLAN:{details}

Create a detailed study schedule based on: {details}

Format the plan like this:
📅 DAY 1 — [Date/Day]
  ⏰ 9:00 AM - 10:30 AM → [Subject/Topic]
  ☕ 10:30 AM - 10:45 AM → Break
  ⏰ 10:45 AM - 12:00 PM → [Subject/Topic]
  ...

Include:
- Short breaks every 90 minutes
- Revision slots
- A motivating tip at the end
Keep it realistic and achievable!"""


# ─────────────────────────────────────────
# TOOL 6: Flashcard Maker 🔤
# ─────────────────────────────────────────
@tool
def flashcard_maker(topic: str) -> str:
    """Use this when the student wants flashcards
    or Q&A cards to memorize a topic.
    Input is the topic name."""
    return f"""GENERATE_FLASHCARDS:{topic}

Create 8 flashcards for the topic: {topic}

Format EXACTLY like this:
🃏 FLASHCARD 1
❓ Q: [Question]
💡 A: [Clear, concise answer]

🃏 FLASHCARD 2
❓ Q: [Question]
💡 A: [Clear, concise answer]

... and so on till Flashcard 8.

Cover the most important concepts.
Keep answers short — max 2 sentences each!"""


# ─────────────────────────────────────────
# TOOL 7: Concept Simplifier 💡
# ─────────────────────────────────────────
@tool
def concept_simplifier(concept: str) -> str:
    """Use this when the student finds a topic
    confusing or asks to explain something simply,
    like they are 10 years old. Input is the concept."""
    return f"""SIMPLIFY:{concept}

Explain '{concept}' as if talking to a 10-year-old.

Structure your explanation like:
🌟 Simple Definition (1-2 sentences max)

🎯 Real Life Example:
[A fun, relatable everyday example]

🔑 Key Points to Remember:
1. [Point 1]
2. [Point 2]
3. [Point 3]

🧠 Memory Trick:
[A fun way to remember this concept]

End with an encouraging message!"""  


# ─────────────────────────────────────────
# TOOL 8: Web Search 🌐
# ─────────────────────────────────────────
from ddgs import DDGS

@tool
def web_search(query: str) -> str:
    """Use this to search the internet for latest
    information, current events, recent discoveries,
    or anything that needs up-to-date data."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                results.append(f"• {r['title']}: {r['body']}")
        if not results:
            return "No results found. Try different keywords."
        return "\n\n".join(results)
    except Exception as e:
        return f"Search failed: {str(e)}"


# ─────────────────────────────────────────
# TOOL 9: Exam Strategy Coach 🎯
# ─────────────────────────────────────────
@tool
def exam_strategy_coach(details: str) -> str:
    """Use this when student mentions an upcoming
    exam and wants preparation strategy or advice
    on what to prioritize. Input includes subject,
    topics and days remaining."""
    return f"""EXAM_STRATEGY:{details}

Create a smart exam strategy for: {details}

Structure your response as:

🎯 EXAM STRATEGY PLAN
━━━━━━━━━━━━━━━━━━━━

⚡ Priority Topics (Study First):
1. [Highest weightage/easiest wins]
2. [Second priority]
3. [Third priority]

📅 Day-by-Day Focus:
Day 1: [What to cover]
Day 2: [What to cover]
...

🚀 Smart Tips:
- [Tip 1 — specific to this subject]
- [Tip 2 — time management]
- [Tip 3 — exam technique]

⚠️ What to Skip if Short on Time:
- [Low priority topics]

💪 Confidence Booster:
[One motivating line personalised to their situation]"""


# ─────────────────────────────────────────
# TOOL 10: Story-Based Learning 📖
# ─────────────────────────────────────────
@tool
def story_based_learning(concept: str) -> str:
    """Use this when student wants to learn a concept
    through a story, narrative, or fun explanation.
    Great for abstract or complex topics."""
    return f"""STORY_LEARNING:{concept}

Teach '{concept}' through an engaging short story.

Structure:
🌟 Title: [Creative story title related to concept]

📖 The Story:
[Write a fun, engaging 150-word story where characters
naturally experience and demonstrate the concept.
Use relatable scenarios — school, cricket, food, etc.]

🔑 What The Story Taught Us:
1. [Key concept 1 from the story]
2. [Key concept 2 from the story]
3. [Key concept 3 from the story]

🎯 Real Exam Connection:
[How this concept appears in actual exam questions]

Remember: Make it fun, Indian context preferred!"""


# ─────────────────────────────────────────
# TOOL 11: Study Break Coach 🧘
# ─────────────────────────────────────────
@tool
def study_break_coach(study_duration: str) -> str:
    """Use this when student says they are tired,
    need a break, have been studying for a long time,
    or asks for break suggestions."""
    return f"""BREAK_COACH:{study_duration}

Student has been studying for: {study_duration}

Respond with:

🧘 BREAK TIME! You've earned it!
━━━━━━━━━━━━━━━━━━━━

⏱️ Recommended Break: [X minutes based on study duration]

🏃 Break Activities (pick one):
1. 👁️ Eye Exercise: [Specific exercise]
2. 🤸 Body Stretch: [Specific stretch]
3. 🌬️ Breathing: [Specific technique]
4. 💧 Hydration tip: [Water/snack suggestion]

🧠 Brain Reset Tip:
[One tip to come back more focused]

⏰ Set a timer! Come back at [time] and we'll tackle:
[Suggest what to study next based on context]

You're doing amazing — keep going! 💪"""


# ─────────────────────────────────────────
# TOOL 12: Progress Tracker 📊
# ─────────────────────────────────────────
progress_store = {}


def _extract_user_id(raw: str) -> str:
    match = re.search(r"\[user_id:(.*?)\]", raw, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "default"


def _extract_topic(raw: str) -> str:
    text = re.sub(r"\[user_id:.*?\]", "", raw, flags=re.IGNORECASE).strip()
    patterns = [
        r"(?:completed|finished|done|studied)\s+(.+)$",
        r"weak\s+(?:in|on)?\s*(.+)$",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip(" .")
    return text.strip(" .")


@tool
def progress_tracker(action_and_data: str) -> str:
    """Use this to track student's study progress.
    Works with explicit command format:
    - add|user_id|topic
    - show|user_id
    - weak|user_id|topic
    - revise|user_id
    Also supports natural language when [user_id:<id>] is present.
    """
    try:
        raw = action_and_data.strip()
        parts = raw.split("|")

        if len(parts) >= 2 and parts[0].strip().lower() in {"add", "show", "weak", "revise"}:
            action = parts[0].strip().lower()
            user_id = parts[1].strip() if len(parts) > 1 else "default"
            topic = parts[2].strip() if len(parts) > 2 else ""
        else:
            lowered = raw.lower()
            user_id = _extract_user_id(raw)
            topic = _extract_topic(raw)
            if any(w in lowered for w in ["show", "progress", "status"]):
                action = "show"
            elif any(w in lowered for w in ["revise", "revision", "what to revise"]):
                action = "revise"
            elif "weak" in lowered:
                action = "weak"
            elif any(w in lowered for w in ["completed", "finished", "done", "studied"]):
                action = "add"
            else:
                action = "show"

        if user_id not in progress_store:
            progress_store[user_id] = {
                "completed": [],
                "weak": [],
                "session_count": 0,
            }

        data = progress_store[user_id]

        if action == "add" and topic:
            if topic not in data["completed"]:
                data["completed"].append(topic)
                data["session_count"] += 1
            return f"""✅ Progress Updated!

📚 Topic Added: {topic}
🏆 Total Topics Completed: {len(data['completed'])}
🔥 Study Sessions: {data['session_count']}

Keep going, you're doing amazing! 💪"""

        if action == "show":
            if not data["completed"]:
                return "📊 No topics tracked yet! Tell me what you've studied and I'll track it for you. 😊"
            topics_list = "\n".join([f"  ✅ {t}" for t in data["completed"]])
            return f"""📊 YOUR STUDY PROGRESS
━━━━━━━━━━━━━━━━━━━━

📚 Completed Topics ({len(data['completed'])}):
{topics_list}

🔥 Total Study Sessions: {data['session_count']}
💪 Keep up the great work!"""

        if action == "weak" and topic:
            if topic not in data["weak"]:
                data["weak"].append(topic)
            return f"⚠️ Added '{topic}' to your weak areas. We'll revise this! 📖"

        if action == "revise":
            if not data["weak"] and not data["completed"]:
                return "📖 Nothing tracked yet! Share what you've studied first."
            revise_topics = data["weak"] if data["weak"] else data["completed"][-3:]
            topics = "\n".join([f"  🔄 {t}" for t in revise_topics])
            return f"""📖 REVISION SUGGESTIONS
━━━━━━━━━━━━━━━━━━━━
{topics}

Start with the first one — 20 mins focused revision! ⏱️"""

        return "I didn't understand that progress command. Try telling me what topic you completed!"
    except Exception as e:
        return f"Progress tracking error: {str(e)}"


# ─────────────────────────────────────────
# TOOL 13: Image Explainer 📸
# ─────────────────────────────────────────
@tool
def image_explainer(image_url: str) -> str:
    """Use this when student sends an image of notes, diagram,
    circuit, graph, or other visual study material.
    Input is the image URL from Twilio.
    """
    try:
        raw_input = image_url.strip()
        user_query = ""

        if "||QUERY:" in raw_input:
            left, right = raw_input.split("||QUERY:", 1)
            raw_input = left.strip()
            user_query = right.strip()

        cleaned_url = raw_input
        if cleaned_url.lower().startswith("image:"):
            cleaned_url = cleaned_url.split(":", 1)[1].strip()

        twilio_sid = os.getenv("TWILIO_ACCOUNT_SID")
        twilio_token = os.getenv("TWILIO_AUTH_TOKEN")

        auth = (twilio_sid, twilio_token) if twilio_sid and twilio_token else None
        img_response = requests.get(cleaned_url, auth=auth, timeout=10)

        if img_response.status_code != 200:
            return "❌ Could not download the image. Please try again."

        img_base64 = base64.b64encode(img_response.content).decode("utf-8")
        content_type = img_response.headers.get("Content-Type", "image/jpeg")
        gemini_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not gemini_api_key:
            return "❌ Image analysis needs GEMINI_API_KEY. Please set it in environment."

        try:
            google_module = importlib.import_module("langchain_google_genai")
            chat_google_class = getattr(google_module, "ChatGoogleGenerativeAI")
        except Exception as exc:
            return (
                "❌ Image analysis needs langchain-google-genai. "
                "Install it with: pip install langchain-google-genai"
            )

        vision_llm = chat_google_class(
            model=os.getenv("GEMINI_VISION_MODEL", "gemini-2.0-flash-lite"),
            google_api_key=gemini_api_key,
            temperature=0.2,
        )

        from langchain_core.messages import HumanMessage

        vision_message = HumanMessage(content=[
            {
                "type": "image_url",
                "image_url": f"data:{content_type};base64,{img_base64}",
            },
            {
                "type": "text",
                "text": f"""You are a study assistant. Analyze this image carefully.
If it contains:
- Notes/text -> summarize key points
- Diagram -> explain what it shows
- Circuit -> explain components and working
- Graph/chart -> explain trend and data
- Math/equation -> explain step by step
- Handwriting -> transcribe and explain

User's specific request (highest priority): {user_query if user_query else 'No custom request provided. Give a useful study-focused analysis.'}

Structure your response as:
IMAGE ANALYSIS
What I see: [type of content]

Explanation:
[Clear detailed explanation]

Key Points:
1. [Point 1]
2. [Point 2]
3. [Point 3]

Study Tip: [One tip related to this content]

If the user asks for calculations (like contribution, split, totals), compute them from values visible in the bill/image only. If something is unclear, state your assumption explicitly."""
            }
        ])

        response = vision_llm.invoke([vision_message])
        output = str(getattr(response, "content", "")).strip()
        if not output:
            return "I could not read enough details from the image. Please send a clearer image or closer crop."

        # Guardrail against made-up numeric answers when OCR extraction is weak.
        suspicious = ["let's say", "assume", "assuming", "example total", "$700"]
        if any(token in output.lower() for token in suspicious):
            return (
                "I could not reliably extract bill values from the image. "
                "Please send a clearer photo (straight angle, good light, closer crop)."
            )

        return output

    except Exception as e:
        return f"Image analysis failed: {str(e)}"