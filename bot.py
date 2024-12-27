from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import time
import os
import requests

# -------------------------------
# CONFIGURATION
# -------------------------------

AUTHORIZED_USER = "7222795580"  # Admin User
APPROVED_USERS_FILE = "approved_users.txt"
BOT_TOKEN = "8022539978:AAHWDBgrQ8N9ZpmOPNTFEXoydTqpn8M5W2k"
ADMIN_CHAT_ID = "7222795580"  # For Notifications

# Conversation States
API_ID, API_HASH, PHONE_NUMBER, OTP, PASSWORD = range(5)

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------

def cool_ui(text: str):
    """Return text wrapped in a clean UI."""
    return f"🟢 *{text}*\n━" * len(text)


def load_approved_users():
    """Load approved users from a file."""
    if not os.path.exists(APPROVED_USERS_FILE):
        with open(APPROVED_USERS_FILE, 'w') as f:
            f.write("")
    with open(APPROVED_USERS_FILE, 'r') as file:
        return [line.strip() for line in file.readlines() if line.strip()]


def approve_user(user_id):
    """Approve a user."""
    approved_users = load_approved_users()
    if user_id in approved_users:
        return "✅ User already approved."
    with open(APPROVED_USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")
    return "✅ User approved successfully."


def is_user_approved(user_id):
    """Check if a user is approved."""
    return user_id in load_approved_users()


def notify_admin(message):
    """Send notifications to admin."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": ADMIN_CHAT_ID, "text": f"🔔 {message}"}
        )
    except Exception as e:
        print(f"❌ Admin notification failed: {e}")


# -------------------------------
# SESSION GENERATION FUNCTIONS
# -------------------------------

def generate_user_session(api_id, api_hash, phone_number):
    """Generate a single user session."""
    session_name = f"session_{phone_number.replace('+', '')}"
    client = TelegramClient(session_name, api_id, api_hash)
    
    try:
        client.connect()
        
        if not client.is_user_authorized():
            print("📲 Sending OTP...")
            client.send_code_request(phone_number)
            
            otp_code = cool_input("🔑 Enter OTP:")
            try:
                client.sign_in(phone_number, otp_code)
            except SessionPasswordNeededError:
                password = cool_input("🔒 Enter your Two-Step Verification password:")
                client.sign_in(password=password)
        
        user = client.get_me()
        print(f"✅ Session created successfully for {user.first_name}")
        client.disconnect()
        return True
    
    except Exception as e:
        error_message = f"❌ Session failed: {e}"
        notify_admin(error_message)
        print(error_message)
        return False


# -------------------------------
# TELEGRAM BOT COMMANDS
# -------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Command."""
    await update.message.reply_text(
        cool_ui("Welcome to Telegram Session Manager Bot! 🎩✨\nType /help to view commands.")
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help Command."""
    commands = cool_ui("""
Available Commands:
🟢 /start → Start the bot
🟢 /ap <user_id> → Approve User (Admin Only)
🟢 /la → List Approved Users (Admin Only)
🟢 /su → Generate Single User Session (Interactive)
🟢 /bu → Generate Bulk User Sessions
🟢 /cancel → Cancel Current Process
    """)
    await update.message.reply_text(commands)


# -------------------------------
# SINGLE USER SESSION HANDLER
# -------------------------------

async def start_single_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Single User Session Conversation."""
    await update.message.reply_text(cool_ui("Step 1: Enter your API ID:"))
    return API_ID


async def handle_api_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['api_id'] = update.message.text
    await update.message.reply_text(cool_ui("Step 2: Enter your API HASH:"))
    return API_HASH


async def handle_api_hash(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['api_hash'] = update.message.text
    await update.message.reply_text(cool_ui("Step 3: Enter your Phone Number (e.g., +1234567890):"))
    return PHONE_NUMBER


async def handle_phone_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['phone_number'] = update.message.text
    await update.message.reply_text(cool_ui("📲 Sending OTP... Please wait."))
    return OTP


async def handle_otp(update: Update, context: ContextTypes.DEFAULT_TYPE):
    otp = update.message.text
    try:
        session_result = generate_user_session(
            int(context.user_data['api_id']),
            context.user_data['api_hash'],
            context.user_data['phone_number']
        )
        if session_result:
            await update.message.reply_text(cool_ui("✅ Session created successfully!"))
        else:
            await update.message.reply_text(cool_ui("❌ Session generation failed."))
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the process."""
    await update.message.reply_text(cool_ui("❌ Session creation cancelled."))
    return ConversationHandler.END


# -------------------------------
# RUN BOT
# -------------------------------

def run_bot():
    notify_admin("✅ Bot started successfully!")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("su", start_single_session)],
        states={
            API_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_api_id)],
            API_HASH: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_api_hash)],
            PHONE_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_phone_number)],
            OTP: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_otp)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    
    print("🚀 Bot is running with a Cool UI!")
    app.run_polling()


if __name__ == '__main__':
    run_bot()
