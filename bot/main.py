import asyncio
import logging
import os
from dataclasses import dataclass

from aiogram import Bot, Dispatcher
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from backend.config import BOT_TOKEN
from backend.odoo_client import OdooVideoDraft, odoo_client
from bot.downloader import download_file
from services.audio import extract_audio, trim_silence
from services.content import build_content_pack
from services.transcription import transcribe

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

VIDEO_PATH = "data/videos/video.mp4"
RAW_AUDIO_PATH = "data/audio/audio_raw.wav"
TRIMMED_AUDIO_PATH = "data/audio/audio_trimmed.wav"


@dataclass
class DraftState:
    transcription: str
    content_preview: str
    vk_post: str
    title: str
    description: str
    hashtags: str
    release_target: str | None = None
    edit_field: str | None = None


USER_DRAFTS: dict[int, DraftState] = {}


def _build_draft_message(state: DraftState) -> str:
    return (
        f"📝 Транскрипт (фрагмент):\n{state.transcription[:700]}\n\n"
        f"📣 Текст поста VK:\n{state.vk_post}\n\n"
        f"🏷 Заголовок:\n{state.title}\n\n"
        f"📄 Описание:\n{state.description}\n\n"
        f"#️⃣ Хэштеги:\n{state.hashtags}"
    )


def _build_edit_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить текст VK", callback_data="edit:vk_post")],
            [InlineKeyboardButton(text="✏️ Изменить заголовок", callback_data="edit:title")],
            [InlineKeyboardButton(text="✏️ Изменить описание", callback_data="edit:description")],
            [InlineKeyboardButton(text="✏️ Изменить хэштеги", callback_data="edit:hashtags")],
            [InlineKeyboardButton(text="🚀 Релиз", callback_data="release:start")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="publish:cancel")],
        ]
    )


@dp.message(lambda message: message.video is not None)
async def handle_video(message: Message):
    await message.answer("📥 Скачиваю видео...")

    file = await bot.get_file(message.video.file_id)
    path = file.file_path

    await download_file(path, VIDEO_PATH)

    await message.answer("🎧 Извлекаю аудио и очищаю паузы...")
    extract_audio(VIDEO_PATH, RAW_AUDIO_PATH)
    trim_silence(RAW_AUDIO_PATH, TRIMMED_AUDIO_PATH)

    await message.answer("🧠 Транскрибирую...")
    text = transcribe(TRIMMED_AUDIO_PATH)

    content_pack = await build_content_pack(text)

    state = DraftState(
        transcription=text,
        content_preview="",
        vk_post=content_pack.vk_post,
        title=content_pack.title,
        description=content_pack.description,
        hashtags=content_pack.hashtags,
    )
    preview = _build_draft_message(state)
    state.content_preview = preview

    job_id = odoo_client.create_video_job(
        OdooVideoDraft(
            telegram_user_id=message.from_user.id,
            transcription=text,
            preview=preview,
        )
    )

    USER_DRAFTS[message.from_user.id] = state

    await message.answer(preview)
    if job_id:
        await message.answer(f"🧾 Черновик синхронизирован с Odoo (video.job #{job_id}).")
    await message.answer(
        "Выберите действие: отредактировать элементы поста или перейти к релизу.",
        reply_markup=_build_edit_kb(),
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("publish:"))
async def handle_publish_decision(call: CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split(":", maxsplit=1)[1]

    try:
        await call.message.delete()
    except TelegramBadRequest:
        pass

    if action in {"vk", "telegram", "dzen"} and user_id in USER_DRAFTS:
        USER_DRAFTS[user_id].release_target = action
        await call.message.answer(f"Площадка выбрана: {action.upper()}. Нажмите «Опубликовать в выбранное» для подтверждения.")
    elif action == "confirm" and user_id in USER_DRAFTS:
        target = USER_DRAFTS[user_id].release_target or "VK"
        await call.message.answer(
            "🚀 Публикация запущена (MVP-режим):\n"
            f"• {target} пост\n\n"
            "Следующий шаг: подключить реальные API площадок и Odoo job queue."
        )
    else:
        await call.message.answer("Ок, публикация отменена.")

    await call.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("edit:"))
async def handle_edit(call: CallbackQuery):
    user_id = call.from_user.id
    state = USER_DRAFTS.get(user_id)
    if not state:
        await call.answer("Нет активного черновика", show_alert=True)
        return

    field = call.data.split(":", maxsplit=1)[1]
    state.edit_field = field
    labels = {
        "vk_post": "текст поста VK",
        "title": "заголовок",
        "description": "описание",
        "hashtags": "хэштеги",
    }
    await call.message.answer(f"Введите новый(ую) {labels.get(field, 'текст')} одним сообщением.")
    await call.answer()


@dp.callback_query(lambda c: c.data == "release:start")
async def handle_release_start(call: CallbackQuery):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="VK", callback_data="publish:vk")],
            [InlineKeyboardButton(text="Telegram", callback_data="publish:telegram")],
            [InlineKeyboardButton(text="Дзен", callback_data="publish:dzen")],
            [InlineKeyboardButton(text="✅ Опубликовать в выбранное", callback_data="publish:confirm")],
        ]
    )
    await call.message.answer("Выберите площадку для релиза (MVP: выбор одной площадки).", reply_markup=kb)
    await call.answer()


@dp.message(lambda message: message.from_user and message.from_user.id in USER_DRAFTS)
async def handle_edit_input(message: Message):
    state = USER_DRAFTS.get(message.from_user.id)
    if not state or not state.edit_field:
        return

    value = message.text.strip() if message.text else ""
    if not value:
        await message.answer("Пустой текст не сохранен. Пришлите непустое значение.")
        return

    if state.edit_field == "vk_post":
        state.vk_post = value
    elif state.edit_field == "title":
        state.title = value
    elif state.edit_field == "description":
        state.description = value
    elif state.edit_field == "hashtags":
        state.hashtags = value

    state.edit_field = None
    state.content_preview = _build_draft_message(state)
    await message.answer("✅ Обновлено. Актуальный черновик:")
    await message.answer(state.content_preview, reply_markup=_build_edit_kb())


@dp.message()
async def fallback(message: Message):
    await message.answer("Пришли видео 🎥")


async def main():
    os.makedirs("data/videos", exist_ok=True)
    os.makedirs("data/audio", exist_ok=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
