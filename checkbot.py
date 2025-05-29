import os
import json
import csv
from datetime import datetime
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.ext import MessageHandler, filters
import nest_asyncio
nest_asyncio.apply()

# === CONFIGURATION ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set with: export BOT_TOKEN='your_token_here'
PROFILE_FILE = "fruit_profiles.json"

# === UTILITY FUNCTIONS ===
def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return []
    with open(PROFILE_FILE, "r") as f:
        return json.load(f)

def save_profiles(data):
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def parse_profile(text):
    profile = {}
    lines = text.strip().splitlines()
    for line in lines:
        parts = line.split(":", 1)
        if len(parts) == 2:
            label = parts[0].strip().lower()
            value = parts[1].strip()
            if "name" in label:
                profile["name"] = value
            elif "number" in label:
                profile["number"] = value
            elif "social" in label:
                profile["socials"] = [s.strip() for s in value.split(",") if s.strip()]
    return profile

async def echo_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user = update.message.from_user
        chat_type = update.message.chat.type
        print(f"[{chat_type}] {user.username}: {update.message.text}")

# === BOT COMMANDS ===
async def submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Triggered /submit by @{update.message.from_user.username}")
    raw_text = update.message.text.replace("/submit", "").strip()
    if not raw_text:
        await update.message.reply_text("❗ Please paste the profile after /submit.")
        return

    profile = parse_profile(raw_text)
    if "name" not in profile or "number" not in profile:
        await update.message.reply_text("⚠️ Missing Name or Number.")
        return

    data = load_profiles()

    # Check for duplicates by name + number
    for existing in data:
        if (existing.get("name", "").lower() == profile["name"].lower() and
            existing.get("number", "").lower() == profile["number"].lower()):
            await update.message.reply_text("⚠️ This person seems to already be in the system!")

    # Save profile
    profile["submitted_by"] = update.message.from_user.username or "unknown"
    profile["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M")

    data.append(profile)
    save_profiles(data)

    await update.message.reply_text(f"✅ Saved profile for {profile['name']}.")

    for profile in matches:
        reply = (
            f"🔎 Match Found:\n\n"
            f"🧍 {profile['name']}\n"
            f"📞 {profile['number']}\n"
            f"📱 {', '.join(profile.get('socials', [])) or '—'}\n"
            f"👤 @{profile['submitted_by']}\n"
            f"🕒 {profile['timestamp']}\n\n"
            f"⚠️ Already fished."
        )
        await update.message.reply_text(reply)

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Triggered /check by @{update.message.from_user.username}")
    if not context.args:
        await update.message.reply_text("❗ Usage: /check <name, number, or social>")
        return

    query = " ".join(context.args).strip().lower()
    data = load_profiles()

    matches = []
    for profile in data:
        if (
            query in profile.get("name", "").lower() or
            query in profile.get("number", "").lower() or
            any(query in s.lower() for s in profile.get("socials", []))
        ):
            matches.append(profile)

    if not matches:
        await update.message.reply_text("✅ No match found.")
        return

    for profile in matches:
        reply = (
            f"🔎 Match Found:\n\n"
            f"🧍 {profile['name']}\n"
            f"📞 {profile['number']}\n"
            f"📱 {', '.join(profile.get('socials', [])) or '—'}\n"
            f"👤 @{profile['submitted_by']}\n"
            f"🕒 {profile['timestamp']}\n"
        )
        await update.message.reply_text(reply)

async def view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Triggered /view by @{update.message.from_user.username}")
    user = update.message.from_user.username or ""
    username = user.lower()

    if context.args:
        username = context.args[0].replace("@", "").strip().lower()

    data = load_profiles()
    matches = [p for p in data if p.get("Fished by", "").lower() == username]

    if not matches:
        await update.message.reply_text(f"🙁 No profiles from @{username}.")
        return

    for profile in matches:
        reply = (
            f"🧍 {profile['name']}\n"
            f"📞 {profile['number']}\n"
            f"📱 {', '.join(profile.get('socials', [])) or '—'}\n"
            f"👤 @{profile['submitted_by']}\n"
            f"🕒 {profile['Date']}"
        )
        await update.message.reply_text(reply)

async def export_profiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Triggered /export by @{update.message.from_user.username}")
    data = load_profiles()
    if not data:
        await update.message.reply_text("📭 No profiles to export.")
        return

    with open("fruit_profiles.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "number", "socials", "submitted_by", "timestamp"])
        writer.writeheader()
        for p in data:
            writer.writerow({
                "name": p.get("name", ""),
                "number": p.get("number", ""),
                "socials": ", ".join(p.get("socials", [])),
                "submitted_by": p.get("submitted_by", ""),
                "timestamp": p.get("timestamp", "")
            })

    await update.message.reply_text("✅ Exported to fruit_profiles.csv.")

# Set bot command descriptions
async def set_commands(app):
    commands = [
        BotCommand("submit", "Submit a new Fruit Profile"),
        BotCommand("check", "Check for duplicates"),
        BotCommand("view", "View user submissions"),
        BotCommand("export", "Export profiles to CSV")
    ]
    await app.bot.set_my_commands(commands)

# === START BOT ===
from telegram.ext import Application
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("submit", submit))
app.add_handler(CommandHandler("check", check))
app.add_handler(CommandHandler("view", view))
app.add_handler(CommandHandler("export", export_profiles))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), echo_all))

# Safe async for macOS/Terminal
import asyncio

async def run():
    await set_commands(app)
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("⚠️ Event loop already running.")
        else:
            loop.run_until_complete(run())
    except RuntimeError:
        asyncio.run(run())