from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import sqlite3
from datetime import datetime, timedelta

DB = "haboob.db"

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER,
        last_claim TEXT
    )
    """)
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (user_id, 0, None))
    conn.commit()
    conn.close()
    await update.message.reply_text("🐫 Welcome to HABOOB\nUse /claim to collect coins.")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT balance, last_claim FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()

    now = datetime.utcnow()
    if row[1]:
        last = datetime.fromisoformat(row[1])
        if now - last < timedelta(hours=24):
            await update.message.reply_text("⏳ Come back after 24h.")
            return

    reward = 25
    c.execute("UPDATE users SET balance = balance + ?, last_claim=? WHERE user_id=?",
              (reward, now.isoformat(), user_id))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"✅ You got {reward} HABOOB 🐫")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    bal = c.fetchone()[0]
    conn.close()
    await update.message.reply_text(f"💰 Your balance: {bal} HABOOB")

init_db()

app = ApplicationBuilder().token("8345091331:AAEvDmP_iZO8AoLDRpt48mmuy38IoZt3hxY").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("claim", claim))
app.add_handler(CommandHandler("balance", balance))
app.run_polling()
