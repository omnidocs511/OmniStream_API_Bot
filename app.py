import os
import asyncio
import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from data import get_movie_qualities
import bot  # This imports your bot.py logic

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    # Cron-job.org will hit this URL to keep the app awake
    return "OmniStream System is Online!"

@app.route('/get-links')
def links():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    return jsonify(get_movie_qualities(url))

def run_bot():
    """Function to initialize and run the telegram bot."""
    print("Starting Telegram Bot...")
    # We create a new event loop for the background thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Import the application object from bot.py
    # We will modify bot.py slightly to make this easier
    from bot import application
    bot.application.run_polling(close_loop=False)

if __name__ == "__main__":
    # 1. Start the Bot in a background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # 2. Start Flask (Render requires this to be on 0.0.0.0)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
