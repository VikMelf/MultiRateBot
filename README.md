📌 MultiRateBot - Telegram Currency Converter Bot

MultiRateBot is a multilingual Telegram bot that provides real-time currency exchange rates.
It supports Ukrainian, English, Polish, and German, and allows users to choose currency pairs through interactive buttons.

The exchange rates are retrieved from the European Central Bank (Frankfurter API), ensuring reliable and up-to-date data.

🚀 Features
🌍 Multilingual interface (UA / EN / PL / DE)
💱 Fast currency conversion
🔘 Convenient inline buttons (no need to type commands)
🔄 Live exchange rates from the European Central Bank
🧮 Supported pairs:
   USD → UAH
   EUR → CAD
   GBP → CHF
   PLN → UAH
And any other pairs supported by the API

🛠️ Tech Stack
Python 3.11
Aiogram 2.25
Requests
Frankfurter API
python-dotenv

📦 Project Structure
MultiRateBot/
│─ multiratebot.py        # main bot logic
│─ test_api.py            # API testing script
│─ requirements.txt        # dependencies
│─ .env (ignored)          # contains the bot token
│─ README.md               # project documentation

⚙️ How to Run

Clone or download the project
Create a virtual environment: python -m venv venv
                              venv\Scripts\activate


Install dependencies: pip install -r requirements.txt


Create .env file: BOT_TOKEN=your_bot_token_here


Run the bot: python multiratebot.py

## 🎥 Demo Video

[![Watch the demo](preview.png)](demo.mp4)


📬 Author

Victor Molven
vikmelf@gmail.com
GitHub: https://github.com/VikMelf

If you like this project
Give it a ⭐ on GitHub - it really helps!
