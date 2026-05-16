import re
from dataclasses import dataclass


@dataclass
class ContentPack:
    reel_caption: str
    vk_post: str
    telegram_post: str
    dzen_post: str
    max_post: str
    rutube_caption: str


def _normalize_transcription(transcription: str) -> str:
    text = transcription.strip()
    text = re.sub(r"\s+", " ", text)
    # readability for cases like "1,2,3,1,2,3"
    text = re.sub(r",(?=\S)", ", ", text)
    return text


def build_content_pack(transcription: str) -> ContentPack:
    short = _normalize_transcription(transcription)

    if not short:
        short = "(Не удалось распознать текст. Нужна ручная правка черновика.)"

    teaser = short[:280] + ("..." if len(short) > 280 else "")

    hook = "🎬 Новый фрагмент из видео"
    cta = "Напишите в комментариях, если хотите продолжение по этой теме."

    reel_caption = f"{hook}\n\n{teaser}\n\n#shorts #reels"
    vk_post = f"{hook} для VK:\n\n{teaser}\n\n{cta}"
    telegram_post = f"{hook} для Telegram:\n\n{teaser}\n\n{cta}"
    dzen_post = f"{hook} для Дзен:\n\n{short[:700]}\n\n{cta}"
    max_post = f"{hook} для MAX:\n\n{teaser}"
    rutube_caption = f"{hook} для RuTube:\n\n{teaser}"

    return ContentPack(
        reel_caption=reel_caption,
        vk_post=vk_post,
        telegram_post=telegram_post,
        dzen_post=dzen_post,
        max_post=max_post,
        rutube_caption=rutube_caption,
    )
