# app.py

import traceback
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from dotenv import load_dotenv
load_dotenv()
from bot.agent import get_bot_response



app = Flask(__name__)

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body")
    sender = request.form.get("From")

    print(f"Message from {sender}: {incoming_msg}")

    try:
        response_text = get_bot_response(incoming_msg, sender)
    except Exception as e:
        print("=" * 60)
        print("ERROR OCCURRED:")
        print(traceback.format_exc())   # ← prints full error
        print("=" * 60)
        response_text = "Sorry, I ran into an issue! Please try again. 🙏"

    resp = MessagingResponse()
    resp.message(response_text)
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True, port=5000)