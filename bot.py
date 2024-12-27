from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import time
import os
import requests

# -------------------------------
# CONFIGURATION
# -------------------------------

AUTHORIZED_USER = "7222795580"  # Only this user can manage approvals
APPROVED_USERS_FILE = "approved_users.txt"
BOT_TOKEN = "8022539978:AAH_95yhC1RxQS8elCyvYsjdea01ZfUwQKs"
ADMIN_CHAT_ID = "7222795580"  # Chat ID to notify admin on startup

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------

def display_step(step_message):
    """Stylish step display."""
    print(f"\n🌟 {step_message}\n" + "━" * len(step_message))


def cool_input(prompt):
    """Stylish input prompt."""
    return input(f"🟢 {prompt}: ").strip()


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
        return f"✅ User {user_id} is already approved."
    with open(APPROVED_USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")
    return f"✅ User {user_id} approved successfully."


def is_user_approved(user_id):
    """Check if a user is approved."""
    approved_users = load_approved_users()
    return user_id in approved_users


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
            print(f"📲 Sending OTP to {phone_number}...")
            client.send_code_request(phone_number)
            
            otp_code = cool_input(f"🔑 Enter OTP for {phone_number}")
            try:
                client.sign_in(phone_number, otp_code)
            except SessionPasswordNeededError:
                password = cool_input("🔒 Enter your Two-Step Verification password")
                client.sign_in(password=password)
        
        user = client.get_me()
        print(f"✅ Session for {phone_number} created successfully! (@{user.username if user.username else user.first_name})")
        client.disconnect()
        return True
    
    except Exception as e:
        print(f"❌ Failed to create session for {phone_number}: {e}")
        return False


def bulk_generate_user_sessions(api_id, api_hash, file_path):
    """Generate multiple user sessions."""
    if not os.path.exists(file_path):
        return "❌ [Error] File not found. Please check the path."
    
    with open(file_path, 'r') as file:
        phone_numbers = [line.strip() for line in file.readlines() if line.strip()]
    
    success_count = 0
    for phone_number in phone_numbers:
        print(f"\n📲 Processing phone number: {phone_number}")
        if generate_user_session(api_id, api_hash, phone_number):
            success_count += 1
        time.sleep(2)
    
    return f"✅ Bulk User Session Generation Completed: {success_count}/{len(phone_numbers)} sessions created successfully."


# -------------------------------
# TELEGRAM BOT COMMANDS
# -------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command for the bot."""
    await update.message.reply_text(
        "🚀 **Welcome to Telegram Session Manager Bot!**\n"
        "Type `/help` to see all commands."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all commands."""
    commands = """
📚 **Available Commands:**
🟢 `/start` → Start the bot.
🟢 `/ap <user_id>` → Approve a user (Admin Only).
🟢 `/la` → List approved users (Admin Only).
🟢 `/su <api_id> <api_hash> <phone>` → Single User Session.
🟢 `/bu <api_id> <api_hash> <file_path>` → Bulk User Sessions.
"""
    await update.message.reply_text(commands)


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a user via bot."""
    if str(update.effective_user.id) != AUTHORIZED_USER:
        await update.message.reply_text("❌ [Error] You are not authorized to approve users.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("❌ Usage: /ap <user_id>")
        return
    
    user_id = context.args[0]
    result = approve_user(user_id)
    await update.message.reply_text(result)


async def list_approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all approved users."""
    users = load_approved_users()
    if users:
        await update.message.reply_text("✅ Approved Users:\n" + "\n".join(users))
    else:
        await update.message.reply_text("❌ No approved users found.")


async def single_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate single user session."""
    if len(context.args) != 3:
        await update.message.reply_text("❌ Usage: /su <api_id> <api_hash> <phone>")
        return
    
    api_id, api_hash, phone = context.args
    result = generate_user_session(api_id, api_hash, phone)
    await update.message.reply_text("✅ Session generated successfully!" if result else "❌ Session generation failed.")


async def bulk_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate bulk user sessions."""
    if len(context.args) != 3:
        await update.message.reply_text("❌ Usage: /bu <api_id> <api_hash> <file_path>")
        return
    
    api_id, api_hash, file_path = context.args
    result = bulk_generate_user_sessions(api_id, api_hash, file_path)
    await update.message.reply_text(result)


# -------------------------------
# NOTIFICATIONS
# -------------------------------

def send_start_notification():
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": ADMIN_CHAT_ID, "text": "✅ Bot started successfully!"}
        )
    except Exception as e:
        print(f"❌ Failed to send start notification: {e}")


def run_bot():
    send_start_notification()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ap", approve))
    app.add_handler(CommandHandler("la", list_approved))
    app.add_handler(CommandHandler("su", single_user))
    app.add_handler(CommandHandler("bu", bulk_user))
    print("🚀 Bot is running with enhanced UI!")
    app.run_polling()


# -------------------------------
# MAIN
# -------------------------------

if __name__ == '__main__':
    run_bot()
