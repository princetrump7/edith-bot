# 🤖 Edith Bot — AI-Powered Telegram Assistant

An AI-powered Telegram bot inspired by the Edith bot concept. Chat, analyze, translate, debug code, and more — all through Telegram.

## ✨ Features

| Category | Tools |
|---|---|
| 💬 **AI Chat** | Natural conversation with context memory, `/newchat` to reset |
| 📝 **Text Analysis** | `/summarize`, `/translate`, `/grammar`, `/sentiment` |
| 💻 **Code Tools** | `/explain`, `/debug`, `/format` |
| 📊 **Utilities** | `/wordcount`, `/extracturls`, `/time` |
| 👤 **Profile & Settings** | `/profile`, `/settings` — customizable preferences |
| 🖼️ **Image Support** | Send a photo with a caption for AI assistance |
| 🆘 **Help** | `/help`, `/tools`, `/about` |

## 🚀 Quick Start

### 1. Get a Telegram Bot Token
Talk to [@BotFather](https://t.me/BotFather) on Telegram and create a new bot. Save the token.

### 2. Get an AI API Key
This bot uses OPENCODE to proxy DeepSeek models. Get your API key from your OPENCODE provider dashboard.

### 3. Configure
```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN and AI_API_KEY
```

### 4. Run
```bash
pip install -r requirements.txt
python bot.py
```

That's it! Message your bot on Telegram.

## 🌐 Deployment

### Polling Mode (default, simple)
```bash
BOT_TOKEN=xxx AI_API_KEY=xxx python bot.py
```

### Webhook Mode (production)
```bash
BOT_MODE=webhook BOT_TOKEN=xxx AI_API_KEY=xxx APP_URL=https://your-app.com python bot.py
```

### Render.com
1. Push this repo to GitHub
2. Create a new **Web Service** on Render
3. Connect your repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python bot.py`
6. Add environment variables (BOT_TOKEN, AI_API_KEY, APP_URL)
7. Deploy!

## 🧹 Commands

```
/start     — Welcome & quick start
/help      — Detailed help
/about     — About the bot
/newchat   — Reset conversation
/chatstat  — Chat statistics
/tools     — List all tools
/settings  — Configure preferences
/profile   — Your profile

/summarize  — Summarize text
/translate  — Translate text
/grammar    — Check grammar
/sentiment  — Analyze sentiment
/wordcount  — Word & character count
/extracturls — Extract URLs

/explain    — Explain code
/debug      — Debug code
/format     — Format code
/time       — Current time
```

## 🔧 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram bot token from BotFather |
| `AI_API_KEY` | ✅ | OPENCODE / DeepSeek API key |
| `AI_BASE_URL` | ❌ | Default: `https://api.opencode.ai/v1` |
| `AI_MODEL` | ❌ | Default: `deepseek-chat` |
| `BOT_MODE` | ❌ | `polling` or `webhook` |
| `APP_URL` | for webhook | Public URL for webhook endpoint |
| `BOT_NAME` | ❌ | Bot display name |

## 📁 Project Structure

```
edith-bot/
├── bot.py                 # Entry point — wires handlers
├── config.py              # Environment config
├── requirements.txt       # Dependencies
├── Dockerfile             # Container image
├── render.yaml            # Render deploy config
├── .env.example           # Config template
├── handlers/
│   ├── chat.py            # AI chat handler
│   ├── tools.py           # Tool commands router
│   ├── settings.py        # Settings & profile
│   └── help_handler.py    # Start, help, about
├── services/
│   ├── ai_service.py      # OPENCODE/DeepSeek API wrapper
│   └── tool_service.py    # Tool implementations
└── utils/
    └── helpers.py         # Shared utilities
```

## ⚙️ Tech Stack

- **Python 3.11+**
- **[python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)** v20.x
- **DeepSeek** via OPENCODE API
- **httpx** / **openai** Python SDK

## 📄 License

MIT
