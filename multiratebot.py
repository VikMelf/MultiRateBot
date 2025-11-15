# multiratebot.py
# Simple Telegram button-driven currency converter
# Requires: aiogram==2.25.1, requests, python-dotenv

import os
import logging
import requests
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load .env and BOT_TOKEN
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Set BOT_TOKEN in .env file (BOT_TOKEN=...)")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Supported languages and localized strings
LANGS = ["en", "de", "pl", "uk"]

LOCALES = {
    "en": {
        "start": "Welcome! I'm MultiRateBot 💱\nChoose language.",
        "menu_convert": "Convert",
        "menu_change_lang": "Change language",
        "menu_help": "Help",
        "prompt_from": "Choose source currency:",
        "prompt_to": "Choose target currency:",
        "prompt_amount": "Choose amount or enter Custom:",
        "custom_amount": "Please type the amount (e.g. 12.50):",
        "error_invalid_amount": "Invalid amount. Use a number like 12.50.",
        "result": "Result: {amount} {from_curr} → {converted:.4f} {to_curr}\nRate: {rate:.6f}",
        "api_error": "Failed to fetch exchange rate. Try later.",
        "help_text": "Use buttons: Convert → choose currencies → choose amount → get result.",
        "custom": "Custom",
        "back": "Back"
    },
    "de": {
        "start": "Willkommen! MultiRateBot 💱\nWähle Sprache.",
        "menu_convert": "Konvertieren",
        "menu_change_lang": "Sprache ändern",
        "menu_help": "Hilfe",
        "prompt_from": "Wähle Quellwährung:",
        "prompt_to": "Wähle Zielwährung:",
        "prompt_amount": "Wähle Betrag oder 'Benutzerdefiniert':",
        "custom_amount": "Bitte gib den Betrag ein (z. B. 12.50):",
        "error_invalid_amount": "Ungültiger Betrag.",
        "result": "Ergebnis: {amount} {from_curr} → {converted:.4f} {to_curr}\nKurs: {rate:.6f}",
        "api_error": "Fehler при отриманні курсу.",
        "help_text": "Nutze die Buttons: Konvertieren → Währungen → Betrag → Ergebnis.",
        "custom": "Benutzerdefiniert",
        "back": "Zurück"
    },
    "pl": {
        "start": "Witaj! MultiRateBot 💱\nWybierz język.",
        "menu_convert": "Konwertuj",
        "menu_change_lang": "Zmień język",
        "menu_help": "Pomoc",
        "prompt_from": "Wybierz walutę źródłową:",
        "prompt_to": "Wybierz walutę docelową:",
        "prompt_amount": "Wybierz kwotę lub 'Własna':",
        "custom_amount": "Wpisz kwotę (np. 12.50):",
        "error_invalid_amount": "Nieprawidłowa kwota.",
        "result": "Wynik: {amount} {from_curr} → {converted:.4f} {to_curr}\nKurs: {rate:.6f}",
        "api_error": "Błąd при отриманні курсу.",
        "help_text": "Użyj przycisków: Konwertuj → waluty → kwota → wynik.",
        "custom": "Własna",
        "back": "Wstecz"
    },
    "uk": {
        "start": "Вітаю! MultiRateBot 💱\nОберіть мову.",
        "menu_convert": "Конвертувати",
        "menu_change_lang": "Змінити мову",
        "menu_help": "Допомога",
        "prompt_from": "Оберіть валюту-джерело:",
        "prompt_to": "Оберіть цільову валюту:",
        "prompt_amount": "Оберіть суму або 'Ввести вручну':",
        "custom_amount": "Введіть суму (наприклад 12.50):",
        "error_invalid_amount": "Невірна сума.",
        "result": "Результат: {amount} {from_curr} → {converted:.4f} {to_curr}\nКурс: {rate:.6f}",
        "api_error": "Не вдалося отримати курс.",
        "help_text": "Використай кнопки: Конвертувати → валюти → сума → результат.",
        "custom": "Ввести вручну",
        "back": "Назад"
    }
}

def L(lang, key):
    if lang not in LOCALES:
        lang = "en"
    return LOCALES[lang].get(key, key)

# In-memory per-user storage (simple)
user_lang = {}   # chat_id -> lang
user_state = {}  # chat_id -> {"from":..., "to":..., "amount":..., "awaiting": ...}

# Common currencies and amount presets
COMMON_CURRENCIES = ["USD","EUR","UAH","PLN","GBP","CHF","JPY","CAD","AUD","SEK"]
AMOUNTS = ["1","5","10","50","100"]

# Keyboards
def make_lang_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        InlineKeyboardButton("🇩🇪 Deutsch", callback_data="lang_de"),
        InlineKeyboardButton("🇵🇱 Polski", callback_data="lang_pl"),
        InlineKeyboardButton("🇺🇦 Українська", callback_data="lang_uk")
    )
    return kb

def main_menu_kb(lang):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(L(lang, "menu_convert"), callback_data="menu_convert"),
        InlineKeyboardButton(L(lang, "menu_change_lang"), callback_data="menu_change_lang"),
        InlineKeyboardButton(L(lang, "menu_help"), callback_data="menu_help")
    )
    return kb

def currencies_kb(prefix="from"):
    kb = InlineKeyboardMarkup(row_width=4)
    for c in COMMON_CURRENCIES:
        kb.insert(InlineKeyboardButton(c, callback_data=f"{prefix}_{c}"))
    kb.add(InlineKeyboardButton("🔎 Other", callback_data=f"{prefix}_OTHER"))
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="back_to_menu"))
    return kb

def amount_kb(lang):
    kb = InlineKeyboardMarkup(row_width=3)
    for a in AMOUNTS:
        kb.insert(InlineKeyboardButton(a, callback_data=f"amt_{a}"))
    kb.add(InlineKeyboardButton(L(lang, "custom"), callback_data="amt_CUSTOM"))
    kb.add(InlineKeyboardButton("⬅️ " + L(lang, "back"), callback_data="back_to_from"))
    return kb

# Exchange API call
def convert_currency(fr, to, amount):
    """Конвертація валют з підтримкою UAH (через НБУ або Frankfurter)"""
    try:
        fr = fr.upper()
        to = to.upper()

        # Якщо є UAH — беремо офіційні курси НБУ (UAH як база)
        if fr == "UAH" or to == "UAH":
            r = requests.get("https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json", timeout=8)
            data = r.json()

            # rates: код -> UAH за 1 одиницю валюти
            rates = {item["cc"]: float(item["rate"]) for item in data}
            rates["UAH"] = 1.0

            if fr not in rates or to not in rates:
                logging.warning("NBU: missing currency in rates: fr=%s to=%s", fr, to)
                return None

            # Правильна формула: rate_fr_to_to = rates[fr] / rates[to]
            rate = rates[fr] / rates[to]
            converted = amount * rate
            return {"converted": converted, "rate": rate}

        # Інакше — Frankfurter (не потребує ключа)
        url = f"https://api.frankfurter.app/latest?from={fr}&to={to}&amount={amount}"
        r = requests.get(url, timeout=8)
        data = r.json()

        rates = data.get("rates", {})
        if not rates or to not in rates:
            logging.warning("Frankfurter: missing rate for %s", to)
            return None

        # Frankfurter повертає вже сконвертовану суму в rates[to]
        converted = float(rates[to])
        # Щоб знати курс один до одного (1 fr -> ? to), запросимо amount=1
        try:
            r2 = requests.get(f"https://api.frankfurter.app/latest?from={fr}&to={to}&amount=1", timeout=8)
            r2data = r2.json()
            rate = float(r2data.get("rates", {}).get(to, converted))
        except Exception:
            rate = converted  # fallback
        return {"converted": converted, "rate": rate}

    except Exception:
        logging.exception("API error in convert_currency")
        return None


# Handlers
@dp.message_handler(commands=["start"])
async def start_cmd(msg: types.Message):
    chat = msg.chat.id
    lc = (msg.from_user.language_code or "en")[:2]
    if lc not in LANGS:
        lc = "en"
    user_lang[chat] = lc
    user_state.pop(chat, None)
    await msg.answer(L(lc, "start"), reply_markup=make_lang_kb())

@dp.callback_query_handler(lambda c: c.data and (c.data.startswith("lang_") or c.data in ["menu_convert","menu_change_lang","menu_help"]))
async def menu_cb(cq: types.CallbackQuery):
    chat = cq.message.chat.id
    data = cq.data
    if data.startswith("lang_"):
        lang = data.split("_",1)[1]
        user_lang[chat] = lang
        user_state.pop(chat, None)
        await bot.edit_message_text(L(lang, "start"), chat, cq.message.message_id, reply_markup=main_menu_kb(lang))
        await cq.answer()
        return
    lang = user_lang.get(chat, "en")
    if data == "menu_convert":
        user_state[chat] = {"awaiting": None}
        await bot.send_message(chat, L(lang, "prompt_from"), reply_markup=currencies_kb("from"))
    elif data == "menu_change_lang":
        await bot.send_message(chat, L(lang, "start"), reply_markup=make_lang_kb())
    elif data == "menu_help":
        await bot.send_message(chat, L(lang, "help_text"), reply_markup=main_menu_kb(lang))
    await cq.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_menu")
async def back_menu(cq: types.CallbackQuery):
    chat = cq.message.chat.id
    lang = user_lang.get(chat, "en")
    user_state.pop(chat, None)
    await bot.edit_message_text(L(lang, "start"), chat, cq.message.message_id, reply_markup=main_menu_kb(lang))
    await cq.answer()

@dp.callback_query_handler(lambda c: c.data == "back_to_from")
async def back_to_from(cq: types.CallbackQuery):
    chat = cq.message.chat.id
    lang = user_lang.get(chat, "en")
    user_state.setdefault(chat, {}).pop("from", None)
    await bot.edit_message_text(L(lang, "prompt_from"), chat, cq.message.message_id, reply_markup=currencies_kb("from"))
    await cq.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("from_"))
async def from_cb(cq: types.CallbackQuery):
    chat = cq.message.chat.id
    data = cq.data.split("_",1)[1]
    lang = user_lang.get(chat, "en")
    st = user_state.setdefault(chat, {"awaiting": None})
    if data == "OTHER":
        await bot.send_message(chat, L(lang, "prompt_from") + "\n(Type code, e.g. USD)")
        st["awaiting"] = "from_manual"
        await cq.answer()
        return
    st["from"] = data
    await bot.send_message(chat, L(lang, "prompt_to"), reply_markup=currencies_kb("to"))
    await cq.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("to_"))
async def to_cb(cq: types.CallbackQuery):
    chat = cq.message.chat.id
    data = cq.data.split("_",1)[1]
    lang = user_lang.get(chat, "en")
    st = user_state.setdefault(chat, {"awaiting": None})
    if data == "OTHER":
        await bot.send_message(chat, L(lang, "prompt_to") + "\n(Type code, e.g. EUR)")
        st["awaiting"] = "to_manual"
        await cq.answer()
        return
    st["to"] = data
    await bot.send_message(chat, L(lang, "prompt_amount"), reply_markup=amount_kb(lang))
    await cq.answer()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith("amt_"))
async def amt_cb(cq: types.CallbackQuery):
    chat = cq.message.chat.id
    data = cq.data.split("_",1)[1]
    lang = user_lang.get(chat, "en")
    st = user_state.setdefault(chat, {})
    if data == "CUSTOM":
        st["awaiting"] = "custom_amount"
        await bot.send_message(chat, L(lang, "custom_amount"))
        await cq.answer()
        return
    st["amount"] = float(data)
    if "from" in st and "to" in st:
        res = convert_currency(st["from"], st["to"], st["amount"])
        if not res:
            await bot.send_message(chat, L(lang, "api_error"), reply_markup=main_menu_kb(lang))
        else:
            await bot.send_message(chat, L(lang, "result").format(
                amount=st["amount"], from_curr=st["from"], converted=res["converted"], to_curr=st["to"], rate=res["rate"]
            ), reply_markup=main_menu_kb(lang))
        user_state.pop(chat, None)
    else:
        await bot.send_message(chat, "Currencies missing.", reply_markup=main_menu_kb(lang))
    await cq.answer()

@dp.message_handler()
async def text_handler(msg: types.Message):
    chat = msg.chat.id
    text = msg.text.strip()
    lang = user_lang.get(chat, "en")
    st = user_state.setdefault(chat, {"awaiting": None})
    if st.get("awaiting") == "from_manual":
        st["from"] = text.upper()
        st["awaiting"] = None
        await msg.reply(L(lang, "prompt_to"), reply_markup=currencies_kb("to"))
        return
    if st.get("awaiting") == "to_manual":
        st["to"] = text.upper()
        st["awaiting"] = None
        await msg.reply(L(lang, "prompt_amount"), reply_markup=amount_kb(lang))
        return
    if st.get("awaiting") == "custom_amount":
        s = text.replace(",",".")
        try:
            a = float(s)
            if a < 0:
                raise ValueError()
        except Exception:
            await msg.reply(L(lang, "error_invalid_amount"))
            return
        st["amount"] = a
        if "from" in st and "to" in st:
            res = convert_currency(st["from"], st["to"], st["amount"])
            if not res:
                await msg.reply(L(lang, "api_error"), reply_markup=main_menu_kb(lang))
            else:
                await msg.reply(L(lang, "result").format(
                    amount=st["amount"], from_curr=st["from"], converted=res["converted"], to_curr=st["to"], rate=res["rate"]
                ), reply_markup=main_menu_kb(lang))
            user_state.pop(chat, None)
        else:
            await msg.reply("Currencies not set.", reply_markup=main_menu_kb(lang))
        return

    if text.lower() in ("/start","start"):
        await start_cmd(msg)
        return
    if text.lower() in ("/convert","convert"):
        user_state[chat] = {"awaiting": None}
        await msg.reply(L(lang, "prompt_from"), reply_markup=currencies_kb("from"))
        return

    await msg.reply(L(lang, "help_text"), reply_markup=main_menu_kb(lang))

if __name__ == "__main__":
    print("MultiRateBot started...")
    executor.start_polling(dp, skip_updates=True)
