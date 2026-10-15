import uvicorn

from src.fastapi import create_app
from src.settings import Settings

app = create_app()

if __name__ == "__main__":
    uvicorn.run("bin.api:app", host="0.0.0.0", port=Settings().port)
