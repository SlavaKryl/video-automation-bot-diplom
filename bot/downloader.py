import aiohttp
import aiofiles
from backend.config import BOT_TOKEN


async def download_file(file_path: str, dest: str):
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.read()

    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)