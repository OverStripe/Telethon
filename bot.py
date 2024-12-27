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

AUTHORIZED_USER = "7222795580"  # Only this phone number can approve users
APPROVED_USERS_FILE = "approved_users.txt"
BOT_TOKEN = "8022539978:AAFCZWIxEMrN5RLIs1inv0EmSsZi9UBs1xU"
ADMIN_CHAT_ID = "7222795580"  # Chat ID to notify when the bot starts

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------

def display_step(step_message):
    """Stylish step display."""
    print(f"\n❖ {step_message}\n" + "-" * len(step_message))


def cool_input(prompt):
    """Stylish input prompt."""
    return input(f"❖ {prompt}: ").strip()


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
        return f"❖ User {user_id} is already approved."
    with open(APPROVED_USERS_FILE, 'a') as file:
        file.write(f"{user_id}\n")
    return f"❖ User {user_id} approved successfully."


def is_user_approved(user_id):
    """Check if a user is approved."""
    approved_users = load_approved_users()
    return user_id in approved_users


def authorize_user():
    """Authorize the user before proceeding."""
    phone_number = cool_input("Enter your phone number for authorization (with country code)")
    if phone_number != AUTHORIZED_USER and not is_user_approved(phone_number):
        print("❖ [Error] You are not authorized. Please contact the admin: 7222795580")
        exit()

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
            print(f"❖ Sending OTP to {phone_number}...")
            client.send_code_request(phone_number)
            
            otp_code = cool_input(f"Enter OTP for {phone_number}")
            try:
                client.sign_in(phone_number, otp_code)
            except SessionPasswordNeededError:
                password = cool_input("Enter your Two-Step Verification password")
                client.sign_in(password=password)
        
        user = client.get_me()
        print(f"❖ Session for {phone_number} created successfully! (@{user.username if user.username else user.first_name})")
        client.disconnect()
        return True
    
    except Exception as e:
        print(f"❖ [Error] Failed to create session for {phone_number}: {e}")
        return False


def generate_bot_session(bot_token):
    """Generate a single bot session."""
    session_name = f"bot_session_{bot_token.split(':')[0]}"
    client = TelegramClient(session_name, api_id=0, api_hash='')
    
    try:
        client.start(bot_token=bot_token)
        print(f"❖ Bot session created successfully for token: {bot_token}")
        client.disconnect()
        return True
    
    except Exception as e:
        print(f"❖ [Error] Failed to create bot session: {e}")
        return False


# -------------------------------
# BULK SESSION FUNCTIONS
# -------------------------------

def bulk_generate_user_sessions():
    display_step("Bulk User Session Generation")
    api_id = cool_input("Enter your API ID")
    api_hash = cool_input("Enter your API HASH")
    
    phone_numbers_file = cool_input("Enter the path to your phone numbers file (one per line)")
    
    if not os.path.exists(phone_numbers_file):
        print("❖ [Error] File not found. Please check the path.")
        return
    
    with open(phone_numbers_file, 'r') as file:
        phone_numbers = [line.strip() for line in file.readlines() if line.strip()]
    
    success_count = 0
    for phone_number in phone_numbers:
        print(f"\n❖ Processing phone number: {phone_number}")
        if generate_user_session(int(api_id), api_hash, phone_number):
            success_count += 1
        time.sleep(2)
    
    print(f"\n❖ Bulk User Session Generation Completed: {success_count}/{len(phone_numbers)} sessions created successfully.")


# -------------------------------
# TELEGRAM BOT COMMANDS
# -------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command for the bot."""
    await update.message.reply_text("❖ Welcome to Telegram Session Manager Bot!")


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Approve a user via bot."""
    if str(update.effective_user.id) != AUTHORIZED_USER:
        await update.message.reply_text("❖ [Error] You are not authorized to approve users.")
        return
    
    if len(context.args) != 1:
        await update.message.reply_text("❖ Usage: /approve <user_id>")
        return
    
    user_id = context.args[0]
    result = approve_user(user_id)
    await update.message.reply_text(result)


async def list_approved(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all approved users."""
    users = load_approved_users()
    if users:
        await update.message.reply_text("❖ Approved Users:\n" + "\n".join(users))
    else:
        await update.message.reply_text("❖ No approved users found.")


def send_start_notification():
    """Notify the admin when the bot starts."""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data={"chat_id": ADMIN_CHAT_ID, "text": "❖ Telegram Session Manager Bot started successfully!"}
        )
    except Exception as e:
        print(f"❖ [Error] Failed to send start notification: {e}")


def run_bot():
    """Run the Telegram Bot."""
    send_start_notification()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("list_approved", list_approved))
    print("❖ Bot is running... Use commands like /approve, /list_approved.")
    application.run_polling()


if __name__ == '__main__':
    run_bot()
