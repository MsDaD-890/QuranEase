# "QuranEase" Telegram Bot 📖🤖

This is a Telegram bot that helps users **read**, **listen to**, and **understand** the Quran in **Arabic**, **Russian**, and **English**.

## 🌟 Features
- Browse and select any Surah and Ayah
- Get translation in 3 languages (AR / RU / EN)
- Listen to the audio recitation (Alafasy)
- Navigate between ayahs (next / previous)
- Simple and multilingual interface

## 🛠️ Technologies Used
- Python 3
- pyTelegramBotAPI (telebot)
- AlQuran Cloud API
- dotenv for managing secrets
- requests with retry logic

## 📦 Installation

```bash
git clone https://github.com/MsDaD-890/QuranEase.git
cd quran-telegram-bot
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
