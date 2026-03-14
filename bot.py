import os
import datetime
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from database import conn, cursor

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# --------- UTILITY FUNCTIONS ---------
def get_or_create_user(user):
    cursor.execute("SELECT id FROM users WHERE telegram_id=%s", (user.id,))
    result = cursor.fetchone()
    if not result:
        cursor.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (%s,%s,%s) RETURNING id",
            (user.id, user.username, user.first_name)
        )
        conn.commit()
        return cursor.fetchone()[0]
    return result[0]

def create_session(session_name):
    now = datetime.datetime.now()
    cursor.execute(
        "INSERT INTO sessions (session_name, start_time) VALUES (%s,%s) RETURNING id",
        (session_name, now)
    )
    conn.commit()
    return cursor.fetchone()[0]

def end_session_db(session_id):
    now = datetime.datetime.now()
    cursor.execute("UPDATE sessions SET end_time=%s WHERE id=%s", (now, session_id))
    conn.commit()

# --------- BOT COMMANDS ---------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to በእንተ ክርስትና Attendance Bot")

# Start a session
async def start_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) == 0:
        await update.message.reply_text("Please provide a session name: /start_session Evening Bible Study")
        return

    session_name = " ".join(context.args)
    session_id = create_session(session_name)
    context.chat_data['current_session'] = session_id

    keyboard = [
        [InlineKeyboardButton("Join Session", callback_data=f"join_{session_id}")],
        [InlineKeyboardButton("Leave Session", callback_data=f"leave_{session_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(f"📢 Session '{session_name}' started!\nClick below to mark attendance.", reply_markup=reply_markup)

# Handle Join/Leave button clicks
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    data = query.data.split("_")
    action = data[0]  # join / leave
    session_id = int(data[1])
    user_id = get_or_create_user(user)

    now = datetime.datetime.now()

    if action == "join":
        cursor.execute(
            "INSERT INTO attendance (user_id, session_id, join_time) VALUES (%s,%s,%s)",
            (user_id, session_id, now)
        )
        conn.commit()
        await query.message.reply_text(f"{user.username} joined the session.")

    elif action == "leave":
        cursor.execute(
            "UPDATE attendance SET leave_time=%s WHERE user_id=%s AND session_id=%s AND leave_time IS NULL",
            (now, user_id, session_id)
        )
        conn.commit()
        await query.message.reply_text(f"{user.username} left the session.")

# End session command
async def end_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session_id = context.chat_data.get('current_session')
    if not session_id:
        await update.message.reply_text("No session currently active.")
        return

    end_session_db(session_id)

    cursor.execute("""
        SELECT u.username, a.join_time, a.leave_time
        FROM attendance a
        JOIN users u ON u.id = a.user_id
        WHERE a.session_id=%s
    """, (session_id,))
    rows = cursor.fetchall()

    report = f"📊 Session Report\n\n"
    for r in rows:
        join_time = r[1].strftime("%H:%M:%S") if r[1] else "N/A"
        leave_time = r[2].strftime("%H:%M:%S") if r[2] else "N/A"
        report += f"{r[0]} | {join_time} → {leave_time}\n"

    await update.message.reply_text(report)
    context.chat_data['current_session'] = None

# --------- SETUP BOT ---------
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("start_session", start_session))
app.add_handler(CommandHandler("end_session", end_session))
app.add_handler(CallbackQueryHandler(button))

app.run_polling()