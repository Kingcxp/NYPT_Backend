import uvicorn

from dotenv import load_dotenv, find_dotenv

from .app import app


if __name__ == "__main__":
    load_dotenv(find_dotenv(), verbose=True)
    uvicorn.run(app, host="0.0.0.0", port=8081, reload=True)
