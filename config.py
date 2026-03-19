import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8656934722:AAGSQrpPT25KJbkSYS2KesC-Bh139_nRNbc")

ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "7257755738").split(",")))

REQUIRED_CHANNELS = os.getenv("REQUIRED_CHANNELS", "@kodli_filmlar5").split(",")

DB_PATH = os.getenv("DB_PATH", "data/kinobot.db")
