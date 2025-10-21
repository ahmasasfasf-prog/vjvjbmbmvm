import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)

# ======= تنظیمات =======
TOKEN = "8169710376:AAGyx3swmW-30cAuttDLuWLY-Atqbf9tURs"  # توکن ربات
ADMIN_IDS = [5579824152, 6503400915]  # ID ادمین‌ها

CHANNELS_FILE = "channels.json"
MUSIC_DIR = "musics"

os.makedirs(MUSIC_DIR, exist_ok=True)

# بارگذاری کانال‌ها
if os.path.exists(CHANNELS_FILE):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        channels = json.load(f)
else:
    channels = []

# بارگذاری دیتای موزیک‌ها
MUSIC_DATA_FILE = os.path.join(MUSIC_DIR, "data.json")
if os.path.exists(MUSIC_DATA_FILE):
    with open(MUSIC_DATA_FILE, "r", encoding="utf-8") as f:
        MUSIC_DATA = json.load(f)
else:
    MUSIC_DATA = {}


# ======= توابع کمکی =======
async def is_user_member(bot, user_id):
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True


def save_channels():
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, ensure_ascii=False, indent=2)


def save_music_data():
    with open(MUSIC_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(MUSIC_DATA, f, ensure_ascii=False, indent=2)


# ======= دستورات =======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # اگر بدون لینک استارت شد
    if not args:
        text = "سلام 👋\nبرای دریافت موزیک‌ها روی لینک مخصوص موزیک بزن یا از ادمین لینک بگیر."
        await update.message.reply_text(text)
        return

    # اگر لینک موزیک هست
    arg = args[0]
    if arg.startswith("music_"):
        file_id = arg.replace("music_", "")
        if not await is_user_member(context.bot, user_id):
            text = "⚠️ لطفاً ابتدا در کانال‌های زیر عضو شوید:"
            buttons = [
                [InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}")]
                for ch in channels
            ]
            buttons.append(
                [InlineKeyboardButton("✅ عضو شدم", callback_data=f"check_{file_id}")]
            )
            await update.message.reply_text(
                text, reply_markup=InlineKeyboardMarkup(buttons)
            )
            return
        await send_music(update, context, file_id)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("check_"):
        file_id = data.replace("check_", "")
        if await is_user_member(context.bot, user_id):
            await query.message.reply_text("✅ عضویت تأیید شد، در حال ارسال موزیک...")
            await send_music(query, context, file_id)
        else:
            await query.answer("❌ هنوز در همه کانال‌ها عضو نیستی!", show_alert=True)


async def send_music(update_obj, context: ContextTypes.DEFAULT_TYPE, file_id):
    if file_id not in MUSIC_DATA:
        await update_obj.message.reply_text("❌ موزیک پیدا نشد یا حذف شده.")
        return
    data = MUSIC_DATA[file_id]
    file_type = data.get("type", "audio")  # audio یا voice
    file_file_id = data["file_id"]
    caption = f"🎵 لینک موزیک شما:\n{data['title']}"

    chat_id = update_obj.effective_chat.id

    if file_type == "voice":
        await context.bot.send_voice(
            chat_id=chat_id, voice=file_file_id, caption=caption
        )
    else:
        await context.bot.send_audio(
            chat_id=chat_id, audio=file_file_id, caption=caption
        )


# ======= آپلود موزیک توسط ادمین =======
async def upload_music(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند موزیک آپلود کنند.")
        return

    file = update.message.audio or update.message.voice
    if not file:
        await update.message.reply_text("❌ فقط فایل صوتی یا ویس قابل قبول است.")
        return

    file_id = file.file_id
    title = file.title if hasattr(file, "title") and file.title else "بدون نام"
    file_type = "voice" if isinstance(file, type(update.message.voice)) else "audio"

    MUSIC_DATA[file_id] = {"file_id": file_id, "title": title, "type": file_type}
    save_music_data()

    bot_username = context.bot.username
    link = f"https://t.me/{bot_username}?start=music_{file_id}"
    await update.message.reply_text(
        f"✅ موزیک ذخیره شد!\n📎 لینک مخصوص کاربران:\n{link}"
    )


# ======= مدیریت کانال‌ها =======
async def add_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند کانال اضافه کنند.")
        return
    if not context.args:
        await update.message.reply_text("فرمت: /addchannel @channel یا لینک")
        return
    ch = context.args[0]
    if ch.startswith("https://t.me/"):
        ch = "@" + ch.split("/")[-1]
    if ch not in channels:
        channels.append(ch)
        save_channels()
        await update.message.reply_text(f"✅ کانال {ch} اضافه شد.")
    else:
        await update.message.reply_text("⚠️ این کانال قبلاً اضافه شده است.")


async def remove_channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ فقط ادمین‌ها می‌توانند کانال حذف کنند.")
        return
    if not context.args:
        await update.message.reply_text("فرمت: /removechannel @channel")
        return
    ch = context.args[0]
    if ch.startswith("https://t.me/"):
        ch = "@" + ch.split("/")[-1]
    if ch in channels:
        channels.remove(ch)
        save_channels()
        await update.message.reply_text(f"🗑️ کانال {ch} حذف شد.")
    else:
        await update.message.reply_text("❌ چنین کانالی در لیست نیست.")


async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not channels:
        await update.message.reply_text("هیچ کانالی اضافه نشده است.")
    else:
        await update.message.reply_text("📋 لیست کانال‌ها:\n" + "\n".join(channels))


# ======= اجرای ربات =======
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, upload_music))
    app.add_handler(CommandHandler("addchannel", add_channel))
    app.add_handler(CommandHandler("removechannel", remove_channel))
    app.add_handler(CommandHandler("listchannels", list_channels))

    print("🤖 ربات با موفقیت اجرا شد...")
    app.run_polling()
