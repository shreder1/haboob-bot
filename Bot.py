import os
import sqlite3
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

DB = "haboob.db"


# -------------------------
# Database
# -------------------------
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 0,
            last_claim TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT user_id, balance, last_claim FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return row


def ensure_user(user_id: int):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "INSERT OR IGNORE INTO users(user_id, balance, last_claim) VALUES (?, 0, NULL)",
        (user_id,),
    )
    conn.commit()
    conn.close()


def update_claim(user_id: int, reward: int, now_iso: str):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute(
        "UPDATE users SET balance = balance + ?, last_claim = ? WHERE user_id = ?",
        (reward, now_iso, user_id),
    )
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return int(row[0]) if row else 0


# -------------------------
# Commands
# -------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    msg = (
        "🐫🕶️ *HABOOB Coin Collector*\n\n"
        "أوامر البوت:\n"
        "• /claim — تجمع HABOOB (مرة كل 24 ساعة)\n"
        "• /balance — رصيدك الحالي\n\n"
        "HABOOB too calm for this market 😎"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    row = get_user(user_id)
    # row: (user_id, balance, last_claim)
    last_claim = row[2]

    now = datetime.utcnow()
    now_iso = now.isoformat()

    if last_claim:
        try:
            last_time = datetime.fromisoformat(last_claim)
        except ValueError:
            # If old/invalid format stored, allow claim and overwrite
            last_time = now - timedelta(days=999)

        if now - last_time < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_time)
            hours = remaining.seconds // 3600
            minutes = (remaining.seconds % 3600) // 60
            await update.message.reply_text(
                f"⏳ بعدك مستعمل /claim.\nارجع بعد: {hours} ساعة و {minutes} دقيقة."
            )
            return

    reward = 25  # عدّلها براحتك
    update_claim(user_id, reward, now_iso)
    bal = get_balance(user_id)

    await update.message.reply_text(
        f"✅ جمعت {reward} HABOOB 🐫\n💰 رصيدك صار: {bal} HABOOB"
    )


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)
    bal = get_balance(user_id)
    await update.message.reply_text(f"💰 رصيدك الحالي: {bal} HABOOB 🐫")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("جرّب: /start /claim /balance")


# -------------------------
# Main
# -------------------------
def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing BOT_TOKEN env var. Add it in Render Environment Variables.")

    init_db()

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("help", help_cmd))

    app.run_polling()


if __name__ == "__main__":
    main()
