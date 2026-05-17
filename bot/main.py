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


USER_DRAFTS: dict[int, DraftState] = {}


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

    content_pack = build_content_pack(text)
    preview = (
        f"📝 Транскрипт (фрагмент):\n{text[:700]}\n\n"
        f"📣 Черновик поста VK:\n{content_pack.vk_post[:500]}"
    )

    job_id = odoo_client.create_video_job(
        OdooVideoDraft(
            telegram_user_id=message.from_user.id,
            transcription=text,
            preview=preview,
        )
    )

    USER_DRAFTS[message.from_user.id] = DraftState(
        transcription=text,
        content_preview=preview,
    )

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить публикацию", callback_data="publish:confirm")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="publish:cancel")],
        ]
    )

    await message.answer(preview)
    if job_id:
        await message.answer(f"🧾 Черновик синхронизирован с Odoo (video.job #{job_id}).")
    await message.answer(
        "Проверить черновик и подтвердить публикацию в выбранные каналы?\n"
        "(Сейчас это MVP-заглушка, публикация эмулируется)",
        reply_markup=kb,
    )


@dp.callback_query(lambda c: c.data and c.data.startswith("publish:"))
async def handle_publish_decision(call: CallbackQuery):
    user_id = call.from_user.id
    action = call.data.split(":", maxsplit=1)[1]

    try:
        await call.message.delete()
    except TelegramBadRequest:
        pass

    if action == "confirm" and user_id in USER_DRAFTS:
        await call.message.answer(
            "🚀 Публикация запущена (MVP-режим):\n"
            "• YouTube Shorts\n• VK Clips\n• RuTube\n• VK/Дзен/Telegram/MAX посты\n\n"
            "Следующий шаг: подключить реальные API площадок и Odoo job queue."
        )
    else:
        await call.message.answer("Ок, публикация отменена.")

    await call.answer()


@dp.message()
async def fallback(message: Message):
    await message.answer("Пришли видео 🎥")


async def main():
    os.makedirs("data/videos", exist_ok=True)
    os.makedirs("data/audio", exist_ok=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
