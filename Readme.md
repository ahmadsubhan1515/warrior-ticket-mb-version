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
