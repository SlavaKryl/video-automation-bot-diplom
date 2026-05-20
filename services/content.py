import re
import os
from dataclasses import dataclass

import aiohttp


@dataclass
class ContentPack:
    reel_caption: str
    vk_post: str
    telegram_post: str
    dzen_post: str
    max_post: str
    rutube_caption: str
    title: str
    description: str
    hashtags: str


def _normalize_transcription(transcription: str) -> str:
    text = transcription.strip()
    text = re.sub(r"\s+", " ", text)
    # readability for cases like "1,2,3,1,2,3"
    text = re.sub(r",(?=\S)", ", ", text)
    return text


async def _rewrite_with_ollama(source_text: str) -> str:
    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    prompt = (
        "Перепиши текст поста на русском языке для соцсетей. "
        "Сохрани смысл, сделай короче и живее, без выдумывания фактов. "
        "Верни только готовый текст поста без пояснений.\n\n"
        f"Исходный текст:\n{source_text}"
    )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{ollama_url}/api/generate", json=payload, timeout=20) as response:
                response.raise_for_status()
                data = await response.json()
                rewritten = str(data.get("response", "")).strip()
                return rewritten or source_text
    except Exception:
        return source_text


async def build_content_pack(transcription: str) -> ContentPack:
    short = _normalize_transcription(transcription)

    if not short:
        short = "(Не удалось распознать текст. Нужна ручная правка черновика.)"

    teaser = short[:280] + ("..." if len(short) > 280 else "")
    refined_teaser = await _rewrite_with_ollama(teaser)

    hook = "Новый фрагмент из видео"
    hashtags = "#видео #контент #автоматизация"
    description = f"Короткий разбор: {teaser}"
    title = short[:70] if short else "Новый видеофрагмент"

    reel_caption = f"{hook}\n\n{refined_teaser}\n\n#shorts #reels {hashtags}"
    vk_post = f"{hook}\n\n{refined_teaser}\n\n{hashtags}"
    telegram_post = f"{hook}\n\n{refined_teaser}\n\n{hashtags}"
    dzen_post = f"{hook}\n\n{short[:700]}\n\n{hashtags}"
    max_post = f"{hook}\n\n{refined_teaser}\n\n{hashtags}"
    rutube_caption = f"{title}\n\n{description}\n\n{hashtags}"

    return ContentPack(
        reel_caption=reel_caption,
        vk_post=vk_post,
        telegram_post=telegram_post,
        dzen_post=dzen_post,
        max_post=max_post,
        rutube_caption=rutube_caption,
        title=title,
        description=description,
        hashtags=hashtags,
    )
