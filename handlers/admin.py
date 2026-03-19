import asyncio
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import (
    add_movie, delete_movie, get_all_movies, count_movies,
    count_users, get_top_movies, get_stats, get_all_user_ids
)
from keyboards import admin_main_keyboard, cancel_keyboard

router = Router()


class AddMovie(StatesGroup):
    waiting_code = State()
    waiting_title = State()
    waiting_description = State()
    waiting_file = State()


class DeleteMovie(StatesGroup):
    waiting_code = State()


class Broadcast(StatesGroup):
    waiting_message = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    await state.clear()
    await message.answer(
        "👨‍💼 <b>Admin Panel</b>\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "❌ Admindan chiqish")
async def exit_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    from aiogram.types import ReplyKeyboardRemove
    await message.answer("✅ Admin paneldan chiqdingiz.", reply_markup=ReplyKeyboardRemove())


@router.message(F.text == "🎬 Film qo'shish")
async def add_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddMovie.waiting_code)
    await message.answer(
        "📝 Film kodini kiriting:\nMisol: <code>A1</code> yoki <code>BATMAN</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(AddMovie.waiting_code)
async def add_movie_code(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    code = message.text.strip().upper().replace("#", "")
    if not code:
        await message.answer("⚠️ Kod bo'sh bo'lmasligi kerak!")
        return
    await state.update_data(code=code)
    await state.set_state(AddMovie.waiting_title)
    await message.answer(f"✅ Kod: <code>#{code}</code>\n\n📝 Endi film nomini kiriting:", parse_mode="HTML")


@router.message(AddMovie.waiting_title)
async def add_movie_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovie.waiting_description)
    await message.answer(
        "📝 Film haqida qisqacha tavsif kiriting.\n"
        "(O'tkazib yuborish uchun <code>-</code> yuboring)",
        parse_mode="HTML"
    )


@router.message(AddMovie.waiting_description)
async def add_movie_description(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    desc = "" if message.text.strip() == "-" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddMovie.waiting_file)
    await message.answer("🎬 Endi film faylini yuboring (video, document yoki audio):")


@router.message(AddMovie.waiting_file)
async def add_movie_file(message: Message, state: FSMContext):
    if message.text and message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    file_id = None
    file_type = None
    if message.video:
        file_id = message.video.file_id
        file_type = "video"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    elif message.audio:
        file_id = message.audio.file_id
        file_type = "audio"
    else:
        await message.answer("⚠️ Iltimos, video, document yoki audio fayl yuboring!")
        return
    data = await state.get_data()
    await add_movie(
        code=data['code'],
        title=data['title'],
        description=data['description'],
        file_id=file_id,
        file_type=file_type,
        added_by=message.from_user.id
    )
    await state.clear()
    await message.answer(
        f"✅ <b>Film muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🔑 Kod: <code>#{data['code']}</code>\n"
        f"🎬 Nomi: {data['title']}\n"
        f"📁 Turi: {file_type}",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "🗑 Film o'chirish")
async def delete_movie_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(DeleteMovie.waiting_code)
    await message.answer(
        "🗑 O'chirmoqchi bo'lgan film kodini kiriting:\nMisol: <code>A1</code>",
        reply_markup=cancel_keyboard(),
        parse_mode="HTML"
    )


@router.message(DeleteMovie.waiting_code)
async def delete_movie_code(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    code = message.text.strip().upper().replace("#", "")
    await delete_movie(code)
    await state.clear()
    await message.answer(
        f"✅ <code>#{code}</code> kodli film o'chirildi.",
        reply_markup=admin_main_keyboard(),
        parse_mode="HTML"
    )


@router.message(F.text == "📋 Filmlar ro'yxati")
async def movie_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    movies = await get_all_movies(limit=20)
    total = await count_movies()
    if not movies:
        await message.answer("📭 Hali hech qanday film yo'q.")
        return
    text = f"🎬 <b>Filmlar ro'yxati</b> (Jami: {total})\n\n"
    for m in movies:
        text += f"• <code>#{m['code']}</code> — {m['title']} 👁{m['views']}\n"
    if total > 20:
        text += f"\n... va yana {total - 20} ta film"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📊 Statistika")
async def statistics(message: Message):
    if not is_admin(message.from_user.id):
        return
    users = await count_users()
    movies = await count_movies()
    stats = await get_stats()
    text = (
        "📊 <b>Bot Statistikasi</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{users}</b>\n"
        f"🎬 Jami filmlar: <b>{movies}</b>\n\n"
        f"🔍 Jami so'rovlar: <b>{stats['total_requests']}</b>\n"
        f"✅ Muvaffaqiyatli: <b>{stats['found_requests']}</b>\n"
        f"📅 Bugungi so'rovlar: <b>{stats['today_requests']}</b>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "🔝 Top filmlar")
async def top_movies(message: Message):
    if not is_admin(message.from_user.id):
        return
    movies = await get_top_movies(10)
    if not movies:
        await message.answer("📭 Hali hech qanday film yo'q.")
        return
    text = "🏆 <b>Top 10 eng ko'p ko'rilgan filmlar:</b>\n\n"
    for i, m in enumerate(movies, 1):
        text += f"{i}. <code>#{m['code']}</code> — {m['title']} 👁 {m['views']}\n"
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📣 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(Broadcast.waiting_message)
    await message.answer(
        "📣 Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:",
        reply_markup=cancel_keyboard()
    )


@router.message(Broadcast.waiting_message)
async def broadcast_send(message: Message, state: FSMContext, bot: Bot):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=admin_main_keyboard())
        return
    await state.clear()
    user_ids = await get_all_user_ids()
    await message.answer(
        f"⏳ Xabar {len(user_ids)} ta foydalanuvchiga yuborilmoqda...",
        reply_markup=admin_main_keyboard()
    )
    success = 0
    failed = 0
    for uid in user_ids:
        try:
            await message.copy_to(uid)
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
    await message.answer(
        f"✅ Xabar yuborildi!\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Xatolik: {failed}"
