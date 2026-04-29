import logging
import urllib.parse
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from data import search_hdhub

TOKEN = '8646555096:AAFovFtcJmAr0BsQVIEJzdT0jYQENUfDwGY'
ITEMS_PER_PAGE = 5

# --- AUTO-DELETE LOGIC ---
async def delete_message_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    try:
        await context.bot.delete_message(chat_id=job.chat_id, message_id=job.data)
    except:
        pass

def schedule_delete(context, chat_id, message_id):
    context.job_queue.run_once(delete_message_job, when=20, chat_id=chat_id, data=message_id)

# --- BOT HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sent_msg = await update.message.reply_text("🔍 *OmniStream Search*\nSend movie name to begin.", parse_mode='Markdown')
    schedule_delete(context, update.effective_chat.id, sent_msg.message_id)

async def send_results_page(update_or_query, context, page):
    results = context.user_data.get('search_results', [])
    start_idx = page * ITEMS_PER_PAGE
    current_batch = results[start_idx:start_idx + ITEMS_PER_PAGE]
    total_pages = (len(results) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    text = f"🍿 *Results (Page {page + 1}/{total_pages})*\n\n"
    keyboard = []

    for i, movie in enumerate(current_batch):
        safe_title = urllib.parse.quote(movie['title'])
        safe_url = urllib.parse.quote(movie['link']) 
        
        # ✅ UPDATE THIS to your live Vercel/GitHub Pages URL
        live_site_url = "http://127.0.0.1:5500/OmniStream" 
        web_portal_url = f"{live_site_url}/index.html?title={safe_title}&url={safe_url}"
        
        text += f"{start_idx + i + 1}. {movie['title']}\n\n"
        keyboard.append([InlineKeyboardButton(f"🚀 Download {start_idx + i + 1}", url=web_portal_url)])

    nav = []
    if page > 0: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"listpage_{page-1}"))
    if page < total_pages - 1: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"listpage_{page+1}"))
    if nav: keyboard.append(nav)

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if isinstance(update_or_query, Update):
        sent_results = await update_or_query.message.reply_text(text, parse_mode='Markdown', reply_markup=reply_markup)

        notice_text = "⚠️ *Notice:*\nThis message will auto-delete in 15 minutes for privacy."
        sent_notice = await update_or_query.message.reply_text(notice_text, parse_mode='Markdown')

        schedule_delete(context, update_or_query.effective_chat.id, sent_results.message_id)
        schedule_delete(context, update_or_query.effective_chat.id, sent_notice.message_id)
        schedule_delete(context, update_or_query.effective_chat.id, update_or_query.message.message_id)
    else:
        await update_or_query.edit_message_text(text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text
    msg = await update.message.reply_text("🔎 Searching...")
    results = search_hdhub(query)
    
    if not results or "error" in results:
        err_msg = await msg.edit_text("❌ No results found.")
        schedule_delete(context, update.effective_chat.id, err_msg.message_id)
        return
    
    context.user_data['search_results'] = results
    await msg.delete()
    await send_results_page(update, context, 0)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data.startswith("listpage_"):
        await send_results_page(query, context, int(query.data.split("_")[1]))

# Create the application instance to be used by app.py
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
application.add_handler(CallbackQueryHandler(button_handler))
