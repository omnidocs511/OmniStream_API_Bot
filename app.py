import os
import threading
import asyncio
from flask import Flask, jsonify, request
from flask_cors import CORS
from data import get_movie_qualities
import bot # This must import the 'application' variable from your bot.py

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "OmniStream API & Bot is Running!"

@app.route('/get-links')
def links():
    url = request.args.get('url')
    return jsonify(get_movie_qualities(url))

def run_bot():
    """Start the bot polling."""
    # We use the 'application' object defined in bot.py
    print("Bot thread started...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
        
    bot.application.run_polling(close_loop=False, stop_signals=None)

if __name__ == "__main__":
    # Start Bot in background thread
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    # Start Flask on the port Render provides
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
