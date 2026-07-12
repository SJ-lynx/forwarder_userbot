# 📨 Telegram Forwarder Userbot

Pyrogram-юзербот для пересылки сообщений между чатами с фильтрацией. Управляется командами прямо в Telegram.

## Запуск

```bash
pip install -r requirements.txt # kurigram для работы pyrogram
cp .env.example .env  # заполнить API_ID, API_HASH, ADMIN_ID
python userbot.py
# При первом запуске Pyrogram запросит номер телефона и код
```

## Команды

`/addsource @chat` — добавить чат-источник  
`/delsource @chat` — удалить чат-источник  
`/settarget @chat` — установить целевой чат  
`/add_keyword kw` — добавить блок-слово  
`/del_keyword kw` — удалить блок-слово  
`/add_spam_type type` — блокировать тип сообщений (text/photo/video/link...)  
`/add_removetype type` — удалять тип при пересылке  
`/set_append kw` — добавлять текст к каждому сообщению  
`/settings` — текущие настройки  

Настройки сохраняются в `settings.json`
