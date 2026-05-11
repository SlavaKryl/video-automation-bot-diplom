import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.types import Message

from backend.config import BOT_TOKEN
from bot.downloader import download_file
from services.audio import extract_audio
from services.transcription import transcribe

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

VIDEO_PATH = "data/videos/video.mp4"
AUDIO_PATH = "data/audio/audio.wav"


@dp.message(lambda message: message.video is not None)
async def handle_video(message: Message):
    await message.answer("📥 Скачиваю видео...")

    file = await bot.get_file(message.video.file_id)
    path = file.file_path

    await download_file(path, VIDEO_PATH)

    await message.answer("🎧 Извлекаю аудио...")
    extract_audio(VIDEO_PATH, AUDIO_PATH)

    await message.answer("🧠 Транскрибирую...")

    text = transcribe(AUDIO_PATH)

    await message.answer(f"📝 Результат:\n{text[:1000]}")


@dp.message()
async def fallback(message: Message):
    await message.answer("Пришли видео 🎥")


async def main():
    os.makedirs("data/videos", exist_ok=True)
    os.makedirs("data/audio", exist_ok=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())