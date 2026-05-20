import base64
import logging
import os
import tempfile
from typing import Optional

import aiohttp


logger = logging.getLogger(__name__)


async def extract_main_idea(text: str) -> str:
    source = (text or "").strip()
    if not source:
        return "абстрактная иллюстрация на тему контента"

    ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

    prompt = (
        "Выдели главную мысль в 1 коротком предложении на русском языке. "
        "Без списков и пояснений, только итоговая мысль.\n\n"
        f"Текст:\n{source[:6000]}"
    )

    payload = {"model": model, "prompt": prompt, "stream": False}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{ollama_url}/api/generate", json=payload, timeout=30) as response:
                response.raise_for_status()
                data = await response.json()
                idea = str(data.get("response", "")).strip()
                return idea or source[:200]
    except Exception:
        return source[:200]


async def generate_image_by_text(main_idea: str) -> Optional[str]:
    api_url = os.getenv("SD_API_URL", "http://127.0.0.1:7860")
    prompt_prefix = os.getenv(
        "SD_PROMPT_PREFIX",
        "cinematic illustration, detailed, high quality, visually appealing,",
    )
    negative_prompt = os.getenv(
        "SD_NEGATIVE_PROMPT",
        "lowres, blurry, watermark, text, logo, artifacts",
    )

    payload = {
        "prompt": f"{prompt_prefix} {main_idea}",
        "negative_prompt": negative_prompt,
        "steps": int(os.getenv("SD_STEPS", "25")),
        "width": int(os.getenv("SD_WIDTH", "768")),
        "height": int(os.getenv("SD_HEIGHT", "768")),
        "cfg_scale": float(os.getenv("SD_CFG_SCALE", "7")),
        "sampler_name": os.getenv("SD_SAMPLER", "Euler a"),
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{api_url}/sdapi/v1/txt2img", json=payload, timeout=180) as response:
                response.raise_for_status()
                data = await response.json()
                images = data.get("images") or []
                if not images:
                    return None

                raw = base64.b64decode(images[0])
                out_dir = os.getenv("GENERATED_IMAGE_DIR", tempfile.gettempdir())
                os.makedirs(out_dir, exist_ok=True)
                path = os.path.join(out_dir, "generated_preview.png")
                with open(path, "wb") as f:
                    f.write(raw)
                return path
    except Exception as exc:
        logger.exception("Ошибка генерации изображения через SD API: %s", exc)
        return None
