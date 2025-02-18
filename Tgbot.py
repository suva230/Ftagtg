import os
import sys
from telethon import TelegramClient, events

# Use environment variables for security
api_id = int(os.getenv("API_ID"))  
api_hash = os.getenv("API_HASH")
bot_token = os.getenv("BOT_TOKEN")

# Pre-set authorization key
authorization_key = os.getenv("AUTH_KEY")  # Change & share with users

# Admins who can restart the bot
admin_users = {'Avengers005', 'Suva023'}  # Only these users can restart

# Initialize the Telegram client
client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Store authorized users
authorized_users = set()
authorized_channels = set()

# Temporary storage (reset on restart)
temp_files = []
file_store = {}

# Track bulk storage mode status
bulk_storage_mode = False

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Handle the /start command and request authorization if needed."""
    sender = await event.get_sender()
    
    if sender.username in authorized_users:
        await event.reply(
            "**✅ You are already authorized!**\n\n"
            "**📌 Available Commands:**\n"
            "🔹 `start bulk` - Enable bulk file storage\n"
            "🔹 `stop bulk` - Disable bulk mode\n"
            "🔹 `setName:-<name>` - Save bulk files under a name\n"
            "🔹 `/name` - Retrieve saved files by name\n"
            "🔹 `clear chat` - Delete all bot messages in the chat\n"
            "🔹 `/restart` - Restart the bot (Admins Only)"
        )
    else:
        await event.reply(
            "**🔒 This bot is restricted!**\n"
            "Please enter the authorization key to access.\n"
            "Use: `auth <your_key>`"
        )

@client.on(events.NewMessage(pattern='auth (.+)'))
async def authorize(event):
    """Authorize the user if they provide the correct key."""
    sender = await event.get_sender()
    key = event.pattern_match.group(1).strip()
    
    if key == authorization_key:
        authorized_users.add(sender.username)
        await event.reply(
            "**✅ Authorization successful!**\n\n"
            "**📌 Available Commands:**\n"
            "🔹 `start bulk` - Enable bulk file storage\n"
            "🔹 `stop bulk` - Disable bulk mode\n"
            "🔹 `setName:-<name>` - Save bulk files under a name\n"
            "🔹 `/name` - Retrieve saved files by name\n"
            "🔹 `clear chat` - Delete all bot messages in the chat\n"
            "🔹 `/restart` - Restart the bot (Admins Only)"
        )
    else:
        await event.reply("❌ **Invalid authorization key. Try again!**")

@client.on(events.NewMessage)
async def handle_message(event):
    """Handle other commands only if the user is authorized."""
    global bulk_storage_mode
    sender = await event.get_sender()

    if sender.username not in authorized_users:
        await event.reply("❌ **You are not authorized!** Use `auth <your_key>` to gain access.")
        return

    text = event.message.text.lower()

    if text == 'start bulk':
        bulk_storage_mode = True
        await event.reply("📂 **Bulk storage mode activated!** Forward multiple files now.")
    elif text == 'stop bulk':
        bulk_storage_mode = False
        await event.reply("🔕 **Bulk storage mode deactivated!**")
    elif text == 'clear chat':
        await clear_chat(event)
    elif text.startswith('setname:-'):
        name = text.replace('setname:-', '').strip()
        if name and temp_files:
            file_store[name] = temp_files.copy()
            temp_files.clear()
            bulk_storage_mode = False
            await event.reply(f"✅ **Files saved under:** `{name}`")
        else:
            await event.reply("❌ **No files to save or invalid name.**")
    elif text.startswith('/'):
        name = text[1:].strip()
        if name in file_store:
            for file in file_store[name]:
                if file['type'] == 'media':
                    await client.send_file(event.chat_id, file['media'], caption=file['caption'])
                else:
                    await client.send_message(event.chat_id, file['text'])
        else:
            await event.reply("❌ **No files found for this name.**")
    elif event.message.forward:
        if bulk_storage_mode:
            temp_files.append({
                'type': 'media' if event.message.media else 'text',
                'media': event.message.media if event.message.media else None,
                'caption': event.message.text if event.message.text else None
            })
        else:
            await client.forward_messages(event.chat_id, event.message)
    else:
        await event.reply("⚠️ **Invalid command or message.**\nUse `/start` to see available commands.")

async def clear_chat(event):
    """Clear the chat by deleting all messages."""
    async for message in client.iter_messages(event.chat_id):
        try:
            await client.delete_messages(event.chat_id, message.id)
        except Exception as e:
            print(f"Failed to delete message {message.id}: {e}")
    await event.respond("🗑️ **Chat cleared!**")

@client.on(events.NewMessage(pattern='/restart'))
async def restart(event):
    """Restart the bot (admin only)."""
    sender = await event.get_sender()
    
    if sender.username in admin_users:  # Only Avengers005 & Suva023 can restart
        await event.reply("🔄 **Restarting bot...**")
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        await event.reply("❌ **You are not authorized to restart the bot!**")

print("🚀 Bot is running...")
client.run_until_disconnected()
