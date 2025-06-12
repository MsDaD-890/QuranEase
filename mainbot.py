import telebot
from telebot import types
from dotenv import load_dotenv
import os
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# ✅ Сессия с retry
session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3, status_forcelist=(500, 502, 504))
adapter = HTTPAdapter(max_retries=retry)
session.mount("https://", adapter)
session.mount("http://", adapter)

current_surah = None
current_ayah = None

def get_all_surahs():
    url = "https://api.alquran.cloud/v1/surah"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'OK':
                return [f"{s['number']}. {s['englishName']}" for s in data['data']]
    except Exception as e:
        print(f"[Surahs error] {e}")
    return []

def split_and_send_text(chat_id, text):
    MAX_LENGTH = 4000
    for i in range(0, len(text), MAX_LENGTH):
        bot.send_message(chat_id, text[i:i + MAX_LENGTH])

def get_ayah_details(surah_number, ayah_number):
    try:
        url_ar = f"https://api.alquran.cloud/v1/ayah/{surah_number}:{ayah_number}/ar.alafasy"
        url_ru = f"https://api.alquran.cloud/v1/ayah/{surah_number}:{ayah_number}/ru.kuliev"
        url_en = f"https://api.alquran.cloud/v1/ayah/{surah_number}:{ayah_number}/en.asad"

        ar_data = session.get(url_ar, timeout=10).json()
        ru_data = session.get(url_ru, timeout=10).json()
        en_data = session.get(url_en, timeout=10).json()

        if ar_data["status"] == "OK" and ru_data["status"] == "OK" and en_data["status"] == "OK":
            return (
                ar_data['data']['text'],
                ru_data['data']['text'],
                en_data['data']['text'],
                ar_data['data']['audio']
            )
    except Exception as e:
        print(f"[Ayah error] {e}")
    return None


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📖 Surah", callback_data='surah'))

    bot.send_message(
        message.chat.id,
        f"Assalamu alaykum {message.from_user.first_name} 🌙\n"
        "Welcome!\nThis bot will help you listen, read and understand the Quran.\n"
        "Choose a surah or a ayah — and start your journey ✨\n\n"
        f"Ассаляму алейкум {message.from_user.first_name} 🌙\n"
        "Добро пожаловать!\nЭтот бот поможет тебе слушать, читать и понимать Коран.\n"
        "Выбери суру — и начни путь ✨",
        reply_markup=markup
    )


@bot.callback_query_handler(func=lambda call: call.data == 'surah')
def show_surahs(call):
    surah_list = get_all_surahs()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for surah in surah_list:
        markup.add(types.KeyboardButton(surah))
    markup.add(types.KeyboardButton("🔙 Назад/ \n🔙 Back"))
    bot.send_message(call.message.chat.id, "📖 Выбери суру / \n📖 Choose the surah:", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "🔙 Назад/ \n🔙 Back")
def go_back(message):
    start(message)


@bot.message_handler(func=lambda m: m.text.split('.')[0].isdigit())
def handle_surah_selection(message):
    global current_surah, current_ayah
    try:
        current_surah = int(message.text.split('.')[0])
        current_ayah = 1
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат суры.")
        return

    url = f"https://api.alquran.cloud/v1/surah/{current_surah}/en.asad"
    try:
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            name = data["data"]["englishName"]
            ayahs = data["data"]["ayahs"]
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
            for ayah in ayahs:
                markup.add(types.KeyboardButton(f"{current_surah} {ayah['numberInSurah']}"))
            markup.add(types.KeyboardButton("🔙 Назад/ \n🔙 Back"))
            bot.send_message(message.chat.id, f"📘 {name} — выбери аят/ \n choose the ayah:", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ Сура не найдена.")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка запроса: {e}")


def get_total_ayahs(surah_number):
    try:
        response = session.get(f"https://api.alquran.cloud/v1/surah/{surah_number}/en.asad", timeout=10)
        if response.status_code == 200:
            return len(response.json()['data']['ayahs'])
    except Exception as e:
        print(f"[Total Ayahs error] {e}")
    return None


@bot.message_handler(func=lambda m: len(m.text.split()) == 2 and m.text.split()[0].isdigit())
def show_ayah(message):
    global current_surah, current_ayah
    try:
        surah_num, ayah_num = map(int, message.text.split())
        current_surah = surah_num
        current_ayah = ayah_num
        send_ayah(message.chat.id, surah_num, ayah_num)
    except:
        bot.send_message(message.chat.id, "❌ Неправильный формат аята.")


def send_ayah(chat_id, surah_num, ayah_num):
    ayah = get_ayah_details(surah_num, ayah_num)
    if ayah:
        arabic, rus, eng, audio = ayah
        text = f"""
🕋 Ayah {ayah_num} of Surah {surah_num}
📖 Arabic: {arabic}
🇷🇺 Русский: {rus}
🇬🇧 English: {eng}
        """
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            types.KeyboardButton("◀️ Предыдущий аят/ \n ◀️ Previous ayah"),
            types.KeyboardButton("▶️ Следующий аят/ \n ▶️ Next ayah")
        )
        markup.add(types.KeyboardButton("🔙 Назад/ \n🔙 Back"))
        bot.send_message(chat_id, text.strip(), reply_markup=markup)
        bot.send_audio(chat_id, audio)
    else:
        bot.send_message(chat_id, "❌ Не удалось получить информацию об аяте.")


@bot.message_handler(func=lambda message: message.text.startswith("▶️ Следующий аят/ \n ▶️ Next ayah"))
def next_ayah(message):
    global current_surah, current_ayah
    if current_surah and current_ayah:
        total = get_total_ayahs(current_surah)
        if current_ayah < total:
            current_ayah += 1
            send_ayah(message.chat.id, current_surah, current_ayah)
        else:
            bot.send_message(message.chat.id, "✅ Это последний аят.")
    else:
        bot.send_message(message.chat.id, "⚠️ Сначала выбери суру и аят.")


@bot.message_handler(func=lambda message: message.text.startswith("◀️ Предыдущий аят/ \n ◀️ Previous ayah"))
def previous_ayah(message):
    global current_surah, current_ayah
    if current_surah and current_ayah > 1:
        current_ayah -= 1
        send_ayah(message.chat.id, current_surah, current_ayah)
    else:
        bot.send_message(message.chat.id, "⚠️ Ты уже на первом аяте или не выбрана сура.")


@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "ℹ️Инструкция:\n"
        "• /start — начать заново\n"
        "• Выбери суру, затем аят — и получишь текст и аудио."
    )


@bot.message_handler(content_types=['text'])
def handle_text(message):
    bot.send_message(message.chat.id, "❗ Команда не распознана.\nНапиши /start, чтобы начать заново.")


while True:
    try:
        bot.polling(none_stop=True, timeout=60, long_polling_timeout=45)
    except Exception as e:
        print(f"[Bot error] {e}")
        time.sleep(5)
