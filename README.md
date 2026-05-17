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
export ODOO_DB=odoo
export ODOO_USERNAME=admin
export ODOO_PASSWORD=admin
```

При включенной интеграции бот будет создавать `video.job` в Odoo после формирования черновика.

### Локальный Odoo для интеграции

### Запуск одной командой

Поднять Odoo + Postgres, дождаться готовности, инициализировать БД и установить модуль:

```bash
make odoo-up
```

Поднять всё (Odoo + backend + bot) одной командой:

```bash
BOT_TOKEN=your_token make dev-all
```

> `make dev-all` запускает backend и bot в текущем окружении Python после успешной подготовки Odoo.

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

Если в вашей локальной Odoo пароль администратора отличается от `admin`, передайте `ODOO_PASSWORD` через переменные окружения при запуске скрипта.

Если видите ошибку `KeyError: 'ir.http'` в контейнере Odoo, обычно это означает, что база не была инициализирована.
Скрипт `./scripts/test_odoo_integration.sh` теперь выполняет инициализацию БД (`base`) и установку `video_automation` автоматически.


### Что смотреть в логах, если `make dev-all` падает

Собрать ключевые логи одной командой:

```bash
docker compose ps
docker compose logs --tail=200 db odoo
```

Если ошибка вида `relation "ir_module_module" does not exist`, это признак неинициализированной БД Odoo.

Исправление:

```bash
docker compose down -v
make odoo-up
```

Команда `make odoo-up` теперь сначала инициализирует БД через one-shot запуск Odoo (`-i base,video_automation`), и только потом поднимает web-сервис.

## Минимальная архитектура (эволюционно)

- `bot/` — Telegram-интерфейс и сценарий диалога.
- `services/` — обработка медиа, транскрибация, генерация текстов.
- `backend/` — API/healthcheck (точка для будущей интеграции с Odoo).

