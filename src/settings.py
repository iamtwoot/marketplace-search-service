from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    postgres_connection_string: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5435/search_db"
    )
    kafka_brokers: str = "localhost:9092"
    kafka_topic_ads: str = "ads"
    kafka_consumer_group: str = "search-service"
    ad_service_url: str = "http://localhost:8002"
