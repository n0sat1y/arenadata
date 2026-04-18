import os
from typing import Generator


def crawl_files(target_dir: str) -> Generator[str, None, None]:
    for root, _, files in os.walk(target_dir):
        for file in files:
            yield os.path.join(root, file)
