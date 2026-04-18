import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SOURCE_DIR: str = "./dataset/share"
    MAX_WORKERS: int = max(1, (os.cpu_count() or 4) - 1)

    CHUNK_SIZE: int = 10000

    NLP_MAX_TEXT_LEN: int = 100000

    VOSK_MODEL_PATH: str = "vosk"

    LARGE_THRESHOLDS: dict[str, int] = {"Ordinary": 50, "Government": 10, "Payment": 5}


settings = Settings()
