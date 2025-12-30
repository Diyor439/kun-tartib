from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

# DB yaratish
conn = sqlite3.connect("schedule.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS schedule (
                    user_id INTEGER,
                    day TEXT,
                    time TEXT,
                    task TEXT
                 )''')
conn.commit()

# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# Eslatma funksiyasi
def send_notification(context: CallbackContext):
    user_id = context.job.data['user_id']
    task = context.job.data['task']
    context.bot.send_message(chat_id=user_id, text=f"⏰ Eslatma: {task}")

# /start komandasi
async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "Salom! Men sizning kun tartibingizni boshqaruvchi botman.\n"
        "Quyidagi komandalarni ishlating:\n"
        "/add - yangi ish qo'shish\n"
        "/list - ishlarni ko'rish\n"
        "/delete - ishni o'chirish"
    )

# Ish qo'shish
async def add(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Format: /add <kun> <soat:daqiqa> <ish>")
        return
    day = args[0].capitalize()
    time = args[1]
    task = " ".join(args[2:])
    user_id = update.message.from_user.id
    cursor.execute("INSERT INTO schedule VALUES (?,?,?,?)", (user_id, day, time, task))
    conn.commit()
    await update.message.reply_text(f"{day} soat {time} uchun '{task}' qo'shildi!")
    
    # Schedulerga qo'shish
    hour, minute = map(int, time.split(":"))
    scheduler.add_job(send_notification, 'cron', day_of_week=day.lower(), hour=hour, minute=minute,
                      args=[context], kwargs={'job': {'user_id': user_id, 'task': task}})

# Ishlarni ko'rish
async def list_tasks(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    cursor.execute("SELECT day, time, task FROM schedule WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("Sizda ishlar yo'q.")
        return
    msg = "Sizning ishlaringiz:\n"
    for day, time, task in rows:
        msg += f"{day} {time} - {task}\n"
    await update.message.reply_text(msg)

# Ishni o'chirish
async def delete(update: Update, context: CallbackContext):
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("Format: /delete <ish raqami>")
        return
    index = int(args[0]) - 1
    user_id = update.message.from_user.id
    cursor.execute("SELECT rowid, task FROM schedule WHERE user_id=?", (user_id,))
    rows = cursor.fetchall()
    if index < 0 or index >= len(rows):
        await update.message.reply_text("Xato raqam!")
        return
    rowid, task = rows[index]
    cursor.execute("DELETE FROM schedule WHERE rowid=?", (rowid,))
    conn.commit()
    await update.message.reply_text(f"Ish '{task}' o'chirildi!")

# Bot ishga tushurish
app = ApplicationBuilder().token("8254640876:AAEK2DVRHeVUSfPCPwpQ60a35_-TpLBfrW0").build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("list", list_tasks))
app.add_handler(CommandHandler("delete", delete))

app.run_polling()
