from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from config import REQUIRED_CHANNELS


def subscribe_keyboard():
    buttons = []
    for ch in REQUIRED_CHANNELS:
        channel = ch.strip()
        url = f"https://t.me/{channel.lstrip('@')}"
        buttons.append([InlineKeyboardButton(text=f"📢 {channel}", url=url)])
    buttons.append([
        InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎬 Film qo'shish"), KeyboardButton(text="🗑 Film o'chirish")],
            [KeyboardButton(text="📋 Filmlar ro'yxati"), KeyboardButton(text="📊 Statistika")],
            [KeyboardButton(text="📣 Xabar yuborish"), KeyboardButton(text="🔝 Top filmlar")],
            [KeyboardButton(text="❌ Admindan chiqish")],
        ],
        resize_keyboard=True
    )


def cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )


def movie_keyboard(code):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔁 Qayta yuklab olish", callback_data=f"reget:{code}")]
    ])
