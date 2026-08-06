import logging
import sqlite3
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8852763495:AAHMR8P11_XausN6e-8sdCqWjvmr0dNRqiE"               # <-- Step 1: Yahan apna Bot Token paste karein
QR_FILE_ID = "https://i.postimg.cc/2SxbQwYd/pr.jpg" # Aapka QR Code Image URL

ADMIN_ID = 8678259543                           
PREMIUM_CHANNEL_ID = -1004395881961            
PROOF_CHANNEL_ID = -1004344349433               
PROOF_CHANNEL_URL = "https://t.me/proofpremiumm" 
SUPPORT_USERNAME = "https://t.me/Shreya153_bot" 

# Welcome Video Direct URL (Added)
WELCOME_VIDEO_URL = "https://files.catbox.moe/436zox.mp4" 

# Logging Setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== DATABASE SETUP ====================
def init_db():
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    # Users table for Premium Subscriptions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            join_date TIMESTAMP,
            expiry_date TIMESTAMP,
            status TEXT
        )
    ''')
    # Bot Total Users table for tracking & broadcasting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_seen TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ==================== MAIN KEYBOARD ====================
def main_menu():
    keyboard = [
        [InlineKeyboardButton("💎 49Rs Exclusive Premium", callback_data='buy_premium')],
        [InlineKeyboardButton("📊 Proofs", url=PROOF_CHANNEL_URL)],
        [InlineKeyboardButton("📞 Contact & Support", url=SUPPORT_USERNAME)]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== BOT HANDLERS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Save user to database
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO bot_users (user_id, username, first_seen) VALUES (?, ?, ?)',
                   (user.id, user.username or "No Username", datetime.datetime.now()))
    conn.commit()
    conn.close()

    welcome_msg = (
        f"👋 **Hello {user.first_name}!**\n\n"
        "Welcome to Premium Access Bot!\n"
        "Niche diye gaye buttons ka use karke aap Premium Access le sakte hain."
    )
    
    # Welcome Video bhejega
    if WELCOME_VIDEO_URL != "":
        try:
            await update.message.reply_video(video=WELCOME_VIDEO_URL, caption=welcome_msg, parse_mode='Markdown', reply_markup=main_menu())
            return
        except Exception as e:
            logging.error(f"Error sending video: {e}")
            
    await update.message.reply_text(welcome_msg, parse_mode='Markdown', reply_markup=main_menu())

# ==================== ADMIN PANEL & BROADCAST ====================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Yeh command sirf Admin ke liye hai!")
        return

    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM bot_users')
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'active'")
    active_premiums = cursor.fetchone()[0]
    conn.close()

    admin_text = (
        "👑 **ADMIN CONTROL PANEL** 👑\n\n"
        f"📊 **Total Users in Bot:** `{total_users}`\n"
        f"💎 **Active Premium Users:** `{active_premiums}`\n\n"
        "📢 **Broadcast karne ke liye:**\n"
        "`/broadcast [Aapka Message]` type karein.\n"
        "*(Example: /broadcast Hello dosto!)*"
    )
    await update.message.reply_text(admin_text, parse_mode='Markdown')

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("⚠️ Kripya message bhi likhein!\nExample: `/broadcast Hello everyone!`", parse_mode='Markdown')
        return

    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM bot_users')
    all_users = cursor.fetchall()
    conn.close()

    sent_count = 0
    blocked_count = 0

    status_msg = await update.message.reply_text("⏳ Broadcast shuru ho gaya hai...")

    for (user_id,) in all_users:
        try:
            await context.bot.send_message(chat_id=user_id, text=f"📢 **Announcement:**\n\n{message_text}", parse_mode='Markdown')
            sent_count += 1
        except Exception:
            blocked_count += 1

    await status_msg.edit_text(
        f"✅ **Broadcast Completed!**\n\n"
        f"📤 Successfully Sent: `{sent_count}`\n"
        f"❌ Failed: `{blocked_count}`",
        parse_mode='Markdown'
    )

# ==================== PAYMENT & APPROVAL ====================
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'buy_premium':
        caption = (
            "💰 **49Rs Exclusive Premium**\n\n"
            "1. Niche diye gaye QR Code par ₹49 pay karein.\n"
            "2. Payment hone ke baad **Payment Ka Screenshot** iss chat me bhej do."
        )
        await query.message.reply_photo(photo=QR_FILE_ID, caption=caption, parse_mode='Markdown')

async def handle_screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    
    await update.message.reply_text("✅ **Screenshot mil gaya hai!** Admin ise verify karke aapko link bhej dega.")
    
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user.id}")
        ]
    ])
    
    photo_file_id = update.message.photo[-1].file_id
    caption = f"📩 **New Payment Claim!**\n\n**User:** {user.full_name} (@{user.username})\n**ID:** `{user.id}`"
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo_file_id,
        caption=caption,
        parse_mode='Markdown',
        reply_markup=admin_keyboard
    )

async def admin_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split('_')
    action = data[0]
    target_user_id = int(data[1])

    if action == "approve":
        now = datetime.datetime.now()
        expiry = now + datetime.timedelta(days=3)

        try:
            # Single-use link
            invite_link = await context.bot.create_chat_invite_link(
                chat_id=PREMIUM_CHANNEL_ID,
                member_limit=1,
                creates_join_request=False,
                expire_date=now + datetime.timedelta(hours=24)
            )

            conn = sqlite3.connect('subscribers.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, join_date, expiry_date, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (target_user_id, "user", now, expiry, 'active'))
            conn.commit()
            conn.close()

            # Send link to user
            await context.bot.send_message(
                chat_id=target_user_id,
                text=(
                    "🎉 **Payment Verified!**\n\n"
                    "Aapka 3-Day Premium Subscription start ho chuka hai.\n\n"
                    f"🔗 **One-Time Join Link:** {invite_link.invite_link}\n\n"
                    "⚠️ *Note: Ye link sirf 1 baar aur aapke liye hi kaam karega!*"
                ),
                parse_mode='Markdown'
            )

            # Post proof in channel
            if query.message.photo:
                await context.bot.send_photo(
                    chat_id=PROOF_CHANNEL_ID,
                    photo=query.message.photo[-1].file_id,
                    caption="✅ **New Payment Verified & Approved!** (₹49 Exclusive Premium)",
                    parse_mode='Markdown'
                )

            await query.edit_message_caption(caption=f"{query.message.caption}\n\n✅ **APPROVED & SENT TO PROOF**")

        except Exception as e:
            await query.message.reply_text(f"⚠️ Error: {e}\n(Bot ko Both Channels me ADMIN banao!)")

    elif action == "reject":
        await context.bot.send_message(
            chat_id=target_user_id,
            text="❌ **Payment Verification Failed!** Support se contact karein."
        )
        await query.edit_message_caption(caption=f"{query.message.caption}\n\n❌ **REJECTED**")

# ==================== AUTO REMOVAL SYSTEM ====================
async def check_subscriptions(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.datetime.now()
    conn = sqlite3.connect('subscribers.db')
    cursor = conn.cursor()

    cursor.execute("SELECT user_id, expiry_date FROM users WHERE status = 'active'")
    users = cursor.fetchall()

    for user_id, expiry_str in users:
        expiry = datetime.datetime.strptime(expiry_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
        time_left = expiry - now

        # Reminder (6 hrs left)
        if datetime.timedelta(hours=0) < time_left <= datetime.timedelta(hours=6):
            try:
                renew_btn = InlineKeyboardMarkup([[InlineKeyboardButton("💎 Renew 49Rs Premium", callback_data='buy_premium')]])
                await context.bot.send_message(
                    chat_id=user_id,
                    text="⏰ **Reminder:** Aapka 3-day Premium plan 6 ghante me khatam hone wala hai!",
                    parse_mode='Markdown',
                    reply_markup=renew_btn
                )
            except Exception:
                pass

        # Expired - Remove user
        elif now >= expiry:
            try:
                await context.bot.ban_chat_member(chat_id=PREMIUM_CHANNEL_ID, user_id=user_id)
                await context.bot.unban_chat_member(chat_id=PREMIUM_CHANNEL_ID, user_id=user_id)
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ **Plan Expired!** Aapka 3-day plan khatam ho gaya hai."
                )
            except Exception as e:
                logging.error(f"Failed to kick user {user_id}: {e}")

            cursor.execute("UPDATE users SET status = 'expired' WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

# ==================== MAIN ====================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CommandHandler("broadcast", broadcast_message))
    
    app.add_handler(CallbackQueryHandler(button_click, pattern='^buy_premium$'))
    app.add_handler(CallbackQueryHandler(admin_approval, pattern='^(approve|reject)_'))
    app.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, handle_screenshot))

    job_queue = app.job_queue
    job_queue.run_repeating(check_subscriptions, interval=600, first=10)

    print("Bot is running perfectly!")
    app.run_polling()

if __name__ == '__main__':
    main()
  
