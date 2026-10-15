import uvicorn

from src.fastapi import create_app
from src.infrastructure.logging_config import configure_logging
from src.settings import Settings

configure_logging()
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "bin.api:app",
        host="0.0.0.0",
        port=Settings().port,
        log_config=None,
    )
