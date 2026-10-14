import uvicorn

from src.fastapi import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("bin.api:app", host="0.0.0.0", port=8003, reload=True)
