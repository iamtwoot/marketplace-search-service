# Search Service

Read-side CQRS для маркетплейса. Слушает Kafka-топик `ads`, дёргает `GET /internal/ads/{id}` у Ad Service и поддерживает денормализованный индекс в PostgreSQL для полнотекстового поиска и автодополнения.

## Стек

- Python 3.13, FastAPI, SQLAlchemy (async), PostgreSQL
- PostgreSQL full-text search (`to_tsvector('russian', ...)` + GIN-индекс)
- Kafka (Redpanda локально) — aiokafka consumer
- httpx — клиент к Ad Service
- Alembic — миграции
- uv — управление зависимостями

## Быстрый старт

```bash
uv sync

# PostgreSQL (Kafka/Redpanda поднимается из docker-compose.yml Ad Service)
docker compose up -d

# Переменные окружения
cp .env.example .env  # или отредактировать .env

# Миграции
make migrate

# API
make run

# В соседнем терминале — консьюмер, который слушает Kafka
make consumer
```

API стартует на `http://localhost:8003`.

## Переменные окружения

| Переменная                    | По умолчанию                                                       | Описание                          |
|-------------------------------|--------------------------------------------------------------------|-----------------------------------|
| `POSTGRES_CONNECTION_STRING`  | `postgresql+asyncpg://postgres:postgres@localhost:5435/search_db`  | Строка подключения к PostgreSQL   |
| `KAFKA_BROKERS`               | `localhost:9092`                                                   | Kafka-брокеры                     |
| `KAFKA_TOPIC_ADS`             | `ads`                                                              | Топик с событиями объявлений      |
| `KAFKA_CONSUMER_GROUP`        | `search-service`                                                   | consumer group                    |
| `AD_SERVICE_URL`              | `http://localhost:8002`                                            | Базовый URL Ad Service (internal) |

Драйвер в `POSTGRES_CONNECTION_STRING` всегда принудительно заменяется на `postgresql+asyncpg`.

## API

### Публичные эндпоинты (`/search`)

| Метод | Путь              | Описание                              | Auth |
|-------|-------------------|---------------------------------------|------|
| `GET` | `/search`         | Полнотекстовый поиск с фильтрами      | Нет  |
| `GET` | `/search/suggest` | Автодополнение по первым символам     | Нет  |

Параметры `GET /search`: `q`, `category`, `city`, `min_price`, `max_price`, `sort` (`date` / `price_asc` / `price_desc`), `limit` (1–100, по умолчанию 20), `offset`.

Параметры `GET /search/suggest`: `q` (минимум 2 символа), `limit` (1–10, по умолчанию 5).

## Kafka consumer

Топик `ads`, consumer group `search-service`. События тонкие, поэтому Search Service источником истины о контенте объявления не является — по `ad_id` он всегда идёт за актуальной копией в Ad Service.

| Событие      | Действие                                                                                    |
|--------------|---------------------------------------------------------------------------------------------|
| `ad.created` | `GET /internal/ads/{ad_id}` → upsert в `search_index`                                       |
| `ad.updated` | `GET /internal/ads/{ad_id}` → upsert (или удаление, если объявление archived)               |
| `ad.deleted` | Удаление записи из `search_index` по `ad_id`                                                |

Если событие потеряно или пришло не по порядку — вызов `/internal/ads/{id}` всегда отдаёт финальное состояние (включая `archived`), поэтому индекс сойдётся к правильному состоянию на следующем событии.

## Make-команды

| Команда                          | Описание                          |
|----------------------------------|-----------------------------------|
| `make run`                       | Запуск API                        |
| `make consumer`                  | Kafka-консьюмер                   |
| `make check`                     | Линтинг + форматирование (ruff)   |
| `make test`                      | Запуск тестов                     |
| `make lint`                      | `ruff check --fix`                |
| `make format`                    | `ruff format`                     |
| `make migrate`                   | Применить миграции                |
| `make migrate-create name="..."` | Сгенерировать миграцию            |
