# app.py

import traceback
import threading
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
from bot.agent import get_bot_response
import os

load_dotenv()

app = Flask(__name__)

# Twilio client for sending messages proactively
twilio_client = Client(
    os.getenv("TWILIO_ACCOUNT_SID"),
    os.getenv("TWILIO_AUTH_TOKEN")
)
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")  # e.g. whatsapp:+14155238886

def process_and_reply(incoming_msg, sender, image_url=None):
    """Runs in background thread — processes message and sends reply via Twilio API"""
    try:
        message_to_process = f"IMAGE:{image_url}||QUERY:{incoming_msg}" if image_url else incoming_msg
        if image_url:
            print(f"Processing image request for {sender}")
        response_text = get_bot_response(message_to_process, sender)
    except Exception as e:
        print("=" * 60)
        print("ERROR OCCURRED:")
        print(traceback.format_exc())
        print("=" * 60)
        error_str = str(e)
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            response_text = "⏳ Taking a short break! API limit reached. Try again in a few minutes 🙏"
        else:
            response_text = "Sorry, I ran into an issue! Please try again 🙏"

    # Send reply via Twilio REST API (not TwiML)
    twilio_client.messages.create(
        from_=TWILIO_WHATSAPP_NUMBER,
        to=sender,
        body=response_text
    )

@app.route("/whatsapp", methods=["POST"])
def whatsapp_reply():
    incoming_msg = request.form.get("Body", "").strip()
    sender = request.form.get("From")
    num_media = int(request.form.get("NumMedia", 0))

    image_url = None
    if num_media > 0:
        image_url = request.form.get("MediaUrl0")
        print(f"Image received from {sender}: {image_url}")
    else:
        print(f"Message from {sender}: {incoming_msg}")

    # ✅ Immediately start background thread
    thread = threading.Thread(
        target=process_and_reply,
        args=(incoming_msg, sender, image_url)
    )
    thread.start()

    # ✅ Return empty response to Twilio instantly (within 15 secs)
    return str(MessagingResponse())

if __name__ == "__main__":
    app.run(debug=True, port=5000)