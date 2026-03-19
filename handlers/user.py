import re
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

from config import REQUIRED_CHANNELS
from database import upsert_user, get_movie, increment_views, log_request
from keyboards import subscribe_keyboard, movie_keyboard

router = Router()


async def check_subscription(bot: Bot, user_id: int) -> bool:
    for channel in REQUIRED_CHANNELS:
        channel = channel.strip()
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except Exception:
            return False
    return True


@router.message(CommandStart())
async def start_handler(message: Message, bot: Bot):
    user = message.from_user
    await upsert_user(user.id, user.username or "", user.full_name)

    args = message.text.split(maxsplit=1)
    code = args[1].upper() if len(args) > 1 else None

    subscribed = await check_subscription(bot, user.id)
    if not subscribed:
        await message.answer(
            "🎬 <b>KinoBot'ga xush kelibsiz!</b>\n\n"
            "Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling 👇",
            reply_markup=subscribe_keyboard(),
            parse_mode="HTML"
        )
        return

    if code:
        await send_movie(message, bot, code)
        return

    await message.answer(
        "🎬 <b>KinoBot'ga xush kelibsiz!</b>\n\n"
        "Film topish uchun uning <b>kodini</b> yuboring.\n"
        "Misol: <code>#A1</code> yoki shunchaki <code>A1</code>\n\n"
        "📌 Kodlarni kanalimizdan topishingiz mumkin!",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    subscribed = await check_subscription(bot, callback.from_user.id)
    if not subscribed:
        await callback.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
        return

    await callback.message.edit_text(
        "✅ <b>Obuna tasdiqlandi!</b>\n\n"
        "Endi film kodini yuboring. Misol: <code>#A1</code>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("reget:"))
async def reget_callback(callback: CallbackQuery, bot: Bot):
    code = callback.data.split(":", 1)[1]
    await send_movie(callback.message, bot, code, from_user_id=callback.from_user.id)
    await callback.answer()


@router.message(F.text)
async def text_handler(message: Message, bot: Bot):
    user = message.from_user
    await upsert_user(user.id, user.username or "", user.full_name)

    subscribed = await check_subscription(bot, user.id)
    if not subscribed:
        await message.answer(
            "⛔ Avval kanallarga obuna bo'ling!",
            reply_markup=subscribe_keyboard()
        )
        return

    text = message.text.strip()
    code = re.sub(r'^#', '', text).upper()

    if not code:
        return

    await send_movie(message, bot, code)


async def send_movie(message: Message, bot: Bot, code: str, from_user_id: int = None):
    movie = await get_movie(code)

    if not movie:
        await log_request(from_user_id or message.from_user.id, code, False)
        await message.answer(
            f"❌ <b>#{code}</b> kodli film topilmadi.\n\n"
            "🔍 Kodni to'g'ri yozganingizni tekshiring.",
            parse_mode="HTML"
        )
        return

    await increment_views(code)
    await log_request(from_user_id or message.from_user.id, code, True)

    caption = (
        f"🎬 <b>{movie['title']}</b>\n"
        f"🔑 Kod: <code>#{movie['code']}</code>\n"
        f"👁 Ko'rishlar: {movie['views'] + 1}\n"
    )
    if movie['description']:
        caption += f"\n📝 {movie['description']}"

    send_kwargs = dict(
        chat_id=message.chat.id,
        caption=caption,
        parse_mode="HTML",
        reply_markup=movie_keyboard(code)
    )

    try:
        if movie['file_type'] == 'video':
            await bot.send_video(video=movie['file_id'], **send_kwargs)
        elif movie['file_type'] == 'document':
            await bot.send_document(document=movie['file_id'], **send_kwargs)
        elif movie['file_type'] == 'audio':
            await bot.send_audio(audio=movie['file_id'], **send_kwargs)
        else:
            await bot.send_video(video=movie['file_id'], **send_kwargs)
    except Exception as e:
        await message.answer(f"⚠️ Xatolik yuz berdi: {e}")
