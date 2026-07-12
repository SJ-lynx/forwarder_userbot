import json
from pyrogram import Client, filters
import re
import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    API_ID = int(os.getenv("API_ID", 0))
    API_HASH = os.getenv("API_HASH", "")
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    if not API_ID or not API_HASH or not ADMIN_ID:
        raise ValueError
except (TypeError, ValueError):
    print("❌ Ошибка: Убедитесь, что переменные API_ID, API_HASH и ADMIN_ID правильно заполнены в файле .env")
    sys.exit(1)

def load_settings():
    try:
        with open("settings.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "admin_id": ADMIN_ID,
            "source_chats": [],
            "target_chat": "",
            "filters": {
                "keywords": [],
                "types": [],
                "remove_types": [],
                "forwarded_from": False,
                "append_keyword": ""
            }
        }

def save_settings(data):
    with open("settings.json", "w") as f:
        json.dump(data, f, indent=4)

settings = load_settings()
app = Client("userbot", API_ID, API_HASH)

@app.on_message()
async def forward_message(client, message):
    if not message.chat or (message.text and message.text.startswith("/")):
        return

    if not settings.get("target_chat"):
        return

    source_chats = [str(c).lower() for c in settings.get("source_chats", [])]
    chat_id = str(message.chat.id)
    chat_username = f"@{message.chat.username}".lower() if message.chat.username else ""

    if chat_id not in source_chats and chat_username not in source_chats:
        return

    filters_config = settings["filters"]
    text = message.text or message.caption or ""

    for kw in filters_config["keywords"]:
        if str(kw).lower() in text.lower():
            return

    spammed_types = filters_config["types"]
    if (("text" in spammed_types and message.text) or
       ("link" in spammed_types and has_link(text)) or
       ("file" in spammed_types and message.document) or
       ("photo" in spammed_types and message.photo) or
       ("video" in spammed_types and message.video) or
       ("location" in spammed_types and message.location) or
       ("contact" in spammed_types and message.contact)):
        return

    if "link" in filters_config["remove_types"]:
        text = remove_links(text)
    if filters_config["append_keyword"]:
        text += f"\n\n{filters_config['append_keyword']}"

    disable_forward_info = filters_config.get("forwarded_from", False)

    if disable_forward_info:
        try:
            await message.forward(settings["target_chat"])
        except Exception as e:
            print(f"Ошибка при пересылке: {e}")
    else:
        try:
            if message.text:
                await client.send_message(settings["target_chat"], text)
            elif message.photo:
                if "photo" in filters_config["remove_types"]:
                    if text: await client.send_message(settings["target_chat"], text)
                else:
                    await client.send_photo(settings["target_chat"], message.photo.file_id, caption=text)
            elif message.video:
                if "video" in filters_config["remove_types"]:
                    if text: await client.send_message(settings["target_chat"], text)
                else:
                    await client.send_video(settings["target_chat"], message.video.file_id, caption=text)
            elif message.document:
                if "document" in filters_config["remove_types"]:
                    if text: await client.send_message(settings["target_chat"], text)
                else:
                    await client.send_document(settings["target_chat"], message.document.file_id, caption=text)
            elif message.audio:
                await client.send_audio(settings["target_chat"], message.audio.file_id, caption=text)
            elif message.voice:
                await client.send_voice(settings["target_chat"], message.voice.file_id, caption=text)
            elif message.sticker:
                if "sticker" not in filters_config["remove_types"]:
                    await client.send_sticker(settings["target_chat"], message.sticker.file_id)
            elif message.contact:
                if "contact" not in filters_config["remove_types"]:
                    await client.send_contact(settings["target_chat"],
                        phone_number=message.contact.phone_number,
                        first_name=message.contact.first_name)
            elif message.location:
                if "location" not in filters_config["remove_types"]:
                    await client.send_location(settings["target_chat"],
                        latitude=message.location.latitude,
                        longitude=message.location.longitude)
        except Exception as e:
            print(f"Ошибка при отправке: {e}")

def has_link(text):
    return bool(re.search(r"@[a-zA-Z0-9_]{5,}", text) or
                re.search(r"(https?://[^\s]+|www\.[^\s]+)", text))

def remove_links(text):
    text = re.sub(r"@[a-zA-Z0-9_]{5,}", "", text)
    text = re.sub(r"(https?://[^\s]+|www\.[^\s]+)", "", text)
    return text

@app.on_message(filters.command("addsource") & filters.user(settings["admin_id"]))
async def add_source(client, message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("Использование: /addsource @chat_username или chat_id")
    chat_id = parts[1]
    if chat_id not in settings["source_chats"]:
        settings["source_chats"].append(chat_id)
        save_settings(settings)
        await message.reply_text(f"✅ {chat_id} добавлен как источник!")

@app.on_message(filters.command("delsource") & filters.user(settings["admin_id"]))
async def del_source(client, message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("Использование: /delsource @chat_username или chat_id")
    chat_id = parts[1]
    if chat_id in settings["source_chats"]:
        settings["source_chats"].remove(chat_id)
        save_settings(settings)
        await message.reply_text(f"❌ {chat_id} удалён из источников!")

@app.on_message(filters.command("settarget") & filters.user(settings["admin_id"]))
async def set_target(client, message):
    parts = message.text.split()
    if len(parts) < 2:
        return await message.reply_text("Использование: /settarget @chat_username или chat_id")
    settings["target_chat"] = parts[1]
    save_settings(settings)
    await message.reply_text(f"🎯 Целевой чат: {parts[1]}")

@app.on_message(filters.command("add_spam_type") & filters.user(settings["admin_id"]))
async def add_spam_type(client, message):
    parts = message.text.split()
    if len(parts) < 2: return await message.reply_text("Использование: /add_spam_type type")
    data = parts[1]
    if data not in settings["filters"]["types"]:
        settings["filters"]["types"].append(data)
        save_settings(settings)
        await message.reply_text(f"{data} добавлен в типы спама!")
    else:
        await message.reply_text(f"{data} уже в типах спама.")

@app.on_message(filters.command("del_spam_type") & filters.user(settings["admin_id"]))
async def del_spam_type(client, message):
    parts = message.text.split()
    if len(parts) < 2: return await message.reply_text("Использование: /del_spam_type type")
    data = parts[1]
    if data in settings["filters"]["types"]:
        settings["filters"]["types"].remove(data)
        save_settings(settings)
        await message.reply_text(f"{data} удалён из типов спама!")

@app.on_message(filters.command("add_removetype") & filters.user(settings["admin_id"]))
async def add_remove_type(client, message):
    parts = message.text.split()
    if len(parts) < 2: return await message.reply_text("Использование: /add_removetype type")
    data = parts[1]
    if data not in settings["filters"]["remove_types"]:
        settings["filters"]["remove_types"].append(data)
        save_settings(settings)
        await message.reply_text(f"{data} добавлен в типы для удаления!")

@app.on_message(filters.command("del_removetype") & filters.user(settings["admin_id"]))
async def del_remove_type(client, message):
    parts = message.text.split()
    if len(parts) < 2: return await message.reply_text("Использование: /del_removetype type")
    data = parts[1]
    if data in settings["filters"]["remove_types"]:
        settings["filters"]["remove_types"].remove(data)
        save_settings(settings)
        await message.reply_text(f"{data} удалён из типов для удаления!")

@app.on_message(filters.command("add_keyword") & filters.user(settings["admin_id"]))
async def add_keyword(client, message):
    parts = message.text.split()
    if len(parts) < 2: return await message.reply_text("Использование: /add_keyword keyword")
    data = parts[1]
    if data not in settings["filters"]["keywords"]:
        settings["filters"]["keywords"].append(data)
        save_settings(settings)
        await message.reply_text(f"{data} добавлен в ключевые слова!")

@app.on_message(filters.command("del_keyword") & filters.user(settings["admin_id"]))
async def del_keyword(client, message):
    parts = message.text.split()
    if len(parts) < 2: return await message.reply_text("Использование: /del_keyword keyword")
    data = parts[1]
    if data in settings["filters"]["keywords"]:
        settings["filters"]["keywords"].remove(data)
        save_settings(settings)
        await message.reply_text(f"{data} удалён из ключевых слов!")

@app.on_message(filters.command("set_append") & filters.user(settings["admin_id"]))
async def set_append(client, message):
    parts = message.text.split()
    if len(parts) < 2: return await message.reply_text("Использование: /set_append keyword")
    keyword = " ".join(parts[1:])
    settings["filters"]["append_keyword"] = keyword
    save_settings(settings)
    await message.reply_text(f"✅ Добавляемое слово: {keyword}")

@app.on_message(filters.command("settings"))
async def get_settings(client, message):
    txt = (f"Чаты-источники: {settings['source_chats']}\n"
           f"Целевой чат: {settings['target_chat']}\n"
           f"Ключевые слова спама: {settings['filters']['keywords']}\n"
           f"Типы спама: {settings['filters']['types']}\n"
           f"Типы для удаления: {settings['filters']['remove_types']}\n"
           f"Добавляемое слово: {settings['filters']['append_keyword']}")
    await message.reply_text(txt)

@app.on_message(filters.command("help"))
async def help_command(client, message):
    txt = ("/settings - текущие настройки\n"
           "/addsource @chat - добавить чат-источник\n"
           "/delsource @chat - удалить чат-источник\n"
           "/settarget @chat - установить целевой чат\n"
           "/add_keyword kw - добавить блок-слово\n"
           "/del_keyword kw - удалить блок-слово\n"
           "/add_spam_type type - добавить тип в спам\n"
           "/del_spam_type type - удалить тип из спама\n"
           "/set_append kw - установить добавляемое слово\n"
           "/add_removetype type - добавить тип для удаления\n"
           "/del_removetype type - удалить тип из удаляемых")
    await message.reply_text(txt)

app.run()
