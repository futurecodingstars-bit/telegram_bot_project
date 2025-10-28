import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import os
import sqlite3

# Set up basic logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# REPLACE THIS WITH YOUR ACTUAL BOT TOKEN from BotFather
TOKEN = "YOUR_TOKEN"
DATABASE_NAME = 'bot_data.db'
 
def init_db():
    """Initializes the SQLite database and creates the users table."""
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                preference TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hello {user.mention_html()}! Welcome!"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles all non-command text messages."""
    await update.message.reply_text(f"I heard you say: {update.message.text}")


async def send_meme(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a local meme image."""
    if os.path.exists("meme.jpg"): 
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open('meme.jpg', 'rb'),
                caption="Hereʼs your Python-powered meme!"
            )
        except Exception:
            await update.message.reply_text("Couldnʼt send the meme. Check the file path.")
    else:
        await update.message.reply_text("Error: meme.jpg file not found!")

async def acknowledge_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles incoming photos (memes)."""
    await update.message.reply_text("Nice meme! Iʼll process that image soon.")


app = Application.builder().token(TOKEN).build()
# Run the bot
logger.info("Bot starting...")

async def set_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sets a user preference with validation and database persistence."""
    user_id = update.effective_user.id
    
    if not context.args:
        # Validation
        await update.message.reply_text("Must provide a preference. Usage: /set_pref <value>")
        return
        
    preference = " ".join(context.args).strip()
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        # SQL INSERT OR REPLACE statement for persistence
        cursor.execute(
            "INSERT OR REPLACE INTO users (id, preference) VALUES (?, ?)", 
            (user_id, preference)
        )
        conn.commit()
        conn.close()
        
        # Basic State Management
        context.user_data['preference'] = preference
        
        await update.message.reply_text(f"Preference saved: {preference}")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        await update.message.reply_text("Sorry, ran into a database error while saving.")

async def get_preference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Retrieves and displays the userʼs saved preference."""
    user_id = update.effective_user.id
    
    # 1. Check transient memory (user_data) first
    preference = context.user_data.get('preference')
    if preference:
        await update.message.reply_text(f"From memory: Your preference is: {preference}")
        return
        
    # 2. If not in memory, check the persistent database
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        
        cursor.execute("SELECT preference FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            preference = result[0]
            context.user_data['preference'] = preference
            await update.message.reply_text(f"From the DB: Your preference is: {preference}")
        else:
            await update.message.reply_text("You havenʼt set a preference yet. Use /set_pref!")
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        await update.message.reply_text("Sorry, ran into a database error while retrieving.")


def main() -> None:
    """Starts the bot application."""
    app = Application.builder().token(TOKEN).build()
    # Run the bot
    logger.info("Bot starting...")

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("meme", send_meme))
    app.add_handler(MessageHandler(filters.PHOTO, acknowledge_photo))
    app.add_handler(CommandHandler("set_pref", set_preference))
    app.add_handler(CommandHandler("get_pref", get_preference)) 
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()