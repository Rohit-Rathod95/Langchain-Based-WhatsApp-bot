# 📚 LangChain WhatsApp Study Assistant Bot

A powerful AI-powered WhatsApp bot built with LangChain, Google Gemini, and Twilio that acts as a personal study assistant for students. The bot can explain concepts, generate quizzes, create flashcards, track progress, analyze images of notes, and much more — all through WhatsApp!

---

## 🌟 Features

| Feature | Description |
|---|---|
| 📝 Quiz Generator | Creates MCQ quizzes on any topic |
| 🗓️ Study Planner | Makes personalized daily study schedules |
| 🔤 Flashcard Maker | Generates Q&A flashcards for memorization |
| 💡 Concept Simplifier | Explains complex topics like you're 10 |
| 📖 Story-Based Learning | Teaches concepts through fun stories |
| 🎯 Exam Strategy Coach | Creates priority-based exam prep plans |
| 🧘 Study Break Coach | Suggests break activities and exercises |
| 📊 Progress Tracker | Tracks completed topics and weak areas |
| 📸 Image Explainer | Analyzes photos of notes and diagrams |
| 🌐 Web Search | Searches internet for latest information |
| 🔍 Wikipedia Search | Looks up factual information |
| 🔢 Calculator | Solves mathematical expressions |
| 📅 DateTime | Provides current date and time |

---

## 🏗️ Architecture

```
User (WhatsApp)
      │
      ▼
Twilio API          ← Receives & sends WhatsApp messages
      │
      ▼
Flask Server        ← Python webhook (app.py)
      │
      ▼
Background Thread   ← Prevents Twilio timeout
      │
      ▼
Smart Tool Router   ← Selects only relevant tools (saves tokens)
      │
      ▼
LangGraph Agent     ← ReAct loop: Think → Act → Observe
      │
   ┌──┴──────────────────────────────┐
   ▼                                 ▼
Tools (DuckDuckGo, Wikipedia,    Google Gemini
  Calculator, Quiz, etc.)        gemini-2.0-flash-lite
      │                                 │
      └──────────────┬──────────────────┘
                     ▼
            Per-User Memory
         (Windowed Chat History)
                     │
                     ▼
            Twilio REST API     ← Sends reply back
                     │
                     ▼
          User (WhatsApp) ✅
```

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| **Python** | 3.10+ | Core language |
| **LangChain** | 1.x | Agent orchestration framework |
| **LangGraph** | Latest | ReAct agent execution |
| **Google Gemini** | gemini-2.0-flash | LLM brain |
| **Flask** | Latest | Web server / webhook receiver |
| **Twilio** | Latest | WhatsApp messaging API |
| **DuckDuckGo Search** | Latest | Free web search |
| **Wikipedia** | Latest | Factual information lookup |
| **ngrok** | 3.x | Local tunnel for development |

---

## 📁 Project Structure

```
study-bot/
│
├── app.py                  ← Flask server entry point
│
├── bot/
│   ├── agent.py            ← LangGraph agent + smart tool router
│   ├── tools.py            ← All 13 tool definitions
│   └── chain.py            ← Phase 1 & 2 reference (basic chain)
│
├── .env                    ← API keys and secrets (never commit!)
├── requirements.txt        ← Python dependencies
└── venv/                   ← Virtual environment
```

---

## ⚙️ How It Works

### 1. Message Flow

When you send a WhatsApp message:

1. **Twilio** receives the message and POSTs it to your Flask webhook
2. **Flask** immediately spawns a background thread and returns 200 OK to Twilio (prevents 15s timeout)
3. The **background thread** calls `get_bot_response(message, user_id)`
4. The **Smart Tool Router** analyzes keywords to select only relevant tools
5. The **LangGraph Agent** runs the ReAct loop:
   - **Thinks** about what tool to use
   - **Acts** by calling the tool
   - **Observes** the result
   - **Responds** with a final answer
6. **Per-user memory** is updated with the new exchange
7. **Twilio REST API** sends the reply back to WhatsApp

### 2. Smart Tool Router

Instead of sending all 13 tools to Gemini every request (expensive!), we only send the relevant ones based on message keywords:

```python
"quiz me on..."        → quiz_generator
"search for..."        → web_search
"I'm tired..."         → study_break_coach
"make flashcards..."   → flashcard_maker
[photo sent]           → image_explainer only
```

This saves ~80% of tokens per request, making quota last much longer.

### 3. Memory System

Each user gets their own conversation history stored in a dictionary keyed by their WhatsApp number:

```python
memory_store = {
    "whatsapp:+91XXXXXXXXXX": [last 6 messages],
    "whatsapp:+91YYYYYYYYYY": [last 6 messages],
}
```

Only the last 6 messages (3 exchanges) are sent to Gemini — this is the **windowing technique** that prevents history from growing forever and exhausting quota.

### 4. Image Analysis

When you send a photo:
1. Twilio provides the image URL with the webhook POST
2. Flask detects `NumMedia > 0` and extracts `MediaUrl0`
3. The image is downloaded using Twilio credentials (auth required)
4. Converted to base64 and sent to **Gemini Vision**
5. Gemini analyzes the image and returns an explanation

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.10 or higher
- A [Twilio](https://twilio.com) account (free trial works)
- A [Google AI Studio](https://aistudio.google.com) account (free)
- [ngrok](https://ngrok.com) installed (for local development)

### Step 1 — Clone & Setup

```bash
git clone https://github.com/yourusername/study-bot.git
cd study-bot
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Step 2 — Install Dependencies

```bash
pip install langchain langchain-google-genai langchain-community langgraph flask twilio python-dotenv wikipedia duckduckgo-search requests
```

### Step 3 — Configure Environment Variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your_gemini_api_key
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

Where to find these:
- `GEMINI_API_KEY` → [Google AI Studio](https://aistudio.google.com/apikey) → Create API Key in **new project**
- `TWILIO_ACCOUNT_SID` & `TWILIO_AUTH_TOKEN` → [Twilio Console](https://console.twilio.com) homepage
- `TWILIO_WHATSAPP_NUMBER` → Twilio Console → Messaging → WhatsApp Sandbox

### Step 4 — Run the Server

```bash
python app.py
```

### Step 5 — Start ngrok

In a new terminal:

```bash
ngrok http 5000
```

Copy the `https://...ngrok-free.app` URL.

### Step 6 — Configure Twilio Webhook

1. Go to Twilio Console → Messaging → Try it out → Send a WhatsApp message → Sandbox Settings
2. In **"When a message comes in"** paste:
   ```
   https://your-ngrok-url.ngrok-free.app/whatsapp
   ```
3. Set method to **HTTP POST**
4. Click **Save**

### Step 7 — Join Sandbox & Test

Send `join <your-sandbox-keyword>` to the Twilio WhatsApp number, then start chatting!

---

## 💬 Usage Examples

```
📝 Quiz:        "Quiz me on Newton's laws"
🗓️ Plan:        "I have Physics exam in 3 days, chapters 1,2,3"
🔤 Flashcards:  "Make flashcards on photosynthesis"
💡 Simplify:    "Explain quantum physics simply"
📖 Story:       "Teach me gravity through a story"
🎯 Strategy:    "I have Chemistry exam tomorrow"
🧘 Break:       "I've been studying for 2 hours, need a break"
📊 Track:       "I completed Newton's Laws today"
📸 Image:       [Send a photo of notes or diagram]
🌐 Search:      "Search latest discoveries in space 2025"
🔢 Math:        "What is 15% of 850?"
```

---

## 🧠 Key LangChain Concepts Used

### Chains (Phase 1 & 2)
A chain is a linear pipeline: `Prompt Template → LLM → Output Parser`. Used in the initial version before agents were added. Built using **LCEL (LangChain Expression Language)** with the `|` pipe operator.

### Memory (Phase 2)
Conversation history is stored per-user and injected into every prompt. Uses `HumanMessage` and `AIMessage` objects from LangChain core. Windowed to last 6 messages to save tokens.

### Agents (Phase 3+)
Built with **LangGraph's `create_react_agent`**. The agent follows the ReAct pattern:
- **Reason** about what to do
- **Act** using a tool
- **Observe** the result
- Repeat until a final answer is reached

### Tools
Each tool is a Python function decorated with `@tool`. LangChain uses the function's docstring to help the agent decide when to use it.

---

## ⚠️ Important Notes

### Twilio Sandbox Expiry
The sandbox connection expires every **72 hours**. You must rejoin by sending:
```
join <your-sandbox-keyword>
```

### ngrok URL Changes
Every time you restart ngrok (free plan), the URL changes. You must update the Twilio webhook URL each time.

### Startup Order
Always start in this order:
1. `python app.py` → Flask server
2. `ngrok http 5000` → tunnel
3. Update Twilio if ngrok URL changed
4. Rejoin sandbox if 72 hours passed

### API Quota
Google Gemini free tier gives **1,500 requests/day** for `gemini-2.0-flash-lite`. The smart tool router and memory windowing reduce usage by ~80%.

If quota is exhausted, create a new API key in a **new Google project** (not existing project).

---

## 🔮 Future Improvements

- [ ] Deploy to Railway/Render for 24/7 availability
- [ ] Persistent memory using Redis or SQLite
- [ ] Support for voice messages
- [ ] Multi-language support
- [ ] Student performance analytics dashboard
- [ ] PDF notes upload and Q&A

---

## 📄 License

MIT License — free to use, modify and distribute.

---

## 🙏 Acknowledgements

- [LangChain](https://langchain.com) — Agent orchestration
- [Google Gemini](https://ai.google.dev) — LLM and Vision
- [Twilio](https://twilio.com) — WhatsApp API
- [LangGraph](https://langchain-ai.github.io/langgraph) — ReAct agent execution
