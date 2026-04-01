# bot/tools.py

from langchain_core.tools import tool
from datetime import datetime
import wikipedia
import ast
import operator

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