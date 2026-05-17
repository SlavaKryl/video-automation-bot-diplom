# video-automation-bot-diplom

MVP-бот для автообработки видео и подготовки кроссплатформенных публикаций.

## Что уже умеет

- Принимает видео в Telegram.
- Скачивает исходник.
- Извлекает аудио (`ffmpeg`).
- Обрезает длительные паузы/тишину (`silenceremove`).
- Транскрибирует через `faster-whisper`.
- Готовит черновики:
  - подпись для reels/shorts,
  - посты для VK, Telegram, Дзен, MAX,
  - описание для RuTube.
- Показывает превью пользователю и запрашивает подтверждение публикации.
- Эмулирует шаг публикации (MVP-заглушка).

## Ближайший roadmap до рабочего MVP

1. **Публикация в реальные каналы**
   - YouTube Data API / Shorts upload.
   - VK API: клипы + посты.
   - RuTube API.
   - Telegram Bot/API для постинга в канал.
2. **Интеграция с Odoo**
   - Отдельный модуль `video_automation`.
   - Модели: `video.job`, `video.asset`, `video.publication`.
   - Очередь фоновых задач (cron/queue_job).
   - UI в Odoo для статусов, ручного апрува и ретраев.
3. **Качество контента**
   - Удаление слов-паразитов (LLM/regex этап после транскрибации).
   - Автогенерация title/description/hashtags под площадку.
   - Генерация превью-картинки по контексту (DALL·E/SDXL).
4. **Надежность**
   - Валидация длины и формата видео.
   - Ограничения по ресурсам и таймаутам.
   - Логи, мониторинг, таблица ошибок.

## Запуск

```bash
pip install -r requirements.txt
python -m bot.main
```

### Переменные окружения (Odoo)

```bash
export ODOO_ENABLED=true
export ODOO_URL=http://localhost:8069
export ODOO_DB=odoo_db
export ODOO_USERNAME=admin
export ODOO_PASSWORD=admin
```

При включенной интеграции бот будет создавать `video.job` в Odoo после формирования черновика.

### Локальный Odoo для интеграции

```bash
docker compose up -d db odoo
# Установка модуля с моделью video.job
docker compose exec -T odoo odoo -d odoo -i video_automation --stop-after-init
```

Структура модуля: `odoo/addons/video_automation` (модель `video.job` + права доступа).

### Smoke-тест интеграции Odoo

```bash
./scripts/test_odoo_integration.sh
```

Если в вашей локальной Odoo пароль администратора отличается от `admin`, обновите `ODOO_PASSWORD` в окружении и в скрипте smoke-теста.

## Минимальная архитектура (эволюционно)

- `bot/` — Telegram-интерфейс и сценарий диалога.
- `services/` — обработка медиа, транскрибация, генерация текстов.
- `backend/` — API/healthcheck (точка для будущей интеграции с Odoo).

