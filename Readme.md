# Advanced Discord Ticket Bot

A production-ready, fully functional Discord Ticket Bot built with Python and discord.py 2.x.

## Features

- 🎫 Fully functional ticket system with prefix commands
- 💾 Support for both SQLite and MongoDB databases
- 🔄 Automatic recovery after bot restart/crash
- 🎨 Interactive UI with Buttons, Select Menus, Embeds, and Modals
- 📝 Automatic transcript generation (HTML format)
- ⏰ Auto-close timers with persistent state
- 👥 Support role system with per-ticket-type access
- 📊 Detailed logging (ticket open/close)
- 🔒 Proper permission management
- 🚀 Production-ready architecture
- 📱 Mobile-friendly transcript format

## Installation

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token
- Discord Server with proper permissions

### Step 1: Clone/Download

```bash
git clone <your-repo-url>
cd discord-ticket-bot
```

```
discord-ticket-bot/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── config.json
├── panelbox.json
├── dropdownoption.json
├── access.json
├── database/
│   ├── __init__.py
│   ├── base.py
│   ├── sqlite.py
│   └── mongodb.py
├── cogs/
│   ├── __init__.py
│   ├── ticket_commands.py
│   └── events.py
├── views/
│   ├── __init__.py
│   ├── ticket_panel.py
│   ├── ticket_controls.py
│   └── modals.py
├── services/
│   ├── __init__.py
│   ├── ticket_service.py
│   ├── transcript_service.py
│   ├── duration_service.py
│   └── recovery_service.py
├── utils/
│   ├── __init__.py
│   ├── config.py
│   ├── permissions.py
│   ├── embeds.py
│   ├── logger.py
│   └── errors.py
├── data/
│   └── tickets.db
└── transcripts/
```
